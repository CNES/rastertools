#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the speed tool
"""
import eolab.rastertools.cli as cli
from eolab.rastertools import Speed


def create_argparser(rastertools_parsers):
    """Adds the speed subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                speed.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    parser = rastertools_parsers.add_parser(
        "speed", aliases=["sp"],
        help="Compute speed of rasters",
        description="Compute the speed of radiometric values of several raster images",
        epilog="By default only first band is computed.")
    parser.add_argument(
        "inputs",
        nargs='+',
        help="Input files to process (e.g. Sentinel2 L2A MAJA from THEIA). "
             "You can provide a single file with extension \".lst\" (e.g. \"speed.lst\") "
             "that lists the input files to process (one input file per line in .lst)")
    cli.with_bands_arguments(parser)
    cli.with_outputdir_arguments(parser)

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_speed)

    return rastertools_parsers


def create_speed(args) -> Speed:
    """Create and configure a new rastertool "Speed" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Speed`: The configured rastertool to run
    """

    # get the bands to process
    if args.all_bands:
        bands = None
    else:
        bands = list(map(int, args.bands)) if args.bands else [1]

    # create the rastertool object
    tool = Speed(bands)

    # set up config with args values
    tool.with_output(args.output)

    return tool
