#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rasterio.windows import Window

from eolab.rastertools import utils
from eolab.rastertools.processing import sliding

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


def test_slices_1d():

    results = [
        [(0, 3)],
        [(0, 5)],
        [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30)],
        [(0, 9), (5, 14), (10, 19), (15, 24), (20, 29), (25, 30)],
        [(-2, 7), (3, 12), (8, 17), (13, 22), (18, 27), (23, 32)],
        [(0, 5), (6, 11), (12, 17), (18, 18)]
    ]

    args = [
        # window size > max value
        (5, 2, 3),
        # window size == max value
        (5, 2, 5),
        # standard case
        (5, 5, 30),
        # overlap but no padding
        (9, 5, 30),
        # overlap with padding
        (9, 5, 32, -2),
        # segments disjoints
        (5, 6, 18)
    ]

    for arg, res in zip(args, results):
        assert res == list(utils.slices_1d(*arg))


def test_slices_2d():
    results = [
        [(0, 3, 0, 3)],
        [(0, 6, 0, 6), (0, 6, 6, 12), (0, 6, 12, 18),
         (6, 12, 0, 6), (6, 12, 6, 12), (6, 12, 12, 18)],
        [(0, 10, 0, 10), (0, 10, 6, 16), (0, 10, 12, 18),
         (6, 16, 0, 10), (6, 16, 6, 16), (6, 16, 12, 18),
         (12, 18, 0, 10), (12, 18, 6, 16), (12, 18, 12, 18)],
        [(-1, 7, -1, 5), (-1, 7, 3, 9), (-1, 7, 7, 13),
         (5, 13, -1, 5), (5, 13, 3, 9), (5, 13, 7, 13),
         (11, 19, -1, 5), (11, 19, 3, 9), (11, 19, 7, 13)],
        [(0, 8, 0, 6), (0, 8, 9, 12),
         (11, 18, 0, 6), (11, 18, 9, 12)]
    ]

    args = [
        # window size > max value
        (5, 2, 3),
        # default case
        (6, 6, (18, 12)),
        # overlap but no padding
        (10, 6, 18),
        # overlap with padding
        ((6, 8), (4, 6), (13, 19), (-1, -1)),
        # segments disjoints
        ((6, 8), (9, 11), (12, 18))
    ]

    for arg, res in zip(args, results):
        assert res == list(utils.slices_2d(*arg))


def test_sliding_windows():
    args = [
        # window size > image size
        (2, 5, 0),
        # window size > image size
        (2, 5, 1),
        # default case
        (18, 6, 0),
        # overlap
        (18, 10, 2),
        # overlap with padding
        ((12, 18), (8, 12), (1, 2))
    ]

    pad0 = (0, 0)
    pad1s = (1, 0)
    pad1e = (0, 1)
    pad2s = (2, 0)
    pad2e = (0, 2)
    results = [
        [(Window(0, 0, 2, 2), (pad0, pad0), Window(0, 0, 2, 2))],
        [(Window(0, 0, 2, 2), ((1, 1), (1, 1)), Window(0, 0, 2, 2))],
        [(Window(0, 0, 6, 6), (pad0, pad0), Window(0, 0, 6, 6)),
         (Window(6, 0, 6, 6), (pad0, pad0), Window(6, 0, 6, 6)),
         (Window(12, 0, 6, 6), (pad0, pad0), Window(12, 0, 6, 6)),
         (Window(0, 6, 6, 6), (pad0, pad0), Window(0, 6, 6, 6)),
         (Window(6, 6, 6, 6), (pad0, pad0), Window(6, 6, 6, 6)),
         (Window(12, 6, 6, 6), (pad0, pad0), Window(12, 6, 6, 6)),
         (Window(0, 12, 6, 6), (pad0, pad0), Window(0, 12, 6, 6)),
         (Window(6, 12, 6, 6), (pad0, pad0), Window(6, 12, 6, 6)),
         (Window(12, 12, 6, 6), (pad0, pad0), Window(12, 12, 6, 6))],
        [(Window(0, 0, 8, 8), (pad2s, pad2s), Window(0, 0, 6, 6)),
         (Window(4, 0, 10, 8), (pad0, pad2s), Window(6, 0, 6, 6)),
         (Window(10, 0, 8, 8), (pad2e, pad2s), Window(12, 0, 6, 6)),
         (Window(0, 4, 8, 10), (pad2s, pad0), Window(0, 6, 6, 6)),
         (Window(4, 4, 10, 10), (pad0, pad0), Window(6, 6, 6, 6)),
         (Window(10, 4, 8, 10), (pad2e, pad0), Window(12, 6, 6, 6)),
         (Window(0, 10, 8, 8), (pad2s, pad2e), Window(0, 12, 6, 6)),
         (Window(4, 10, 10, 8), (pad0, pad2e), Window(6, 12, 6, 6)),
         (Window(10, 10, 8, 8), (pad2e, pad2e), Window(12, 12, 6, 6))],
        [(Window(0, 0, 7, 10), (pad1s, pad2s), Window(0, 0, 6, 8)),
         (Window(5, 0, 7, 10), (pad1e, pad2s), Window(6, 0, 6, 8)),
         (Window(0, 6, 7, 12), (pad1s, pad0), Window(0, 8, 6, 8)),
         (Window(5, 6, 7, 12), (pad1e, pad0), Window(6, 8, 6, 8)),
         (Window(0, 14, 7, 4), (pad1s, pad2e), Window(0, 16, 6, 2)),
         (Window(5, 14, 7, 4), (pad1e, pad2e), Window(6, 16, 6, 2))]
    ]

    for arg, res in zip(args, results):
        assert res == list(sliding._sliding_windows(*arg))
