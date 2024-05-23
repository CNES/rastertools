# -*- coding: utf-8 -*-
"""This module contains the eolab's rastertools CLI and API
"""
from importlib.metadata import version

# Change here if project is renamed and does not equal the package name
dist_name = "rastertools"
__version__ = version(dist_name)

from eolab.rastertools.rastertools import RastertoolConfigurationException
from eolab.rastertools.rastertools import Rastertool, Windowable
# import rastertool Filtering
from eolab.rastertools.filtering import Filtering
# import rastertool Hillshade
from eolab.rastertools.hillshade import Hillshade
# import rastertool Radioindice
from eolab.rastertools.radioindice import Radioindice
# import rastertool Speed
from eolab.rastertools.speed import Speed
# import rastertool SVF
from eolab.rastertools.svf import SVF
# import rastertool Tiling
from eolab.rastertools.tiling import Tiling
# import rastertool Timeseries
from eolab.rastertools.timeseries import Timeseries
# import rastertool Zonalstats
from eolab.rastertools.zonalstats import Zonalstats
# import the method to run a rastertool
from eolab.rastertools.main import run_tool, add_custom_rastertypes

__all__ = [
    "RastertoolConfigurationException", "Rastertool", "Windowable",
    "Filtering", "Hillshade", "Radioindice", "Speed", "SVF", "Tiling",
    "Timeseries", "Zonalstats",
    "run_tool", "add_custom_rastertypes"
]
