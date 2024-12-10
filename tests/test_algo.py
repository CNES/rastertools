#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import numpy.ma as ma
import rasterio
import pytest
import xarray as xr
from rioxarray import rioxarray

from eolab.rastertools import utils
from eolab.rastertools.processing import algo
from eolab.rastertools.product import RasterProduct

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"

from eolab.rastertools.timeseries import compute_timeseries, Timeseries
from .utils4test import RastertoolsTestsData

# zero_np = np.zeros((1,100,100))
# zero_xarr = xr.DataArray(zero_np, dims=("x", "y", "z"))
#
# rd_np = np.random.randn(1,100, 100)
# rd_xarr = xr.DataArray(rd_np, dims=("x", "y", "z"))
#
# rd2_np = np.random.randn(1,100, 100)
# rd2_xarr = xr.DataArray(rd2_np, dims=("x", "y", "z"))
#
# #Both zeros arrays
# zero_nptest = [zero_np, zero_np]
# zero_xarrtest = [zero_xarr, zero_xarr]
#
# #One random array and a zero array
# rd1_nptest = [zero_np, rd_np]
# rd1_xarrtest = [zero_xarr, rd_xarr]
#
# #Two same random array
# rd2_nptest = [rd_np, rd_np]
# rd2_xarrtest = [rd_xarr, rd_xarr]
#
# #Two different random array
# rd3_nptest = [rd_np, rd2_np]
# rd3_xarrtest = [rd_xarr, rd2_xarr]
#
# @pytest.mark.parametrize("input_np, input_xarray, interval",
#                          [(zero_nptest, zero_xarrtest, 0.0),
#                           (zero_nptest, zero_xarrtest, 5.0),
#                           (rd1_nptest, rd1_xarrtest, 5.0),
#                           (rd2_nptest, rd2_xarrtest, -4.0),
#                           (rd3_nptest, rd3_xarrtest, 1.0)])
#
#
# def test_speed_algo(input_np :list, input_xarray : list, interval : float):
#     """
#     Test if the output of the speed algorithm obtained with numpy.ndarray are the same that with xarray.DataArray
#     """
#     data1_np, data2_np = input_np
#     data1_xarr, data2_xarr = input_xarray
#     speed_np = algo.speed(data1_np, data2_np, interval)
#     speed_xarr = algo.speed(data1_xarr, data2_xarr, interval)
#
#     #Assert that the values of both arrays are the same
#     np.testing.assert_array_equal(speed_np, speed_xarr.values)
#     assert type(speed_xarr) == xr.DataArray


# input_file1 = "tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
# input_file2 = "tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
# file_list = [input_file1, input_file2]
#
# @pytest.mark.parametrize("file_list, start_date, end_date, period, window_size",
#                          [(file_list,"2018-09-26", "2018-11-07" , 20, (512,512))])
#
#
# def test_xarray_timeseries_algo(file_list : list, start_date :str, end_date: str, period : int, window_size : tuple):
#     """
#     Test if the output of the timeseries algorithm obtained with numpy.ndarray are the same that with xarray.DataArray
#     Only nan values are different
#     """
#     # outputdir = RastertoolsTestsData.tests_output_data_dir + "/test_timeseries_xarray"
#     bands = [1]
#
#     start_date = datetime.strptime(start_date, "%Y-%m-%d")
#     end_date = datetime.strptime(end_date, "%Y-%m-%d")
#
#     all_outputs = []
#     for filename in file_list:
#         outputs = list(filename)
#         if outputs:
#             all_outputs.extend(outputs)
#
#     # # create the rastertool object
#     # tools = Timeseries(start_date, end_date, period, bands)
#     # out_imgs_np, out_imgs_xarray = tools.postprocess_files(file_list, all_outputs, xarray_vers = True)
#     #
#
#     out_imgs_np = ['/home/ecadaux/pluto/rastertools/rastertools/tests/tests_out/test_timeseries_xarray/SENTINEL2A_20180926-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif', '/home/ecadaux/pluto/rastertools/rastertools/tests/tests_out/test_timeseries_xarray/SENTINEL2A_20181016-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif', '/home/ecadaux/pluto/rastertools/rastertools/tests/tests_out/test_timeseries_xarray/SENTINEL2A_20181105-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif']
#     out_imgs_xarray = [
#         '/home/ecadaux/pluto/rastertools/rastertools/tests/tests_out/test_timeseries_xarray/SENTINEL2A_20180926-000000-685_L2A_T30TYP_D-ndvi-timeseries-xarray.tif',
#         '/home/ecadaux/pluto/rastertools/rastertools/tests/tests_out/test_timeseries_xarray/SENTINEL2A_20181016-000000-685_L2A_T30TYP_D-ndvi-timeseries-xarray.tif',
#         '/home/ecadaux/pluto/rastertools/rastertools/tests/tests_out/test_timeseries_xarray/SENTINEL2A_20181105-000000-685_L2A_T30TYP_D-ndvi-timeseries-xarray.tif']
#
#
#     for product_id in range(len(out_imgs_np)) :
#         with rasterio.open(out_imgs_np[product_id]) as src_np:
#             times_np = src_np.read(bands, masked=True)
#
#         src_xarray = rioxarray.open_rasterio(out_imgs_xarray[product_id])
#         times_xarray = src_xarray.sel(band=bands).values.astype(np.float32)
#
#         if isinstance(times_np, np.ma.MaskedArray):
#             times_np = times_np.filled(np.nan)
#         np.testing.assert_allclose(times_np, times_xarray, equal_nan=True)

#
# zero3d_np = np.zeros((3,3,3))
# zero3d_xarr = xr.DataArray(zero3d_np, dims=("x", "y", "z"))
#
# rd3d_np = np.random.randn(3,3,3)
# rd3d_xarr = xr.DataArray(rd3d_np, dims=("x", "y", "z"))
#
# @pytest.mark.parametrize("input_np, input_xarray", [(zero3d_np,zero3d_xarr),
#                                                      (rd3d_np,rd3d_xarr)])
#
# def test_indices_algo(input_np :np.ndarray, input_xarray : xr.DataArray):
#     """
#     Test if the outputs obtained with numpy.ndarray are the same that with xarray.DataArray
#     """
#     ind_func = [algo.normalized_difference, algo.rvi, algo.tndvi, algo.pvi, algo.savi, algo.tsavi, algo.msavi, algo.msavi2, algo.ipvi,
#                 algo.evi, algo.redness_index, algo.brightness_index, algo.brightness_index2]
#
#     for indic in ind_func :
#         ind_np = indic(input_np)
#         ind_xarr = indic(input_xarray)
#         #Assert that the values of both arrays are the same
#         np.testing.assert_array_equal(ind_np, ind_xarr.values)
#         assert type(ind_xarr) == xr.DataArray

#
# @pytest.mark.parametrize("input_np, input_xarray, params", [(zero_np,zero_xarr, [50, 16, 0.5, None]),
#                                                      (zero_np,zero_xarr, [50, 16, 0.5, 0]),
#                                                      (rd_np,rd_xarr, [50, 16, 0.5, None]),
#                                                      (rd_np,rd_xarr, [50, 16, 0.5, 0])])
#
# def test_svf_algo(input_np : np.ndarray, input_xarray : xr.DataArray, params : list):
#     """
#     Test if the outputs obtained with numpy.ndarray are the same that with xarray.DataArray
#     """
#     radius, directions, resolution, altitude = params
#     svf_np = algo.svf(input_np, radius, directions, resolution, altitude)
#     svf_xarr = algo.svf(input_xarray, radius, directions, resolution, altitude)
#     #Assert that the values of both arrays are the same
#     np.testing.assert_array_equal(svf_np, svf_xarr.values)
#     assert type(svf_xarr) == xr.DataArray


# @pytest.mark.parametrize("input_np, input_xarray, params", [(zero_np,zero_xarr, [27.2, 82.64, 3, 0.5]),
#                                                      (rd_np,rd_xarr, [27.2, 82.64, 3, 0.5])])
#
# def test_hillshade_algo(input_np : np.ndarray, input_xarray : xr.DataArray, params : list):
#     """
#     Test if the outputs obtained with numpy.ndarray are the same that with xarray.DataArray
#     """
#     elevation, azimuth , radius, resolution = params
#     hills_np = algo.hillshade(input_np, elevation, azimuth , radius, resolution)
#     hills_xarr = algo.hillshade(input_xarray, elevation, azimuth , radius, resolution)
#     #Assert that the values of both arrays are the same
#     np.testing.assert_array_equal(hills_np, hills_xarr.values)
#     assert type(hills_xarr) == xr.DataArray


def test_local_sum():
    """
    Test the local sum filter with varying kernel sizes.

    This function verifies that the local sum filter correctly applies to a
    5x5 matrix with kernel sizes ranging from 1 to 5, comparing each output
    to expected results.
    """
    results = [
        np.array(
            [[0, 1, 2, 3, 4],
             [5, 6, 7, 8, 9],
             [10, 11, 12, 13, 14],
             [15, 16, 17, 18, 19],
             [20, 21, 22, 23, 24]]
        ),
        np.array(
            [[12, 16, 20, 24, 26],
             [32, 36, 40, 44, 46],
             [52, 56, 60, 64, 66],
             [72, 76, 80, 84, 86],
             [82, 86, 90, 94, 96]]
        ),
        np.array(
            [[18, 24, 33, 42, 48],
             [48, 54, 63, 72, 78],
             [93, 99, 108, 117, 123],
             [138, 144, 153, 162, 168],
             [168, 174, 183, 192, 198]]
        ),
        np.array(
            [[72, 84, 100, 112, 120],
             [132, 144, 160, 172, 180],
             [212, 224, 240, 252, 260],
             [272, 284, 300, 312, 320],
             [312, 324, 340, 352, 360]]
        )
    ]

    for i in range(1, 5):
        kernel_width = i

        # we need to extend the input data
        radius = (kernel_width + 1) // 2

        band = np.arange(25).reshape(5, 5)
        # reshape and pad band, input shape is increased by kernel_width or
        # kernel_width + 1 if kernel_width is odd
        array = np.full((3, 5 + 2 * radius, 5 + 2 * radius),
                        np.pad(band, (radius, radius), mode="edge"))

        # output shape is array shape - kernel_width
        output = algo.local_sum(array, kernel_size=kernel_width)

        # if kernel_width is odd, output is too large
        output = output[:, radius:-radius, radius:-radius]

        assert (output[0] == results[i - 1]).all()

# @pytest.mark.parametrize("input_np, input_xarray, kernel_width", [(zero_np,zero_xarr, 5)])
#
# def test_xarray_local_mean(input_np : np.ndarray, input_xarray : xr.DataArray, kernel_width : int):
#     """
#     Test if the output of the speed algorithm obtained with numpy.ndarray are the same that with xarray.DataArray
#     """
#     mean_np = algo.local_mean(ma.array(input_np), kernel_width)
#     mean_xarr = algo.local_mean(input_xarray, kernel_width)
#
#     #Assert that the values of both arrays are the same
#     np.testing.assert_array_equal(mean_np, mean_xarr.values)
#     assert type(mean_xarr) == xr.DataArray


def test_local_mean():
    """
    Test the local mean filter with a kernel size of 2.
    This test verifies the local mean filter by comparing its output on a 5x5 matrix to an expected result matrix.
    """
    result = np.array(
        [[1, 1.5, 2.5, 3.5, 4],
         [3, 3.5, 4.5, 5.5, 6],
         [7, 7.5, 8.5, 9.5, 10],
         [11, 11.5, 12.5, 13.5, 14],
         [13, 13.5, 14.5, 15.5, 16]])

    kernel_width = 2

    # we need to extend the input data
    radius = (kernel_width + 1) // 2

    band = [
        [-2., -2., -2., -2., -2.],
        [-2., 1, 2, 3, 4],
        [-2., 5, 6, 7, 8],
        [-2., 9, 10, 11, 12],
        [-2., 13, 14, 15, 16]]
    band = np.pad(band, (radius, radius), mode="edge")
    mask = np.array(
        [[True, True, True, True, True],
         [True, False, False, False, False],
         [True, False, False, False, False],
         [True, False, False, False, False],
         [True, False, False, False, False]]
    )
    mask = np.pad(mask, (radius, radius), mode="edge")

    array = ma.array(band, mask=mask) # masks the band array
    # ie. removes the first line and first column of band

    # output shape is array shape - kernel_width
    output = algo.local_mean(array, kernel_size=kernel_width)

    # if kernel_width is odd, output is too large
    output = output[radius:-radius, radius:-radius]

    assert (output == result).all()


def test_bresenham_line():
    """
    Test the Bresenham's line algorithm for angles from 0° to 360° in 15° increments.

    This function verifies that the Bresenham line algorithm generates accurate
    line coordinates for a given radius across multiple theta values. Each angle
    is tested against an expected list of coordinates.
    """
    results = [
        # 0°
        [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
        # 15°
        [(1, 0), (2, 1), (3, 1), (4, 1), (5, 1)],
        # 30°
        [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3)],
        # 45°
        [(1, 1), (2, 2), (3, 3), (4, 4)],
        # 60°
        [(1, 1), (1, 2), (2, 3), (2, 4), (3, 5)],
        # 75°
        [(0, 1), (1, 2), (1, 3), (1, 4), (1, 5)],
        # 90°
        [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5)],
        # 105°
        [(0, 1), (-1, 2), (-1, 3), (-1, 4), (-1, 5)],
        # 120°
        [(-1, 1), (-1, 2), (-2, 3), (-2, 4), (-3, 5)],
        # 135°
        [(-1, 1), (-2, 2), (-3, 3), (-4, 4)],
        # 150°
        [(-1, 1), (-2, 1), (-3, 2), (-4, 2), (-5, 3)],
        # 165°
        [(-1, 0), (-2, 1), (-3, 1), (-4, 1), (-5, 1)],
        # 180°
        [(-1, 0), (-2, 0), (-3, 0), (-4, 0), (-5, 0)],
        # 195°
        [(-1, 0), (-2, -1), (-3, -1), (-4, -1), (-5, -1)],
        # 210°
        [(-1, -1), (-2, -1), (-3, -2), (-4, -2), (-5, -3)],
        # 225°
        [(-1, -1), (-2, -2), (-3, -3), (-4, -4)],
        # 240°
        [(-1, -1), (-1, -2), (-2, -3), (-2, -4), (-3, -5)],
        # 255°
        [(0, -1), (-1, -2), (-1, -3), (-1, -4), (-1, -5)],
        # 270°
        [(0, -1), (0, -2), (0, -3), (0, -4), (0, -5)],
        # 285°
        [(0, -1), (1, -2), (1, -3), (1, -4), (1, -5)],
        # 300°
        [(1, -1), (1, -2), (2, -3), (2, -4), (3, -5)],
        # 315°
        [(1, -1), (2, -2), (3, -3), (4, -4)],
        # 330°
        [(1, -1), (2, -1), (3, -2), (4, -2), (5, -3)],
        # 345°
        [(1, 0), (2, -1), (3, -1), (4, -1), (5, -1)]
    ]
    i = 0

    for theta in range(0, 360, 15):
        assert results[i] == [(x, y) for x, y, r in algo._bresenham_line(theta, 5)]
        i += 1
