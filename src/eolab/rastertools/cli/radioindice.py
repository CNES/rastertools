#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the radioindice tool
"""
import eolab.rastertools.cli as cli
from eolab.rastertools import RastertoolConfigurationException, Radioindice
from eolab.rastertools.product import BandChannel
from eolab.rastertools.processing import RadioindiceProcessing


def create_argparser(rastertools_parsers):
    """Adds the radioindice subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                radioindice.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    indicenames = ', '.join(sorted([indice.name for indice in Radioindice.get_default_indices()]))
    parser = rastertools_parsers.add_parser(
        "radioindice", aliases=["ri"],
        help="Compute radiometric indices",
        description="Compute a list of radiometric indices (NDVI, NDWI, etc.) on a raster image",
        epilog="If no indice option is explicitly set, NDVI, NDWI and NDWI2 are computed.")
    parser.add_argument(
        "inputs",
        nargs='+',
        help="Input file to process (e.g. Sentinel2 L2A MAJA from THEIA). "
             "You can provide a single file with extension \".lst\" (e.g. \"radioindice.lst\") "
             "that lists the input files to process (one input file per line in .lst)")
    cli.with_outputdir_arguments(parser)
    parser.add_argument(
        '-m',
        '--merge',
        dest="merge",
        action="store_true",
        help="Merge all indices in the same image (i.e. one band per indice).")
    parser.add_argument(
        '-r',
        '--roi',
        dest="roi",
        help="Region of interest in the input image (vector)")
    indices_pc = parser.add_argument_group("Options to select the indices to compute")
    indices_pc.add_argument(
        '-i',
        '--indices',
        dest="indices",
        nargs="+",
        help="List of indices to compute"
             f"Possible indices are: {indicenames}")
    for indice in Radioindice.get_default_indices():
        indices_pc.add_argument(
            f"--{indice.name}",
            dest=indice.name,
            action="store_true",
            help=f"Compute {indice.name} indice")
    indices_pc.add_argument(
        '-nd',
        "-normalized_difference",
        nargs=2,
        action="append",
        metavar=("band1", "band2"),
        help="Compute the normalized difference of two bands defined as parameter of this option, "
             "e.g. \"-nd red nir\" will compute (red-nir)/(red+nir). "
             "See eolab.rastertools.product.rastertype.BandChannel for the list of bands names. "
             "Several nd options can be set to compute several normalized differences.")
    cli.with_window_arguments(parser, pad=False)

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_radioindice)

    return rastertools_parsers


def create_radioindice(args) -> Radioindice:
    """Create and configure a new rastertool "Radioindice" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Radioindice`: The configured rastertool to run
    """
    indices_to_compute = []
    argsdict = vars(args)

    # append indices defined with --<name_of_indice>
    indices_to_compute.extend([indice for indice in Radioindice.get_default_indices()
                               if argsdict[indice.name]])
    # append indices defined with --indices
    if args.indices:
        indices_dict = {indice.name: indice for indice in Radioindice.get_default_indices()}
        for ind in args.indices:
            if ind in indices_dict:
                indices_to_compute.append(indices_dict[ind])
            else:
                raise RastertoolConfigurationException(f"Invalid indice name: {ind}")

    if args.nd:
        for nd in args.nd:
            if nd[0] in BandChannel.__members__ and nd[1] in BandChannel.__members__:
                channel1 = BandChannel[nd[0]]
                channel2 = BandChannel[nd[1]]
                new_indice = RadioindiceProcessing(f"nd[{nd[0]}-{nd[1]}]").with_channels(
                    [channel2, channel1])
                indices_to_compute.append(new_indice)
            else:
                raise RastertoolConfigurationException(
                    f"Invalid band(s) in normalized difference: {nd[0]} and/or {nd[1]}")

    # handle special case: no indice setup
    if len(indices_to_compute) == 0:
        indices_to_compute.append(Radioindice.ndvi)
        indices_to_compute.append(Radioindice.ndwi)
        indices_to_compute.append(Radioindice.ndwi2)

    # create the rastertool object
    tool = Radioindice(indices_to_compute)

    # set up config with args values
    tool.with_output(args.output, args.merge)
    tool.with_roi(args.roi)
    tool.with_windows(args.window_size)

    return tool
