#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the hillshade tool
"""
import eolab.rastertools.cli as cli
from eolab.rastertools import Hillshade


def create_argparser(rastertools_parsers):
    """Adds the hillshade subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                hillshade.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    parser = rastertools_parsers.add_parser(
        "hillshade", aliases=["hs"],
        help="Compute hillshades of a Digital Elevation / Surface / Height Model "
             "(a raster containing the height of the point as pixel values)",
        description="Compute hillshades of a Digital Elevation / Surface / Height Model.")

    # add specific arguments of the hillshade processing
    arguments = {
        "elevation": {
            "required": True,
            "type": float,
            "help": "Elevation of the sun in degrees, [0°, 90°] where 90°=zenith and 0°=horizon"
        },
        "azimuth": {
            "required": True,
            "type": float,
            "help": "Azimuth of the sun in degrees, [0°, 360°] "
                    "where 0°=north, 90°=east, 180°=south and 270°=west"
        },
        "radius": {
            "required": False,
            "type": int,
            "help": "Max distance (in pixels) around a point to evaluate horizontal"
                    " elevation angle. If not set, it is automatically computed from"
                    " the range of altitudes in the digital model."
        },
        "resolution": {
            "default": 0.5,
            "required": True,
            "type": float,
            "help": "Pixel resolution in meter"
        },
    }
    # add argument declared in the hillshade processing definition
    for argument_name, argument_params in arguments.items():
        parser.add_argument(f"--{argument_name}", **argument_params)

    # add common arguments (inputs, output dir, window size, pad mode)
    parser.add_argument(
        "inputs",
        nargs='+',
        help="Input file to process (i.e. geotiff that contains the height "
             "of the points as pixel values). "
             "You can provide a single file with extension \".lst\" (e.g. \"filtering.lst\") "
             "that lists the input files to process (one input file per line in .lst)")
    cli.with_outputdir_arguments(parser)
    cli.with_window_arguments(parser)
    cli.with_max_radius_arguments(parser)

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_hillshade)

    return rastertools_parsers


def create_hillshade(args) -> Hillshade:
    """Create and configure a new rastertool "Hillshade" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Hillshade`: The configured rastertool to run
    """
    # create the rastertool object
    tool = Hillshade(args.elevation, args.azimuth, args.resolution, args.radius)

    # set up config with args values
    tool.with_output(args.output)
    tool.with_windows(args.window_size, args.pad)
    tool.with_max_radius(args.max_radius)

    return tool
