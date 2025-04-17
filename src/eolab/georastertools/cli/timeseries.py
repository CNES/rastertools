#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the timeseries tool
"""
from datetime import datetime

from eolab.georastertools import Timeseries
from eolab.georastertools.cli.utils_cli import apply_process, win_opt, all_opt, band_opt
from eolab.georastertools import RastertoolConfigurationException
import click
import sys
import os
import logging

_logger = logging.getLogger(__name__)
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

#Timeseries command
@click.command("timeseries",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.option("-s","--start_date", help="Start date of the timeseries to generate in the following format: yyyy-MM-dd")

@click.option("-e", "--end_date", help="End date of the timeseries to generate in the following format: yyyy-MM-dd")

@click.option("-p", "--time_period",type=int, help="Time period (number of days) between two consecutive images in the timeseries "
             "to generate e.g. 10 = generate one image every 10 days")

@band_opt
@all_opt
@win_opt
@click.pass_context

def timeseries(ctx, inputs : list, bands : list, all_bands : bool, output : str, start_date : str, end_date : str, time_period : int, window_size : int) :
    """
    Generate a timeseries of images (without gaps) from a set of input images.
    Data not present in the input images (e.g., missing images for specific dates or masked data) are interpolated
    (with linear interpolation) so that all gaps in the timeseries are filled.

    This command is useful for generating continuous timeseries data, even when some input images are missing
    or contain masked values.

    Arguments:

    inputs TEXT

        Input file to process (e.g. Sentinel2 L2A MAJA from THEIA).
    You can provide a single file with extension \".lst\" (e.g. \"speed.lst\") that lists
    the input files to process (one input file per line in .lst).
    """
    # get the bands to process
    if all_bands:
        bands = None
    else:
        bands = list(map(int, bands)) if bands else [1]

    # convert start/end dates to datetime
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    except Exception:
        raise RastertoolConfigurationException(
            f"Invalid format for start date: {start_date} (must be %Y-%m-%d)")

    # convert start/end dates to datetime
    try:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        raise RastertoolConfigurationException(
            f"Invalid format for end date: {end_date} (must be %Y-%m-%d)")

    # create the rastertool object
    tool = Timeseries(start_date, end_date, time_period, bands)

    # set up config with args values
    tool.with_output(output)
    tool.with_windows(window_size)

    apply_process(ctx, tool, inputs)