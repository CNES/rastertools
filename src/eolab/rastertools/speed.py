#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named speed that computes the time derivative (speed)
of the radiometry of the input rasters.
"""
from datetime import datetime
import logging.config
from pathlib import Path
from typing import List

import numpy
import rasterio

from eolab.rastertools import utils
from eolab.rastertools import Rastertool
from eolab.rastertools.processing import algo
from eolab.rastertools.product import RasterProduct


_logger = logging.getLogger(__name__)


class Speed(Rastertool):
    """Raster tool that computes the time derivative (speed) of raster images.

    For images of the same and known type, the tool extract the timestamp metadata
    from the names of the images. It can then compute the time derivatives of every
    bands.
    """

    def __init__(self, bands: List[int] = [1]):
        """ Constructor

        Args:
            bands ([int], optional, default=[1]):
                List of bands in the input image to process.
                Set None if all bands shall be processed.
        """
        super().__init__()

        self._bands = bands

    @property
    def bands(self) -> List[int]:
        """List of bands to process"""
        return self._bands

    def postprocess_files(self, inputfiles: List[str], outputfiles: List[str]) -> List[str]:
        """Compute the temporal derivative of input files' radiometry

        Args:
            inputfiles ([str]): Input images to process
            outputfiles ([str]): List of generated files after executing the
                rastertool on the input files individually

        Returns:
            [str]: List of speed images that have been generated
        """
        if len(inputfiles) < 2:
            raise ValueError("Can not compute speed with 1 input image. Provide at least 2 images.")

        # STEP 1: Prepare the input images so that they can be processed
        product_per_date = {}
        same_type = True
        common_rastertype = None

        for infile in inputfiles:
            product = RasterProduct(infile, vrt_outputdir=self.vrt_dir)
            if common_rastertype is None:
                common_rastertype = product.rastertype
            elif same_type and common_rastertype != product.rastertype:
                raise ValueError("Speed can only be computed with images of the same type")

            product_per_date[product.get_date()] = (infile, product)

        # STEP 2: Compute speed
        outdir = Path(self.outputdir)
        outputs = []
        product0 = None
        date0 = None
        for i, date1 in enumerate(sorted(product_per_date.keys())):
            infile, product1 = product_per_date[date1]
            if i > 0:
                # compute the speed
                date0str = date0.strftime('%Y%m%d-%H%M%S')
                date1str = date1.strftime('%Y%m%d-%H%M%S')
                _logger.info(f"Compute speed between {date0str} and {date1str}")
                speed_image = outdir.joinpath(f"{utils.get_basename(infile)}-speed-{date0str}.tif")
                compute_speed(date0, date1, product0, product1,
                              speed_image.as_posix(), self.bands)
                outputs.append(speed_image.as_posix())

            product0 = product1
            date0 = date1

        # free resources
        for infile, product in product_per_date.values():
            product.free_in_memory_vrts()

        return outputs


def compute_speed(date0: datetime, date1: datetime,
                  product0: RasterProduct, product1: RasterProduct,
                  speed_image: str, bands: List[int] = None):
    """Compute the evolution of the raster band during a time interval

    Args:
        date0 (:obj:`datetime.datetime`):
            Date of the first dataset
        date1 (:obj:`datetime.datetime`):
            Date of the second dataset
        product0 (:obj:`eolab.rastertools.product.RasterProduct`):
            Path of the first raster image
        product1 (:obj:`eolab.rastertools.product.RasterProduct`):
            Path of the second raster image
        speed_image (str):
            Path of the output image
        bands ([int], optional, default=None):
            List of bands to process. None if all bands shall be processed
    """
    with rasterio.Env(GDAL_VRT_ENABLE_PYTHON=True):
        # compute time interval
        interval = (date1 - date0).total_seconds()

        # open input images
        with product0.open_xarray() as src0, product1.open_xarray() as src1:

            if src1.shape[0] != src0.shape[0]:
                raise ValueError(f"Number of bands in images {src1.shape[0]} and {src1.shape[0]}"
                                 " are not the same")
            if src1.shape[1] != src0.shape[1] or src1.shape[2] != src0.shape[2]:
                raise ValueError(f"All images have not the same size")
            if src1.rio.transform() != src0.rio.transform() :
                 raise ValueError(f"Images {product0} and {product1} are not fully"
                                  " geographically overlapping")

            # check band index and handle all bands options (when bands is an empty list)
            if bands is None or len(bands) == 0:
                bands = src1["band"].values
            elif min(bands) < 1 or max(bands) > src1.shape[0]:
                raise ValueError(f"Invalid bands, all values are not in range [1, {src1.shape[0]}]")

            dtype = rasterio.float32
            src0 = src0.isel(band=slice(0, len(bands))).astype(dtype)
            src1 = src1.isel(band=slice(0, len(bands))).astype(dtype)

            result = algo.speed(src0, src1, interval).astype(dtype)

            ##Create the file and compute
            result.rio.write_nodata(-2, inplace=True)
            result.rio.to_raster(speed_image)

