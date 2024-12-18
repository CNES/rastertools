# -*- coding: utf-8 -*-
"""This module contains the eolab's georastertools CLI and API
"""
from importlib.metadata import version

# Change here if project is renamed and does not equal the package name
dist_name = "georastertools"
__version__ = version(dist_name)

from eolab.georastertools.georastertools import RastertoolConfigurationException
from eolab.georastertools.georastertools import Rastertool, Windowable
# import rastertool Filtering
from eolab.georastertools.filtering import Filtering
# import rastertool Hillshade
from eolab.georastertools.hillshade import Hillshade
# import rastertool Radioindice
from eolab.georastertools.radioindice import Radioindice
# import rastertool Speed
from eolab.georastertools.speed import Speed
# import rastertool SVF
from eolab.georastertools.svf import SVF
# import rastertool Tiling
from eolab.georastertools.tiling import Tiling
# import rastertool Timeseries
from eolab.georastertools.timeseries import Timeseries
# import rastertool Zonalstats
from eolab.georastertools.zonalstats import Zonalstats
# import the method to run a rastertool
from eolab.georastertools.main import georastertools, add_custom_rastertypes

__all__ = [
    "RastertoolConfigurationException", "Rastertool", "Windowable",
    "Filtering", "Hillshade", "Radioindice", "Speed", "SVF", "Tiling",
    "Timeseries", "Zonalstats",
    "run_tool", "add_custom_rastertypes"
]
