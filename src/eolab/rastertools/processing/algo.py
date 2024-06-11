#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Algorithms on raster data
"""
import math

import numpy as np
import numpy.ma as ma
from scipy import ndimage, signal


def normalized_difference(bands, **kwargs):
    """Algorithm that performs a normalized band ratio
    -1 <= nd <= 1

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    return (bands[1] - bands[0]) / (bands[1] + bands[0])


def tndvi(bands, **kwargs):
    """Transformed Normalized Difference Vegetation Index
    TNDVI > 0

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(invalid='ignore')
    ratio = normalized_difference(bands) + 0.5
    ratio[ratio < 0] = 0
    return np.sqrt(ratio)


def rvi(bands, **kwargs):
    """Ratio Vegetation Index
    RVI > 0

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    return bands[1] / bands[0]


def pvi(bands, **kwargs):
    """Perpendicular Vegetation Index
    -1 < PVI < 1

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    return (bands[1] - 0.90893 * bands[0] - 7.46216) * 0.74


def savi(bands, **kwargs):
    """Soil Adjusted Vegetation Index
    -1 < SAVI < 1

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    return (1. + 0.5) * (bands[1] - bands[0]) / (bands[1] + bands[0] + 0.5)


def tsavi(bands, **kwargs):
    """Transformed Soil Adjusted Vegetation Index
    -1 < TSAVI < 1

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    denominator = 0.7 * bands[1] + bands[0] + 0.08 * (1 + 0.7 * 0.7)
    numerator = 0.7 * (bands[1] - 0.7 * bands[0] - 0.9)
    return numerator / denominator


def _wdvi(bands, **kwargs):
    """Weighted Difference Vegetation Index
    Infinite range

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    return bands[1] - 0.4 * bands[0]


def msavi(bands, **kwargs):
    """Modified Soil Adjusted Vegetation Index
    -1 < MSAVI < 1

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    ndvi = normalized_difference(bands)
    wdvi = _wdvi(bands)
    dl = 1 - 2 * 0.4 * ndvi * wdvi
    denominator = bands[1] + bands[0] + dl
    return (1 + dl) * (bands[1] - bands[0]) / denominator


def msavi2(bands, **kwargs):
    """Modified Soil Adjusted Vegetation Index
    -1 < MSAVI2 < 1

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore', invalid='ignore')
    dsqrt = (2. * bands[1] + 1) ** 2 - 8 * (bands[1] - bands[0])
    return (2. * bands[1] + 1) - np.sqrt(dsqrt)


def ipvi(bands, **kwargs):
    """Infrared Percentage Vegetation Index
    0 < IPVI < 1

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    return bands[1] / (bands[1] + bands[0])


def evi(bands, **kwargs):
    """Enhanced vegetation index

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    return 2.5 * (bands[1] - bands[0]) / ((bands[1] + 6.0 * bands[0] - 7.5 * bands[2]) + 1.0)


def redness_index(bands, **kwargs):
    """Redness Index

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(divide='ignore')
    return bands[0] ** 2 / bands[1] ** 3


def brightness_index(bands, **kwargs):
    """Brightness Index

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(invalid='ignore')
    bi = (bands[0] ** 2 + bands[1] ** 2) / 2
    return np.sqrt(bi)


def brightness_index2(bands, **kwargs):
    """Brilliance Index

    Args:
        bands: list of bands as a numpy ndarray

    Returns:
        The numpy array with the results
    """
    np.seterr(invalid='ignore')
    bi2 = (bands[0] ** 2 + bands[1] ** 2 + bands[2] ** 2) / 3
    return np.sqrt(bi2)


def speed(data0, data1, interval, **kwargs):
    """Compute speed for input data

    Args:
        data0 (np.ndarray): band value at first date
        data1 (np.ndarray): band value at second date
        interval (float): time interval between first and second dates

    Returns:
        The numpy array with the results
    """
    return (data1 - data0) / interval


def interpolated_timeseries(dates, series, output_dates, nodata):
    """Interpolate a timeseries of data. Dates and series must
    be sorted in ascending order.

    Args:
        dates (mumpy.masked_array):
            List of dates (timestamps) of the given series of images
        series ([numpy.masked_array]):
            List of 3-dims numpy masked_array containing the raster bands
            at every dates
        output_dates ([numpy.array]):
            The dates (timestamps) of the rasters to generate
        nodata:
            No data value to use

    Returns:
        numpy.ndarray: the numpy array of the rasters, its shape is
        (time, bands, height, width)
    """
    # stacked input data: shape is time x band x height x width
    stack = ma.stack(series)
    stack_shape = stack.shape
    # flatten the stacked data: shape is pixel x time
    pixel_series = stack.transpose((1, 2, 3, 0)).reshape(
        stack_shape[1] * stack_shape[2] * stack_shape[3], -1)

    output = []
    for serie in pixel_series:
        compressed = serie.compressed()
        if serie.count() > 1:
            output.append(np.interp(
                output_dates,
                ma.masked_array(dates, serie.mask).compressed(),
                compressed,
                compressed[0],
                compressed[-1]))
        else:
            default_val = serie.sum() if serie.count() > 0 else nodata
            output.append([default_val] * len(output_dates))

    output = np.array(output)
    return output.transpose(1, 0).reshape(
        -1, stack_shape[1], stack_shape[2], stack_shape[3])


def _local_sum(data: np.ndarray, kernel_width: int):
    """Compute the local sum of an image of shape width x height.
    on a kernel of size: size x size. Output image has a shape of
    (width - size) x (height - size)

    Args:
        data (np.ndarray):
            2 or 3 dimension ndarray or maskedarray. If array has 3 dimensions, the
            local_sum is computed for the last 2 dims (we consider
            first dim as band list)
        kernel_width (int):
            Kernel size to compute the local sum

    Returns:
        np.ndarray:
            Output data with same shape as input data. Computed data
            have a size minored by the kernel_size and are centered
            in the output shape
    """
    if kernel_width == 1:
        output = data.copy()
    else:
        # special case: size = 1 ==> returns data
        if np.issubdtype(data.dtype, np.floating):
            ii_dtype = np.float64
        elif np.issubdtype(data.dtype, np.int32):
            ii_dtype = np.int64
        else:
            ii_dtype = data.dtype

        # create the integral image
        line_cumsum = np.nancumsum(data, axis=data.ndim - 1, dtype=ii_dtype)
        ii = np.nancumsum(line_cumsum, axis=data.ndim - 2)

        # if input data is a masked array, ii is a masked array
        if hasattr(ii, 'mask'):
            # get the data of the masked array
            ii = ii.data

        # compute local sum at each pixel from integral image
        output = np.zeros(data.shape, dtype=ii.dtype)
        posd = (kernel_width + 1) // 2
        posf = kernel_width - posd
        if data.ndim == 3:
            output[:, posd:-posf, posd:-posf] = ii[:, :-kernel_width, :-kernel_width] \
                + ii[:, kernel_width:, kernel_width:] \
                - ii[:, :-kernel_width, kernel_width:] \
                - ii[:, kernel_width:, :-kernel_width]
        else:
            output[posd:-posf, posd:-posf] = ii[:-kernel_width, :-kernel_width] \
                + ii[kernel_width:, kernel_width:] \
                - ii[:-kernel_width, kernel_width:] \
                - ii[kernel_width:, :-kernel_width]

    return output.astype(data.dtype)


def median(input_data, **kwargs):
    """Median filter computed using scipy.ndimage.median_filter

    Args:
        input_data: list of bands as a numpy ndarray of dims 3.
        kwargs : parameters of the computing: kernel_size

    Returns:
        The numpy array with the results
    """
    if len(input_data.shape) != 3:
        raise ValueError("adaptive_gaussian only accepts 3 dims numpy arrays")

    kernel_size = kwargs.get('kernel_size', 8)
    output = ndimage.median_filter(input_data, size=(1, kernel_size, kernel_size))
    return output


def local_sum(input_data, **kwargs):
    """Local sum computed using integral image

    Args:
        bands: list of bands as a numpy ndarray of dims 2 or 3.
        kwargs : parameters of the computing: kernel_size

    Returns:
        The numpy array with the results
    """
    kernel_size = kwargs.get('kernel_size', 8)
    # compute local sum of band pixels
    output = _local_sum(input_data, kernel_size)
    return output


def local_mean(input_data, **kwargs):
    """Local mean computed using integral image

    Args:
        bands: list of bands as a numpy ndarray of dims 2 or 3.
        kwargs : parameters of the computing: kernel_size

    Returns:
        The numpy array with the results
    """
    kernel_size = kwargs.get('kernel_size', 8)
    # compute local sum of band pixels
    output = _local_sum(input_data, kernel_size)
    # compute local sum of band mask: number of valid pixels
    # in the kernel
    if ma.is_masked(input_data):
        valid = _local_sum(1 - input_data.mask, kernel_size)
    else:
        valid = kernel_size ** 2
    # compute mean for the band
    return np.divide(output, valid, out=np.zeros_like(output), where=valid != 0)


def adaptive_gaussian(input_data, **kwargs):
    """Adaptive Gaussian Filter

    Args:
        bands: list of bands as a numpy ndarray of dims 3. First dimension muse be of size 1
        kwargs : parameters of the computing: kernel_size and sigma

    Returns:
        The numpy array with the results
    """
    if len(input_data.shape) != 3:
        raise ValueError("adaptive_gaussian only accepts 3 dims numpy arrays")
    if input_data.shape[0] != 1:
        raise ValueError("adaptive_gaussian only accepts numpy arrays with first dim of size 1")

    kernel_size = kwargs.get('kernel_size', 8)
    sigma = kwargs.get('sigma', 1)
    dtype = input_data.dtype

    w_1 = (input_data[0, :, :-2] - input_data[0, :, 2:]) ** 2
    w_2 = (input_data[0, :-2, :] - input_data[0, 2:, :]) ** 2
    w = np.exp(-(w_1[1:-1, :] + w_2[:, 1:-1]) / (2 * sigma ** 2))
    w_sum = signal.convolve2d(w, np.ones((3, 3), dtype=dtype), boundary='symm', mode='same')
    w_sum += np.finfo(dtype).eps
    out = input_data
    for i in range(kernel_size):
        prod = w * out[0, 1:-1, 1:-1]
        conv = signal.convolve2d(prod, np.ones((3, 3), dtype=dtype), boundary='symm', mode='same')
        out[0, 1:-1, 1:-1] = conv / w_sum
    return out


def svf(input_data, **kwargs):
    """Sky View Factor computing. The input data consist in a Digital Height Model.

    Args:
        bands: list of bands as a numpy ndarray of dims 3. First dimension is of size 1.
        kwargs: parameters of the computing: radius, directions, resolution and altitude.

    Returns:
        The numpy array with the results
    """
    if len(input_data.shape) != 3:
        raise ValueError("svf only accepts 3 dims numpy arrays")
    if input_data.shape[0] != 1:
        raise ValueError("svf only accepts numpy arrays with first dim of size 1")

    radius = kwargs.get('radius', 8)
    nb_directions = kwargs.get('directions', 12)
    resolution = kwargs.get('resolution', 0.5)
    altitude = kwargs.get('altitude', None)

    # initialize output
    shape = input_data.shape
    out = np.zeros(shape, dtype=np.float32)

    # prevent nodata problem
    input_band = np.nan_to_num(input_data[0], copy=False, nan=0)

    # compute directions
    axes = [_bresenham_line(360 * i / nb_directions, radius)
            for i in range(nb_directions)]

    # get altitude of current point to consider for computing elevation angle
    if altitude is None:
        view = input_band[radius: shape[1] - radius, radius: shape[2] - radius]
    else:
        view = altitude

    # iterate over axes to identify the largest elevation in the radius
    for axe in axes:
        ratios = np.zeros((shape[1] - 2 * radius, shape[2] - 2 * radius), dtype=np.float32)
        for x_tr, y_tr, r in axe:
            new_ratios = input_band[radius + x_tr: shape[1] - radius + x_tr,
                                    radius + y_tr: shape[2] - radius + y_tr] - view
            # tangente de l'angle
            new_ratios /= (r * resolution)
            ratios = np.maximum(ratios, new_ratios)

        # SVF = (cosinus de l'angle avec la relation : cos² = sqrt(1 / (1+tan²))
        ratios = 1 / np.sqrt(ratios**2 + 1)  # = np.sin(np.arctan(ratios / self.pixel_size))
        out[0, radius: shape[1] - radius, radius: shape[2] - radius] += ratios

    out /= nb_directions
    return out


def hillshade(input_data, **kwargs):
    """Hillshades computing. The input data consist in a Digital Height Model.

    Args:
        bands: list of bands as a numpy ndarray of dims 3. First dimension is of size 1.
        kwargs: parameters of the computing: elevation, azimuth, radius and resolution

    Returns:
        The numpy array with the results
    """
    if len(input_data.shape) != 3:
        raise ValueError("hillshade only accepts 3 dims numpy arrays")
    if input_data.shape[0] != 1:
        raise ValueError("hillshade only accepts numpy arrays with first dim of size 1")

    elevation = np.radians(kwargs.get('elevation', 0.0))
    azimuth = kwargs.get('azimuth', 0.0)
    radius = kwargs.get('radius', 8)
    resolution = kwargs.get('resolution', 0.5)

    # initialize output
    shape = input_data.shape
    out = np.zeros(shape, dtype=bool)

    # prevent nodata problem
    input_band = np.nan_to_num(input_data[0], copy=False, nan=0)

    # compute direction
    axe = _bresenham_line(180 - azimuth, radius)

    # identify the largest elevation in the radius
    view = input_band[radius: shape[1] - radius, radius: shape[2] - radius]
    ratios = np.zeros((shape[1] - 2 * radius, shape[2] - 2 * radius), dtype=np.float32)
    for x_tr, y_tr, r in axe:
        new_ratios = input_band[radius + x_tr: shape[1] - radius + x_tr,
                                radius + y_tr: shape[2] - radius + y_tr] - view
        # tangente de l'angle
        new_ratios /= (r * resolution)
        ratios = np.maximum(ratios, new_ratios)

    angles = np.arctan(ratios)
    out[0, radius: shape[1] - radius, radius: shape[2] - radius] = angles > elevation
    return out


def _bresenham_line(theta, radius):
    """Implementation of the Bresenham's line algorithm:
    https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm

    Params:
        theta: theta angle (in degrees)
        radius: size of the line

    Returns:
        Tuple with the coordinates of the line points from point (0, 0)
        ((0, 0) is not included).
    """
    x, y = 0, 0
    dx = math.cos(math.radians(theta))
    dy = math.sin(math.radians(theta))
    sx = -1 if dx < 0 else 1
    sy = -1 if dy < 0 else 1
    pts = list()
    r = 0
    if abs(dx) > abs(dy):
        delta = abs(math.tan(math.radians(theta)))
        err = 0
        while r < radius:
            x += sx
            err += delta
            if err > 0.5:
                y += sy
                err -= 1.0
            r = math.sqrt(x ** 2 + y ** 2)
            pts.append((x, y, r))
    else:
        delta = abs(math.tan(math.radians(90 - theta)))
        err = 0
        while r < radius:
            y += sy
            err += delta
            if err > 0.5:
                x += sx
                err -= 1.0
            r = math.sqrt(x ** 2 + y ** 2)
            pts.append((x, y, r))

    return pts
