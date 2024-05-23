#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the filtering tool
"""
import eolab.rastertools.cli as cli
from eolab.rastertools import Filtering


def create_argparser(rastertools_parsers):
    """Adds the filtering subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                filtering.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    parser = rastertools_parsers.add_parser(
        "filter", aliases=["fi"],
        help="Apply a filter to a set of images",
        description="Apply a filter to a set of images.")

    # create a subparser to configure each kind of filter
    sub_parser = parser.add_subparsers(title='Filters')

    for rasterfilter in Filtering.get_default_filters():
        # new parser for the filter
        filterparser = sub_parser.add_parser(
            rasterfilter.name,
            aliases=rasterfilter.aliases,
            help=rasterfilter.help,
            description=rasterfilter.description,
            epilog="By default only first band is computed.")

        # add argument declared in the filter definition
        for argument_name, argument_params in rasterfilter.arguments.items():
            filterparser.add_argument(f"--{argument_name}", **argument_params)

        # add common arguments (inputs, output dir, window size, pad mode)
        filterparser.add_argument(
            "inputs",
            nargs='+',
            help="Input file to process (e.g. Sentinel2 L2A MAJA from THEIA). "
                 "You can provide a single file with extension \".lst\" (e.g. \"filtering.lst\") "
                 "that lists the input files to process (one input file per line in .lst)")
        cli.with_outputdir_arguments(filterparser)
        cli.with_window_arguments(filterparser)
        cli.with_bands_arguments(filterparser)

        # set the default commmand to run for this filter parser
        filterparser.set_defaults(filter=rasterfilter.name)

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_filtering)

    return rastertools_parsers


def create_filtering(args) -> Filtering:
    """Create and configure a new rastertool "Filtering" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Filtering`: The configured rastertool to run
    """
    argsdict = vars(args)

    # get the bands to process
    if args.all_bands:
        bands = None
    else:
        bands = list(map(int, args.bands)) if args.bands else [1]

    # create the rastertool object
    raster_filters_dict = {rf.name: rf for rf in Filtering.get_default_filters()}
    tool = Filtering(raster_filters_dict[args.filter], args.kernel_size, bands)

    # set up config with args values
    tool.with_output(args.output) \
        .with_windows(args.window_size, args.pad) \
        .with_filter_configuration(argsdict)

    return tool
