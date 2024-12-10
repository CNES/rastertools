#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named timeseries that generate a timeseries
of rasters at different dates from a list of rasters that may contain gaps (due
to clouds for instance). The timeseries is generated with a linear interpolation
thus enabling to fill gaps.
"""
from datetime import datetime, timedelta
from idlelib.format import reformat_paragraph
from itertools import repeat
import logging.config
import multiprocessing
import os
from pathlib import Path
import xarray as xr
from typing import Dict, List

import numpy as np
import rasterio
from osgeo import gdal
from tqdm.contrib.concurrent import process_map

from eolab.rastertools import utils
from eolab.rastertools import Rastertool, Windowable
from eolab.rastertools.processing import algo
from eolab.rastertools.product import RasterProduct

_logger = logging.getLogger(__name__)


class Timeseries(Rastertool, Windowable):
    """Raster tool that generates the time series of raster images. The timeseries is
    generated with a linear interpolation thus enabling to fill gaps.
    """

    def __init__(self, start_date: datetime, end_date: datetime, period: int,
                 bands: List[int] = [1]):
        """ Constructor

        Args:
            start_date (datetime):
                Start date of the timeseries to generate
            end_date (datetime):
                End date of the timeseries to generate
            period (int):
                Time period (in days) between two consecutive dates in the timeseries
            bands ([int], optional, default=[1]):
                List of bands in the input image to process.
                Set None if all bands shall be processed.
        """
        super().__init__()
        self.with_windows()

        self._bands = bands
        self._start_date = start_date
        self._end_date = end_date
        self._period = period

    @property
    def start_date(self):
        """Start date of the timeseries to generate"""
        return self._start_date

    @property
    def end_date(self):
        """End date of the timeseries to generate"""
        return self._end_date

    @property
    def period(self):
        """Period (in days) of the timeseries to generate"""
        return self._period

    @property
    def bands(self) -> List[int]:
        """List of bands to process"""
        return self._bands

    def postprocess_files(self, inputfiles: List[str], outputfiles: List[str]) -> List[str]:
        """Generates the timeseries from a list of inputfiles.

        Args:
            inputfiles ([str]): Input images to process
            outputfiles ([str]): List of generated files after executing the
                rastertool on the input files individually

        Returns:
            [str]: List of images that have been generated
        """
        if len(inputfiles) < 2:
            raise ValueError("Can not compute a timeseries with 1 input image. "
                             "Provide at least 2 images.")

        # STEP 1: Prepare the input images so that they can be processed
        reftype = None
        products_per_date = dict()
        template_name = ""
        for i, infile in enumerate(inputfiles):
            product = RasterProduct(infile, vrt_outputdir=self.vrt_dir)
            if reftype is None:
                if product.rastertype is None:
                    raise ValueError(f"Unknown rastertype for input file {infile}")
                else:
                    reftype = product.rastertype
            elif product.rastertype != reftype:
                raise ValueError("Timeseries can only be computed with images of the same type")

            d = product.get_date().replace(hour=0, minute=0, second=0, microsecond=0)
            products_per_date[d.timestamp()] = product

            if i == 0:
                template_name = utils.get_basename(infile).replace(
                    product.get_date_string(), "{}")

        # STEP 2: create the list of requested dates
        dates = np.arange(self.start_date,
                          self.end_date,
                          timedelta(days=self.period)).astype(datetime)
        # convert dates to timestamp
        timestamps = np.array([d.timestamp() for d in dates])
        date_format = "%Y-%m-%d"
        _logger.info("Compute timeseries at dates "
                     f"{[date.strftime(date_format) for date in dates]}")

        # STEP 3: Generate timeseries
        # create the list of output files
        outdir = Path(self.outputdir)

        times_img = []
        for date in dates:
            img_name = f"{template_name.format(date.strftime(reftype.date_format))}-timeseries.tif"
            times_img.append(outdir.joinpath(img_name).as_posix())

        # compute the timeseries
        compute_timeseries(products_per_date, timestamps, times_img,
                           self.bands)

        # free resources
        for product in products_per_date.values():
            product.free_in_memory_vrts()

        return times_img


def compute_timeseries(products_per_date: Dict[float, RasterProduct], timeseries_dates: np.ndarray,
                       timeseries_images: List[str],
                       bands: List[int] = None):
    """Generate the timeseries

    Args:
        products_per_date (dict[float, :obj:`eolab.rastertools.product.RasterProduct`]):
            List of input images indexed by their timestamp
        timeseries_dates ([float]:
            List of dates (timestamps) in the requested timeseries
        timeseries_images ([str]):
            Paths of the output images (one per requested date)
        bands ([int], optional, default=None):
            List of bands to process. None if all bands shall be processed
        window_size (tuple(int, int), optional, default=(1024, 1024)):
            Size of windows for splitting the process in small parts
    """
    with rasterio.Env(GDAL_VRT_ENABLE_PYTHON=True):

        # open all input rasters
        products_dates = sorted(products_per_date.keys())

        for i, date in enumerate(products_dates):
            product = products_per_date[date]
            with product.open_xarray() as src:
                # check if srcs have same size and are geographically overlapping
                if i == 0:
                    refcount = src.shape[0]
                    refindexes = src["band"].values
                    refwidth = src.shape[2]
                    refheight = src.shape[1]
                    reftransform = src.rio.transform()
                else:
                    if src.shape[0] != refcount:
                        raise ValueError(f"All images have not the same number of bands")
                    if src.shape[2] != refwidth or src.shape[1] != refheight :
                        raise ValueError(f"All images have not the same size")
                    if src.rio.transform() != reftransform:
                        raise ValueError(f"All images are not fully"
                                         " geographically overlapping")

        # check band index and handle all bands options (when bands is an empty list)
        if bands is None or len(bands) == 0:
            bands = refindexes
        elif min(bands) < 1 or max(bands) > refcount:
            raise ValueError(f"Invalid bands, all values are not in range [1, {refcount}]")

        nodata = src.rio.nodata

        _interpolate_xarray(products_dates, products_per_date,
                            timeseries_dates, timeseries_images, bands, nodata)



def _interpolate_xarray(products_dates, products_per_date,
                 timeseries_dates, timeseries_images, bands, nodata):
    """Internal method that performs the interpolation for a specific window.
    This method can be called safely by several processes thanks to the locks
    that prevent from reading / writing files simultaneously.
    """
    datas = list()
    for date in products_dates:

        src = products_per_date[date].open_xarray()
        dtype = src.dtype or rasterio.float32
        band_data = src.isel(band=slice(0, len(bands)))  # Select the desired bands
        crs = src.rio.crs
        datas.append(band_data)

    output = algo.interpolated_timeseries_xarray(products_dates, datas, timeseries_dates, nodata)

    m = multiprocessing.Manager()
    write_lock = m.Lock()

    # Use of the lock to avoid writing in //
    with write_lock:
        for i, img in enumerate(timeseries_images):
            output[i].rio.write_crs(crs, inplace=True)
            output[i].rio.write_nodata(0, inplace=True)
            output[i].rio.to_raster(img, nodata=0, dtype=dtype)

    # ref_path = 'tests/tests_refs/test_timeseries/SENTINEL2A_20181016-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif'
    # ref = gdal.Open(ref_path)
    # band_ref = ref.GetRasterBand(1)
    #
    # # Read the band as a NumPy array
    # band_ref = band_ref.ReadAsArray()
    #
    # out_path = 'tests/tests_out/SENTINEL2A_20181016-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif'
    # out = gdal.Open(out_path)
    # band_out = ref.GetRasterBand(1)
    #
    # # Read the band as a NumPy array
    # band_out = band_out.ReadAsArray()
    #
    # print(np.sum(band_out == band_ref))
