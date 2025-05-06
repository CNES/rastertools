#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named speed that computes the time derivative (speed)
of the radiometry of the input rasters.
"""
from datetime import datetime
import logging.config
import os
from pathlib import Path
import threading
from typing import List

import rasterio
from tqdm.contrib.concurrent import thread_map

from eolab.georastertools import utils
from eolab.georastertools import Rastertool
from eolab.georastertools.processing import algo
from eolab.georastertools.product import RasterProduct


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
        product0 (:obj:`eolab.georastertools.product.RasterProduct`):
            Path of the first raster image
        product1 (:obj:`eolab.georastertools.product.RasterProduct`):
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
        with product0.open() as src0, product1.open() as src1:
            if src1.count != src0.count:
                raise ValueError(f"Number of bands in images {product0} and {product1}"
                                 " are not the same")
            if src1.width != src0.width or src1.height != src0.height:
                raise ValueError(f"Images {product0} and {product1} have different sizes")
            if src1.transform != src0.transform:
                raise ValueError(f"Images {product0} and {product1} are not fully"
                                 " geographically overlapping")

            profile = src0.profile
            dtype = rasterio.float32
            nodata = src0.nodata

            # set block size
            blockysize = 1024 if src0.width > 1024 else utils.highest_power_of_2(src0.width)
            blockxsize = 1024 if src0.height > 1024 else utils.highest_power_of_2(src0.height)

            # check band index and handle all bands options (when bands is an empty list)
            if bands is None or len(bands) == 0:
                bands = src1.indexes
            elif min(bands) < 1 or max(bands) > src1.count:
                raise ValueError(f"Invalid bands, all values are not in range [1, {src1.count}]")

            profile.update(driver="GTiff",
                           blockxsize=blockysize, blockysize=blockxsize, tiled=True,
                           dtype=dtype, count=len(bands))

            with rasterio.open(speed_image, "w", **profile) as dst:
                # Materialize a list of destination block windows
                windows = [window for ij, window in dst.block_windows()]

                read_lock = threading.Lock()
                write_lock = threading.Lock()

                def process(window):
                    """Read input rasters, compute speed and write output raster"""
                    with read_lock:
                        data0 = src0.read(bands, window=window, masked=True).astype(dtype)
                        data1 = src1.read(bands, window=window, masked=True).astype(dtype)

                    # The computation can be performed concurrently
                    result = algo.speed(data0, data1, interval).astype(dtype).filled(nodata)

                    with write_lock:
                        dst.write(result, window=window)

                disable = os.getenv("RASTERTOOLS_NOTQDM", 'False').lower() in ['true', '1']
                thread_map(process, windows, disable=disable, desc="speed")
