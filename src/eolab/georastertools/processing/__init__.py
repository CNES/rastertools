# -*- coding: utf-8 -*-
"""This module contains the georastertools processing algorithms.
"""

# importing the RasterProcessing and children classes
from eolab.georastertools.processing.rasterproc import RasterProcessing
from eolab.georastertools.processing.rasterproc import RadioindiceProcessing, RasterFilter
# importing the methods that perform the raster processings
from eolab.georastertools.processing.sliding import compute_sliding
from eolab.georastertools.processing.stats import compute_zonal_stats, compute_zonal_stats_per_category
from eolab.georastertools.processing.stats import extract_zonal_outliers, plot_stats

__all__ = [
    "RasterProcessing", "RadioindiceProcessing", "RasterFilter",
    "compute_sliding",
    "compute_zonal_stats", "compute_zonal_stats_per_category",
    "extract_zonal_outliers", "plot_stats"
]

# register the matplot lib converters that are required for plotting datetime values
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
