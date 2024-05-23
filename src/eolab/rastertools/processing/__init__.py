# -*- coding: utf-8 -*-
"""This module contains the rastertools processing algorithms.
"""

# importing the RasterProcessing and children classes
from eolab.rastertools.processing.rasterproc import RasterProcessing
from eolab.rastertools.processing.rasterproc import RadioindiceProcessing, RasterFilter
# importing the methods that perform the raster processings
from eolab.rastertools.processing.sliding import compute_sliding
from eolab.rastertools.processing.stats import compute_zonal_stats, compute_zonal_stats_per_category
from eolab.rastertools.processing.stats import extract_zonal_outliers, plot_stats

__all__ = [
    "RasterProcessing", "RadioindiceProcessing", "RasterFilter",
    "compute_sliding",
    "compute_zonal_stats", "compute_zonal_stats_per_category",
    "extract_zonal_outliers", "plot_stats"
]

# register the matplot lib converters that are required for plotting datetime values
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
