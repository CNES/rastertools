# -*- coding: utf-8 -*-
"""This module contains the eolab's georastertools CLI and API
"""
from importlib.metadata import version
import os

# Change here if project is renamed and does not equal the package name
dist_name = "georastertools"
__version__ = version(dist_name)

from eolab.georastertools.georastertools import RastertoolConfigurationException
from eolab.georastertools.georastertools import Rastertool, Windowable

from eolab.georastertools.filtering import Filtering
from eolab.georastertools.hillshade import Hillshade
from eolab.georastertools.radioindice import Radioindice
from eolab.georastertools.speed import Speed
from eolab.georastertools.svf import SVF
from eolab.georastertools.tiling import Tiling
from eolab.georastertools.timeseries import Timeseries
from eolab.georastertools.zonalstats import Zonalstats
# import the method to run a rastertool
from eolab.georastertools.main import georastertools, add_custom_rastertypes


__all__ = [
    "RastertoolConfigurationException", "Rastertool", "Windowable",
    "Filtering", "Hillshade", "Radioindice", "Speed", "SVF", "Tiling",
    "Timeseries", "Zonalstats",
    "run_tool", "add_custom_rastertypes"
]
