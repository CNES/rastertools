#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines several utility methods for:

- handling path
- transforming data
- computing sliding windows
- ...
"""
import math
from pathlib import Path


def to_tuple(val):
    """Convert val as a tuple of two val"""
    return val if type(val) == tuple else (val, val)


def highest_power_of_2(n):
    """Get the highest power of 2 that is less than n
    """
    p = int(math.log(n, 2))
    return int(pow(2, p))


def is_dir(file) -> bool:
    """Check if file is a dir or not
    """
    path = to_path(file)
    return path.is_dir()


def to_path(file, default=None) -> Path:
    """Transform a file name to a Path
    """
    path = None
    if file:
        path = Path(file) if isinstance(file, str) else file
    else:
        path = Path(default) if isinstance(default, str) else default
    return path


def get_basename(file) -> str:
    """Get the basename of a Path
    """
    path = to_path(file)
    suffix = ''.join(path.suffixes).lower()
    basename = path.name
    if len(suffix) > 0:
        basename = path.name[:-len(suffix)]
    return basename


def get_suffixes(file) -> str:
    """Get the suffixes of a filename as a concatenated string
    """
    return ''.join(to_path(file).suffixes).lower()


def get_metadata_name(band: int, prefix: str, metadata: str):
    """Get the metadata name for the statistics to generate"""
    name = None
    if prefix is None or prefix == "":
        name = f"b{str(band)}.{metadata}"
    else:
        name = f"{prefix}.{metadata}"
    return name


def slices_1d(window_width, shift, stop, start=0):
    """Yield 1 dimension sliding windows according to the given parameters

    Args:
        window_width: window width
        shift: shift to apply between two consecutive windows
        stop: max value
        start: min value (default 0)

    Returns:
        min, max (int, int): start and end index of the sliding windows.
    """
    nb_iter = math.ceil(1 + max(0, (stop - start - window_width) / shift))
    return ((start + i * shift, min(start + window_width + i * shift, stop))
            for i in range(nb_iter))


def slices_2d(window_size, shift, stop, start=0):
    """Yield 2 dimensions sliding windows according to the given parameters.

    Args:
        window_size: window width and height
        shift: shift to apply between two consecutive windows
        stop: max value
        start: min value (default 0)

    Returns: Firstly yield number of windows, then
             window y_min, y_max, x_min, x_max for each windoww
    """
    width, height = to_tuple(window_size)
    shift_c, shift_r = to_tuple(shift)
    start_c, start_r = to_tuple(start)
    stop_c, stop_r = to_tuple(stop)

    window_c = list(slices_1d(width, shift_c, stop_c, start_c))
    window_r = list(slices_1d(height, shift_r, stop_r, start_r))

    return ((r_min, r_max, c_min, c_max)
            for r_min, r_max in window_r
            for c_min, c_max in window_c)
