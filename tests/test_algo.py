#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import numpy.ma as ma

from eolab.rastertools.processing import algo

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


def test_local_sum():
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


def test_local_mean():

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

    array = ma.array(band, mask=mask)

    # output shape is array shape - kernel_width
    output = algo.local_mean(array, kernel_size=kernel_width)

    # if kernel_width is odd, output is too large
    output = output[radius:-radius, radius:-radius]

    assert (output == result).all()


def test_bresenham_line():

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
