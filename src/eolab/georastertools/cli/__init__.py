# -*- coding: utf-8 -*-
"""Module that defines the subcommands of georastertools.
This module's API is not intended for external use.
"""


def with_window_arguments(parser, pad: bool = True):
    """Add arguments to set the windowing parameters of the raster tool

    Args:
        parser: the argument parser to configure
        pad: whether to add an argument for the padding
    """
    # argument to set the window size
    parser.add_argument(
        '-ws',
        '--window_size',
        dest="window_size",
        default=1024,
        type=int,
        help="Size of tiles to distribute processing, default: 1024")

    if pad:
        # argument to set the padding strategy
        parser.add_argument(
            '-p',
            '--pad',
            dest="pad",
            default="edge",
            choices=["none", "edge", "maximum", "mean", "median",
                     "minimum", "reflect", "symmetric", "wrap"],
            help="Pad to use around the image, default : edge "
                 "(see https://numpy.org/doc/stable/reference/generated/numpy.pad.html"
                 " for more information)")


def with_outputdir_arguments(parser):
    """Add arguments to set the output dir

    Args:
        parser: the argument parser to configure
    """
    # argument to set the output dir
    parser.add_argument(
        '-o',
        '--output',
        dest="output",
        default=".",
        help="Output dir where to store results (by default current dir)")


def with_bands_arguments(parser):
    """Add arguments to set the list of bands to process

    Args:
        parser: the argument parser to configure
    """
    # two arguments to manage the bands selection:
    # - specify a list of requested bands
    # - or use all existing bands
    parser.add_argument(
        '-b',
        '--bands',
        nargs="+",
        dest="bands",
        help="List of bands to compute")
    parser.add_argument(
        '-a',
        '--all',
        dest="all_bands",
        action="store_true",
        help="Compute all bands")