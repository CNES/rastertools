#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the timeseries tool
"""
from datetime import datetime

import eolab.rastertools.cli as cli
from eolab.rastertools import RastertoolConfigurationException, Timeseries


def create_argparser(rastertools_parsers):
    """Adds the timeseries subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                timeseries.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    parser = rastertools_parsers.add_parser(
        "timeseries", aliases=["ts"],
        help="Temporal gap filling of an image time series",
        description="Generate a timeseries of images (without gaps) from a set of input images. "
                    "Data not present in the input images (no image for the date or masked data) "
                    "are interpolated (with linear interpolation) so that all gaps are filled.",
        epilog="By default only first band is computed.")
    parser.add_argument(
        "inputs",
        nargs='+',
        help="Input files to process (e.g. Sentinel2 L2A MAJA from THEIA). "
             "You can provide a single file with extension \".lst\" (e.g. \"speed.lst\") "
             "that lists the input files to process (one input file per line in .lst)")
    cli.with_bands_arguments(parser)
    cli.with_outputdir_arguments(parser)
    parser.add_argument(
        "-s",
        "--start_date",
        help="Start date of the timeseries to generate in the following format: yyyy-MM-dd")
    parser.add_argument(
        "-e",
        "--end_date",
        help="End date of the timeseries to generate in the following format: yyyy-MM-dd")
    parser.add_argument(
        "-p",
        "--time_period",
        type=int,
        help="Time period (number of days) between two consecutive images in the timeseries "
             "to generate e.g. 10 = generate one image every 10 days")
    cli.with_window_arguments(parser, pad=False)

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_timeseries)

    return rastertools_parsers


def create_timeseries(args) -> Timeseries:
    """Create and configure a new rastertool "Timeseries" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Timeseries`: The configured rastertool to run
    """

    # get the bands to process
    if args.all_bands:
        bands = None
    else:
        bands = list(map(int, args.bands)) if args.bands else [1]

    # convert start/end dates to datetime
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    except Exception:
        raise RastertoolConfigurationException(
            f"Invalid format for start date: {args.start_date} (must be %Y-%m-%d)")

    # convert start/end dates to datetime
    try:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    except Exception:
        raise RastertoolConfigurationException(
            f"Invalid format for end date: {args.end_date} (must be %Y-%m-%d)")

    # create the rastertool object
    tool = Timeseries(start_date, end_date, args.time_period, bands)

    # set up config with args values
    tool.with_output(args.output)
    tool.with_windows(args.window_size)

    return tool
