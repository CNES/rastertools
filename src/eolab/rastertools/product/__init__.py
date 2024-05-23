# -*- coding: utf-8 -*-
"""This module defines the raster product definition.
"""
import numpy as np

from eolab.rastertools.product.rastertype import Band, BandChannel, RasterType
from eolab.rastertools.product.rasterproduct import RasterProduct

# import classes of rasterproduct and rastertype submodules
__all__ = [
    "Band", "BandChannel", "RasterType", "RasterProduct"
]

# initialize the default raster types
import importlib.resources
import json

RasterType.add(json.load(importlib.resources.open_binary("eolab.rastertools.product", "rastertypes.json")))


def s2_maja_mask(in_ar, out_ar, xoff, yoff, xsize, ysize,
                 raster_xsize, raster_ysize, buf_radius, gt, **kwargs):
    """Computes the mask band from the Sentinel2 L2A MAJA cloud mask
    """
    out_ar[:] = np.where(np.sum(in_ar, axis=0) == 0, 1, 0)
