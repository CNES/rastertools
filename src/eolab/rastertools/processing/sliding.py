#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a method to run a RasterProcessing on sliding windows.
"""
from itertools import repeat
import logging.config
import os
from typing import List
import multiprocessing

import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.windows import Window
from tqdm.contrib.concurrent import process_map

from eolab.rastertools import utils
from eolab.rastertools.processing import RasterProcessing
from eolab.rastertools.utils import vsimem_to_rasterio

_logger = logging.getLogger(__name__)


def compute_sliding(input_image: str, output_image: str, rasterprocessing: RasterProcessing,
                    window_size: tuple = (1024, 1024), window_overlap: int = 0,
                    pad_mode: str = "edge", bands: List[int] = None):
    """
    Apply a sliding window raster processing operation on an input image and save the result.

    This function processes a raster image in small sliding windows, allowing efficient
    memory management for large datasets by processing chunks. The specified `rasterprocessing`
    operation is applied to each window, with options for padding and overlapping windows.

    Args:
        input_image (str): Path to the input raster image file to be processed.
        output_image (str): Path to save the output raster image after processing.
        rasterprocessing (RasterProcessing): A processing object defining the algorithm and
            parameters to apply on each window of the input image.
        window_size (tuple(int, int), optional): Size of each window for processing,
            default is (1024, 1024).
        window_overlap (int, optional): Number of pixels to overlap between consecutive windows,
            default is 0.
        pad_mode (str, optional, default="edge"): Padding mode for the edges of the windows, default is "edge".
            Refer to `numpy.pad <https://numpy.org/doc/stable/reference/generated/numpy.pad.html`_ documentation for valid modes.
        bands (List[int], optional): List of specific bands to process. If None, all bands in
            the input image will be processed.

    Raises:
        ValueError: If specified band indices are out of range for the input image.

    Note:
        This function supports concurrent processing and makes use of a thread pool for efficient
        handling of multiple windows. Window padding at the image boundaries is applied as
        specified, and sliding window indices are computed internally.
    """
    with rasterio.Env(GDAL_VRT_ENABLE_PYTHON=True):

        src = vsimem_to_rasterio(input_image)
        profile = src.profile

        # set block size
        blockxsize, blockysize = window_size
        if src.width < blockxsize:
            blockxsize = utils.highest_power_of_2(src.width)
        if src.height < blockysize:
            blockysize = utils.highest_power_of_2(src.height)

        # dtype and creation options of output data
        dtype = rasterprocessing.dtype or rasterio.float32
        in_dtype = rasterprocessing.in_dtype or dtype
        nbits = rasterprocessing.nbits
        compress = rasterprocessing.compress or src.compression or 'lzw'
        nodata = rasterprocessing.nodata or src.nodata

        # check band index and handle all bands options (when bands is an empty list)
        if bands is None or len(bands) == 0:
            bands = src.indexes
        elif min(bands) < 1 or max(bands) > src.count:
            raise ValueError(f"Invalid bands, all values are not in range [1, {src.count}]")

        # setup profile for output image
        profile.update(driver='GTiff', blockxsize=blockxsize, blockysize=blockysize,
                       tiled=True, dtype=dtype, nbits=nbits, compress=compress,
                       nodata=nodata, count=len(bands))

        with rasterio.open(output_image, "w", **profile):
            # file is created
            pass

        # create the generator of sliding windows
        sliding_gen = _sliding_windows((src.width, src.height),
                                       window_size, window_overlap)

        if rasterprocessing.per_band_algo:
            sliding_windows_bands = [(w, [b]) for w in sliding_gen for b in bands]
        else:
            sliding_windows_bands = [(w, bands) for w in sliding_gen]
        src.close()

    m = multiprocessing.Manager()
    write_lock = m.Lock()

    # compute using concurrent.futures.ThreadPoolExecutor and tqdm
    kwargs = {
        "total": len(sliding_windows_bands),
        "disable": os.getenv("RASTERTOOLS_NOTQDM", 'False').lower() in ['true', '1']
    }
    max_workers = os.getenv("RASTERTOOLS_MAXWORKERS")
    if max_workers is not None:
        kwargs["max_workers"] = int(max_workers)

    process_map(_process_sliding, repeat(rasterprocessing),
                repeat(input_image), repeat(output_image),
                sliding_windows_bands, repeat(window_overlap),
                repeat(pad_mode), repeat(in_dtype),
                repeat(write_lock),
                **kwargs)


def _process_sliding(rasterprocessing: RasterProcessing,
                     input_image, output_image,
                     sliding_windowbands, window_overlap,
                     pad_mode, dtype, write_lock):
    """Internal method that computes the raster data for a specific window.
    This method can be called safely by several processes thanks to the locks
    that prevent from writing files simultaneously.
    """
    sliding_window, bands = sliding_windowbands
    r_window, pad, w_window = sliding_window

    with rasterio.Env(GDAL_VRT_ENABLE_PYTHON=True):
        with rasterio.open(input_image) as src:
            dataset = _read_dataset(src, bands, r_window, pad, pad_mode)
            dataset = dataset.astype(dtype)

    # The computation can be performed concurrently
    output = rasterprocessing.compute(dataset)

    # Use of the lock to avoid writing in //
    with write_lock:
        with rasterio.open(output_image, mode="r+") as dst:
            if rasterprocessing.per_band_algo:
                # here bands only contain a single item which is the band number
                dst.write_band(
                    bands[0],
                    output[0, window_overlap:-window_overlap,
                           window_overlap:-window_overlap],
                    window=w_window)
            else:
                dst.write(
                    output[:,
                           window_overlap:-window_overlap,
                           window_overlap:-window_overlap],
                    window=w_window)


def _read_dataset(src, bands: List[int], window: Window, pad: tuple, pad_mode: str):
    """Read a src dataset

    Args:
        src:
            Source dataset as given by rasterio.open(...)
        bands ([int]):
            Bands to read or None if all bands shall be read
        window (:obj:`rasterio.windows.Window`):
            Window of data to read
        pad (tuple of tuple of int):
            Pad to apply to the read data: (padx, pady). padx
            and pady are also a tuple. The first (resp. second) value is the
            pad to apply at the beginning (resp. end) of the window.
        pad_mode:
            Method to pad data
            (See https://numpy.org/doc/stable/reference/generated/numpy.pad.html)

    Returns:
        The numpy masked array
    """
    # get all bands values as a np.ndarray of 2 or 3 dimensions depending
    # on band argument (if None, all bands are read simultaneously and the
    # dataset contains all bands and is thus a 3-dims array)
    if bands is not None:
        dataset = src.read(bands, window=window, masked=True)
    else:
        dataset = src.read(window=window, masked=True)

    # pad the dataset if necessary
    pad_width = [(0, 0)]
    padx, pady = pad
    if padx != (0, 0) or pady != (0, 0):
        pad_width.extend([pady, padx])
        pad_dataset = np.pad(dataset, pad_width=pad_width, mode=pad_mode)

        # reapply a padded mask if a mask exists
        if ma.is_masked(dataset):
            mask = np.pad(dataset.mask, pad_width=pad_width, mode=pad_mode)
            dataset = ma.masked_array(pad_dataset, mask=mask)
        else:
            dataset = ma.masked_array(pad_dataset)

    return dataset


def _sliding_windows(image_size, window_size, overlap):
    """Create a generator of windows of a given size with an overlap.

    (*) = Image boundaries
    (-) = Windows boundaries

    1st window starts at position (-overlap, -overlap) in the
    coordinates reference of the image.
    Last window ends at position (width + overlap, height + overlap)
    in the coordinates reference of the image

    ```
    (-o,-o)
       |-----------|      ...      ---------|
       | (0,0)     |                        |
       |   ********|**********************  |
       |   *       |                     *  |
       |-----------|               ---------|
           *                             *
           *                             *
           *                             *
       |   *       |                     *  |
       |   *       |                     *  |
       |   ********|**********************  |
       |           |                   (w,h)|
       |-----------|     ...       ---------|
                                           (w+o,h+o)
    ```

    Args:
        image_size (tuple or int):
            Total size of the image that is windowed
        window_size (tuple or int):
            Window size
        overlap (tuple or int):
            Number of pixels that overlap previous (or next) window

    Returns:
        A generator of tuples. Each tuple contains: the window to read,
        the pad to apply when the window is on the edge of the image, the
        corresponding window of "useful data" (the window without the
        overlapping pixels). Pad is given as a tuple (padx, pady). padx
        and pady are also a tuple. The first (resp. second) value is the
        pad to apply at the beginning (resp. end) of the window.
    """
    w_width, w_height = utils.to_tuple(window_size)
    width, height = utils.to_tuple(image_size)
    c_overlap, r_overlap = utils.to_tuple(overlap)

    # compute 2d slices from input parameters
    slices = utils.slices_2d(window_size,
                             # shift is reduced by 2 * overlap
                             (w_width - 2 * c_overlap, w_height - 2 * r_overlap),
                             # stop is increased by overlap
                             (width + c_overlap, height + r_overlap),
                             # start is decreased by overlap
                             (-c_overlap, -r_overlap))

    # iterate the slices and compute windows and padding
    for row_start, row_stop, col_start, col_stop in slices:
        # compute padding when the window is partially outside the image
        padx = (max(0, -col_start), max(0, col_stop - width))
        pady = (max(0, -row_start), max(0, row_stop - height))

        # read window should not be outside the actual dataset window
        r_window = Window.from_slices((max(0, row_start), min(height, row_stop)),
                                      (max(0, col_start), min(width, col_stop)))
        # write window corresponds to the window without overlap
        w_window = Window.from_slices((row_start + r_overlap, row_stop - r_overlap),
                                      (col_start + c_overlap, col_stop - c_overlap))

        yield(r_window, (padx, pady), w_window)
