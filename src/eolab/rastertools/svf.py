#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named SVF (Sky View Factor) which computes the SVF
of a Digital Height Model.
"""
import logging
import logging.config
from pathlib import Path
import numpy as np
import rasterio
import rioxarray
import xarray as xr

from eolab.rastertools import utils
from eolab.rastertools import Rastertool, Windowable
from eolab.rastertools.processing import algo
from eolab.rastertools.processing import RasterProcessing, compute_sliding
from eolab.rastertools.processing.sliding import _pad_dataset_xarray
from eolab.rastertools.product import RasterProduct

_logger = logging.getLogger(__name__)


class SVF(Rastertool, Windowable):
    """Raster tool that computes the Sky View Factor (SVF) of a
    Digital Elevation / Surface / Height Model.

    Kokalj, Žiga & all 2013:

    SVF is a geophysical parameter that measures the portion of the sky visible from a certain
    point. The portion of the sky visible above the surface is especially relevant in energy balance
    studies and computation of diffuse solar insolation.

    Sky-view factor is defined as the proportion of visible sky (:math:`\\Omega`) above a certain
    observation point as seen from a two-dimensional representation.

    The light that falls from the sky onto a certain part of the surface is reduced by the obstacles
    that form the horizon. These obstacles can be described in all directions by the vertical
    elevation angle above the horizontal plane.

    A good SVF approximation can therefore be performed with the estimate of this angle
    in several directions. After the vertical elevation angle is determined in the chosen
    number of directions n, the SVF is determined as a sum of all portions of the sky within
    each direction: :math:`\\sum \\frac {\\cos \\gamma_i}{n}`, where :math:`\\gamma_i` is the
    vertical angle of the horizon in the`direction i.

    The angle :math:`\\gamma` is extracted from the Digital Model:
    :math:`\\tan \\frac{Height}{Distance}`::

                          _____
                        x|     |  ^
                    x    |     |  | Height (from Digital Model)
               x   __    |     |  |
      ____p_______|  |___|     |__v____________
          <-------------->
              Distance

    Where p is the current pixel where the SVF is computed.

    In a direction, the algorithm computes all angles and keeps the largest one. To avoid testing
    too many points, the "radius" parameter defines the max distance of the pixel to test.

    The output image of SVF rastertool is a raster image with the SVF value computed at every pixels
    of the input Digital Height Model.
    """

    def __init__(self, nb_directions: int, radius: int, resolution: float):
        """ Constructor

        Args:
            nb_directions (int):
                Number of directions to compute the SVF
            radius (int):
                Max distance from current point (in pixels) to consider
                for evaluating the max elevation angle
            resolution (float):
                Resolution of the input Digital Height Model (in meter)
        """
        super().__init__()
        self.with_windows()

        self._radius = radius
        self._nb_directions = nb_directions
        self._resolution = resolution
        self._altitude = None

    @property
    def radius(self):
        """Max distance from current point (in pixels) to consider
        for evaluating the max elevation angle"""
        return self._radius

    @property
    def nb_directions(self):
        """Number of directions to compute the SVF"""
        return self._nb_directions

    @property
    def resolution(self):
        """Resolution of the input Digital Height Model (in meter)"""
        return self._resolution

    @property
    def altitude(self):
        """The altitude at which SVF is computed. If None, the SVF is computed
        at the altitude of the point."""
        return self._altitude

    def with_altitude(self, altitude: float):
        """Configure the altitude at which the Sky View Factor shall be computed.
        If not set, the SVF is computed for each pixel at the pixel altitude.

        Args:
            altitude (float):
                Altitude at which SVF shall be computed

        Returns:
            The current instance so that it is possible to chain the with... calls (fluent API)
        """
        self._altitude = altitude

    def process_file(self, inputfile: str):
        """Compute SVF for the input file

        Args:
            inputfile (str):
                Input image to process

        Returns:
            [str]: A list containing a single element: the generated Sky View Factor image.
        """
        _logger.info(f"Processing file {inputfile}")
        outdir = Path(self.outputdir)
        output_image = outdir.joinpath(f"{utils.get_basename(inputfile)}-svf.tif")

        if self.radius >= min(self.window_size) / 2:
            raise ValueError(f"The radius (option --radius, value={self.radius}) must be strictly "
                             "less than half the size of the window (option --window_size, "
                             f"value={min(self.window_size)})")

        # Configure the processing
        svf = RasterProcessing("svf", algo=algo.svf, dtype=np.float32, per_band_algo=True)
        svf.with_arguments({
            "radius": None,
            "directions": None,
            "resolution": None,
            "altitude": None,
            "pad_mode": None
        })
        # set the configuration of the raster processing
        svf.configure({
            "radius": self.radius,
            "directions": self.nb_directions,
            "resolution": self.resolution,
            "altitude": self.altitude,
            "pad_mode": self.pad_mode
        })

        # STEP 1: Prepare the input image so that it can be processed
        with RasterProduct(inputfile, vrt_outputdir=self.vrt_dir) as product:

            # STEP 2: apply svf
            outdir = Path(self.outputdir)
            output_image = outdir.joinpath(
                f"{utils.get_basename(inputfile)}-svf.tif")


            with rasterio.Env(GDAL_VRT_ENABLE_PYTHON=True):
                with product.open_xarray(chunks=True) as src:
                    # dtype and creation options of output data
                    dtype = svf.dtype or rasterio.float32
                    src = src.astype(dtype)

                    #SVF computing
                    output = svf.compute(src).astype(dtype)

                    ##Create the file and compute
                    output.rio.to_raster(output_image)

        return [output_image.as_posix()]
