#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the tiling tool
"""
import eolab.rastertools.cli as cli
from eolab.rastertools import Tiling


def create_argparser(rastertools_parsers):
    """Adds the tiling subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                tiling.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    parser = rastertools_parsers.add_parser(
        "tiling", aliases=["ti"],
        help="Generate image tiles",
        description="Generate tiles of an input raster image following the geometries "
                    "defined by a given grid")
    parser.add_argument(
        "inputs",
        nargs='+',
        help="Raster files to process. "
             "You can provide a single file with extension \".lst\" (e.g. \"tiling.lst\") "
             "that lists the input files to process (one input file per line in .lst)")
    parser.add_argument(
        '-g',
        '--grid',
        dest="grid_file",
        help="vector-based spatial data file containing the grid to use to generate the tiles",
        required=True)
    parser.add_argument(
        "--id_col",
        dest="id_column",
        help="Name of the column in the grid file used to number the tiles. When ids are defined,"
             " this argument is required to identify which column corresponds to the defined ids",
    )
    parser.add_argument(
        "--id",
        dest="id",
        help="Tiles ids of the grid to export as new tile, default all",
        nargs="+",
        type=int
    )
    cli.with_outputdir_arguments(parser)
    parser.add_argument(
        "-n",
        "--name",
        dest="output_name",
        help="Basename for the output raster tiles, default: \"{}_tile{}\". "
             "The basename must be defined as a formatted string where tile index is at position 1 "
             "and original filename is at position 0. For instance, tile{1}.tif will generate the "
             "filename tile75.tif for the tile id = 75.",
        default="{}_tile{}"
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="subdir_name",
        help="When each tile must be generated in a different subdir, it defines the naming "
             "convention for the subdir. It is a formatted string with one positional parameter "
             "corresponding to the tile index. For instance, tile{} will generate the subdir "
             "name tile75/ for the tile id = 75. By default, subdir is not defined and output "
             "files will be generated directly in the outputdir."
    )

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_tiling)

    return rastertools_parsers


def create_tiling(args) -> Tiling:
    """Create and configure a new rastertool "Tiling" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Tiling`: The configured rastertool to run
    """

    # create the rastertool object
    tool = Tiling(args.grid_file)

    # set up config with args values
    tool.with_output(args.output, args.output_name, args.subdir_name)
    tool.with_id_column(args.id_column, args.id)

    return tool
