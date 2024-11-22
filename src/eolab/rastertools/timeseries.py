#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named timeseries that generate a timeseries
of rasters at different dates from a list of rasters that may contain gaps (due
to clouds for instance). The timeseries is generated with a linear interpolation
thus enabling to fill gaps.
"""
from datetime import datetime, timedelta
from itertools import repeat
import logging
import logging.config
import multiprocessing
import os
from pathlib import Path
import xarray as xr
from typing import Dict, List

import numpy as np
import rasterio
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

    def postprocess_files(self, inputfiles: List[str], outputfiles: List[str], xarray_vers : bool = False) -> List[str]:
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
        outdir = Path("/home/ecadaux/pluto/rastertools/rastertools/tests/tests_out" + "/test_timeseries_xarray") #Path(self.outputdir) # # # # # #

        times_img_np = []
        times_img_xarray = []
        for date in dates:
            img_name_np = f"{template_name.format(date.strftime(reftype.date_format))}-timeseries.tif"
            times_img_np.append(outdir.joinpath(img_name_np).as_posix())
            if xarray_vers :
                img_name_xarray = f"{template_name.format(date.strftime(reftype.date_format))}-timeseries_xarray.tif"
                times_img_xarray.append(outdir.joinpath(img_name_xarray).as_posix())

        # compute the timeseries
        compute_timeseries(products_per_date, timestamps, times_img_np,
                           self.bands, self.window_size, xarray_vers)

        # free resources
        for product in products_per_date.values():
            product.free_in_memory_vrts()

        if xarray_vers:
            return times_img_np, times_img_xarray
        else :
            return times_img_np


def compute_timeseries(products_per_date: Dict[float, RasterProduct], timeseries_dates: List[float],
                       timeseries_images: List[str],
                       bands: List[int] = None, window_size: tuple = (1024, 1024), xarray_vers : bool = False):
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
            with product.open() as src:
                # check if srcs have same size and are geographically overlapping
                if i == 0:
                    refcount = src.count
                    refindexes = src.indexes
                    refwidth = src.width
                    refheight = src.height
                    reftransform = src.transform
                    refprofile = src.profile
                    descriptions = src.descriptions
                else:
                    if src.count != refcount:
                        raise ValueError(f"All images have not the same number of bands")
                    if src.width != refwidth or src.height != refheight:
                        raise ValueError(f"All images have not the same size")
                    if src.transform != reftransform:
                        raise ValueError(f"All images are not fully"
                                         " geographically overlapping")

        # set block size
        blockxsize, blockysize = window_size
        if refwidth < blockxsize:
            blockxsize = utils.highest_power_of_2(refwidth)
        if refheight < blockysize:
            blockysize = utils.highest_power_of_2(refheight)

        # check band index and handle all bands options (when bands is an empty list)
        if bands is None or len(bands) == 0:
            bands = refindexes
        elif min(bands) < 1 or max(bands) > refcount:
            raise ValueError(f"Invalid bands, all values are not in range [1, {refcount}]")

        # update the profile to use for opening output files
        refprofile.update(driver="GTiff",
                          blockxsize=blockysize, blockysize=blockxsize, tiled=True,
                          count=len(bands))
        dtype = refprofile.get("dtype")
        nodata = refprofile.get("nodata")

        # create empty output files with correct metadata
        for i, img in enumerate(timeseries_images):
            with rasterio.open(img, mode="w", **refprofile) as dst:
                if i == 0:
                    # with rasterio.open(timeseries_images[0], mode="w", **profile) as dst:
                    windows = [window for ij, window in dst.block_windows()]
                for j, band in enumerate(bands, 1):
                    dst.set_band_description(j, descriptions[band - 1])

        m = multiprocessing.Manager()
        write_lock = m.Lock()

        kwargs = {
            "total": len(windows),
            "disable": os.getenv("RASTERTOOLS_NOTQDM", 'False').lower() in ['true', '1']
        }
        max_workers = os.getenv("RASTERTOOLS_MAXWORKERS")
        if max_workers is not None:
            kwargs["max_workers"] = int(max_workers)


        if not(xarray_vers) :
            #Launch with np
            print("np")
            process_map(_interpolate,
                            repeat(products_dates), repeat(products_per_date),
                            repeat(timeseries_dates), repeat(timeseries_images),
                            windows, repeat(bands),
                            repeat(dtype), repeat(nodata),
                            repeat(write_lock),
                            **kwargs)
        else:
            # Launch with xarray
            print("xarray")
            process_map(_interpolate_xarray,
                            repeat(products_dates), repeat(products_per_date),
                            repeat(timeseries_dates), repeat(timeseries_images),
                            windows, repeat(bands),
                            repeat(dtype), repeat(nodata),
                            repeat(write_lock),
                            **kwargs)


def _interpolate(products_dates, products_per_date,
                 timeseries_dates, timeseries_images,
                 window, bands,
                 dtype, nodata,
                 write_lock):
    """Internal method that performs the interpolation for a specific window.
    This method can be called safely by several processes thanks to the locks
    that prevent from reading / writing files simultaneously.
    """
    datas = list()
    for date in products_dates:
        product = products_per_date[date]
        with product.open() as src:
            data = src.read(bands, window=window, masked=True)
            datas.append(data)

    output = algo.interpolated_timeseries(products_dates, datas, timeseries_dates, nodata)

    with write_lock:
        for i, img in enumerate(timeseries_images):
            with rasterio.open(img, mode="r+") as dst:
                dst.write(output[i].astype(dtype), window=window)


def _interpolate_xarray(products_dates, products_per_date,
                 timeseries_dates, timeseries_images,
                 window, bands,
                 dtype, nodata,
                 write_lock):
    """Internal method that performs the interpolation for a specific window.
    This method can be called safely by several processes thanks to the locks
    that prevent from reading / writing files simultaneously.
    """
    datas = list()
    for date in products_dates:
        product = products_per_date[date]

        src = product.open_xarray()
        band_data = src.isel(band=slice(0, len(bands)))  # Select the desired bands

        # Process the desired window
        window_data = band_data.isel(x=slice(window.col_off, window.col_off + window.width),
                                     y=slice(window.row_off, window.row_off + window.height))

        # data = src.read(bands, window=window, masked=True)
        datas.append(window_data)


    output = algo.interpolated_timeseries(products_dates, datas, timeseries_dates, nodata)

    with write_lock:
        for i, img in enumerate(timeseries_images):
            with rasterio.open(img, mode="r+") as dst:
                dst.write(output[i].astype(dtype), window=window)
