#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named Tiling that generates tiles a raster images based on
a reference grid.
"""
import logging
from typing import List
from pathlib import Path

import numpy as np
import rasterio
import rasterio.mask
import geopandas as gpd
import rioxarray
from rasterio.rio.options import all_touched_opt
from rioxarray.exceptions import NoDataInBounds

from eolab.rastertools import utils
from eolab.rastertools import Rastertool, RastertoolConfigurationException
from eolab.rastertools.processing import vector
from eolab.rastertools.product import RasterProduct


_logger = logging.getLogger(__name__)


class Tiling(Rastertool):
    """Raster tool that tiles a raster following the geometries of a grid.

    The tool takes as input two files: a raster image and a grid file (shapefile, geojson ...).
    The grid file defines the geometries of the tiles.

    Different options can be configured:

    - output dir: select the dir where tiles will be stored to disk
    - output basename: naming rule of tiles. By default, the basename is the name of
      the original file followed by "_tile" followed by the tile index. In the
      formatted string, tile index is at position 1 and original filename is at
      position 0. For instance, a naming rule such as "tile{1}.tif" will generate
      the tile name "tile75.tif" for the tile id = 75.
    - output subdir: naming rule for subdirs when every tile must be generated in a
      different subdir.

    It is also possible to select the tiles to generate. The seleted tiles are the ones
    which match the expected values of a given grid's property.
    """

    def __init__(self, geometry_file: str):
        """ Constructor

        Args:
            geometry_file (str):
                File name of the geometry file used to tile raster images
        """
        super().__init__()

        self._grid = gpd.read_file(geometry_file)
        self._output_basename = None
        self._output_subdir = False

    @property
    def grid(self):
        """Get the grid that defines the geometries for tiling raster images"""
        return self._grid

    @property
    def output_basename(self) -> str:
        """Base name for naming output"""
        return self._output_basename

    @property
    def output_subdir(self):
        """Naming convention of the subdir where to store outputs. None if
        no tiles shall not be generated in subdirs (but directly in the output dir)"""
        return self._output_subdir

    def with_output(self, outputdir: str = ".", output_basename: str = "{}_tile{}",
                    output_subdir: str = None):
        """Set up the output.

        Args:
            outputdir (str, optional, default="."):
                Output dir where to store results.
            output_basename (str, optional, default="{}_tile{}"):
                Basename for the output file as a formatted string. By default, the
                basename is the name of the original file followed by "_tile" followed
                by the tile index. In the formatted string, tile index is at position 1
                and original filename is at position 0. For instance, tile{1}.tif will
                generate the following name tile75.tif for the tile id = 75
            output_subdir (str, optional, default=None):
                When each tile must be generated in a different subdir, output_subdir
                defines the naming convention for the subdir. It is a formatted string
                with one positional parameter corresponding to the tile index.
                For instance, tile{} will generate the following subdir name: tile75/
                for the tile id = 75. If None, output files will be generated directly
                in the outputdir.

        Returns:
            :obj:`eolab.rastertools.Tiling`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        # Test if output repository is valid
        super().with_output(outputdir)
        self._output_basename = output_basename
        self._output_subdir = output_subdir
        return self

    def with_id_column(self, id_column: str, ids: List[int]):
        """Set up a filter on the geometries for which tiles shall be generated.

        Args:
            id_column (str):
                Name of the column in the vector file that contains the ids to filter.
            ids:
                List of ids values for which tiles shall be generated.

        Returns:
            :obj:`eolab.rastertools.Tiling`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """

        # Test if id_column is defined when ids are set
        if id_column is not None:
            if id_column not in self._grid.columns:
                raise RastertoolConfigurationException(
                    f"Invalid id column named \"{id_column}\": it does not exist in the grid")
            self._grid = self._grid.set_index(id_column)

        if ids is not None:
            if id_column is None:
                raise RastertoolConfigurationException(
                    "Ids cannot be specified when id_col is not defined")

            self._grid = self._grid[self._grid.index.isin(ids)]
            if self._grid.empty:
                # if no id common between grid and given ids
                raise RastertoolConfigurationException(
                    f"No value in the grid column \"{id_column}\" are matching "
                    f"the given list of ids {str(ids)}")
            else:
                invalid_ids = [i for i in ids if i not in self._grid.index]
                if len(invalid_ids) > 0:
                    # log given ids which are not in the grid
                    _logger.error(f"The grid column \"{id_column}\" does not contain "
                                  f"the following values: {str(invalid_ids)}")
        return self

    def process_file(self, inputfile: str):
        """Tile the input file following the geometry file

        Args:
            inputfile (str):
                Input image to process

        Returns:
            [str]: The list of generates tiles.
        """
        _logger.info(f"Processing file {inputfile}")
        inputfile = '/home/ecadaux/pluto/rastertools/rastertools/tests/tests_data/tif_file.tif'
        # STEP 1: Prepare the input image so that it can be processed
        with RasterProduct(inputfile, vrt_outputdir=self.vrt_dir) as product:

            # Load raster as xarray.DataArray
            raster = product.open_xarray()
            crs = raster.rio.crs

            with rasterio.open(product.get_raster()) as src:
                out_meta = src.meta

            output_paths = []

            # STEP 2: Prepare grid (reproject it to raster's CRS)
            grid = vector.reproject(self.grid, product.get_raster())

            for shape, i in zip(grid.geometry, grid.index):
                _logger.info("Crop and export tile " + str(i) + "...")

                try:
                    print(raster.rio.crs)
                    print(shape)
                    # Generate mask to crop the raster to the geometry
                    masked_raster = raster.rio.clip([shape], crs, from_disk=True, all_touched=True, drop=False)

                    # Get the original raster's transform and resolution
                    original_transform = raster.rio.transform()
                    # Update the clipped raster with the original resolution
                    masked_raster = masked_raster.rio.write_transform(original_transform)

                    # output location
                    output = Path(self.outputdir)

                    if self.output_subdir is not None:  # if we need to export in a subdirectory
                        output = output.joinpath(self.output_subdir.format(i))
                        if not output.is_dir():
                            output.mkdir()

                    basename = utils.get_basename(inputfile)
                    output = output.joinpath(self.output_basename.format(basename, i) + ".tif")


                    # Save the cropped raster
                    masked_raster.rio.write_crs(crs, inplace=True)
                    masked_raster.rio.to_raster(output, meta=out_meta, recalc_transform = False)
                    output_paths.append(output.as_posix())

                    _logger.info("Tile " + str(i) + " exported to " + str(output_paths))
                    print(output)
                except NoDataInBounds:  # if no overlap
                    _logger.error("Input shape " + str(i) + " does not overlap raster")

            return output_paths
