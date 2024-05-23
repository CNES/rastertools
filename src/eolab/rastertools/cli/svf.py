#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the SVF (Sky View Factor) tool
"""
import eolab.rastertools.cli as cli
from eolab.rastertools import SVF


def create_argparser(rastertools_parsers):
    """Adds the SVF subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                svf.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    parser = rastertools_parsers.add_parser(
        "svf",
        help="Compute Sky View Factor of a Digital Height Model",
        description="Compute Sky View Factor of a Digital Height Model.")

    # add specific argument of the svf processing
    arguments = {
        "radius": {
            "default": 16,
            "required": True,
            "type": int,
            "help": "Max distance (in pixels) around a point to evaluate horizontal"
                    " elevation angle"
        },
        "directions": {
            "default": 12,
            "required": True,
            "type": int,
            "help": "Number of directions on which to compute the horizon elevation angle"
        },
        "resolution": {
            "default": 0.5,
            "required": True,
            "type": float,
            "help": "Pixel resolution in meter"
        },
        "altitude": {
            "type": int,
            "help": "Reference altitude to use for computing the SVF. If this option is not"
                    " specified, SVF is computed for every point at the altitude of the point"
        }
    }
    for argument_name, argument_params in arguments.items():
        parser.add_argument(f"--{argument_name}", **argument_params)

    # add common arguments (inputs, output dir, window size, pad mode)
    parser.add_argument(
        "inputs",
        nargs='+',
        help="Input file to process (i.e. geotiff corresponding to a Digital Height Model). "
             "You can provide a single file with extension \".lst\" (e.g. \"filtering.lst\") "
             "that lists the input files to process (one input file per line in .lst)")
    cli.with_outputdir_arguments(parser)
    cli.with_window_arguments(parser)

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_svf)

    return rastertools_parsers


def create_svf(args) -> SVF:
    """Create and configure a new rastertool "SVF" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.SVF`: The configured rastertool to run
    """

    # create the rastertool object
    tool = SVF(args.directions, args.radius, args.resolution)

    # set up config with args values
    tool.with_output(args.output)
    tool.with_windows(args.window_size, args.pad)
    if args.altitude is not None:
        tool.with_altitude(args.altitude)

    return tool
