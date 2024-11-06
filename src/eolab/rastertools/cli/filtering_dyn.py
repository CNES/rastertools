#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the filtering tool
"""
from eolab.rastertools import Filtering
#from eolab.rastertools.main import get_logger
from eolab.rastertools.cli.utils_cli import apply_process
#from eolab.rastertools.main import rastertools #Import the click group named rastertools
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def create_filtering(output : str, window_size : int, pad : str, argsdict : dict, filter : str, bands : list, kernel_size : int, all_bands : bool) -> Filtering:
    """
    This function initializes a `Filtering` tool instance and configures it with specified settings.

    It selects the filter type, kernel size, output settings, and processing bands. If `all_bands` is set
    to True, the filter will apply to all bands in the raster; otherwise, it applies only to specified bands.

    Args:
        output (str): The path for the filtered output file.
        window_size (int): Size of the processing window used by the filter.
        pad (str): Padding method used for windowing (e.g., 'reflect', 'constant', etc.).
        argsdict (dict): Dictionary of additional filter configuration arguments.
        filter (str): The filter type to apply (must be a valid name in `Filtering` filters).
        bands (list): List of bands to process. If empty and `all_bands` is False, defaults to [1].
        kernel_size (int): Size of the kernel used by the filter.
        all_bands (bool): Whether to apply the filter to all bands (True) or specific bands (False).

    Returns:
        :obj:`eolab.rastertools.Filtering`: A configured `Filtering` instance ready for execution.
    """
    # get the bands to process
    if all_bands:
        bands = None
    else:
        bands = list(map(int, bands)) if bands else [1]

    # create the rastertool object
    raster_filters_dict = {rf.name: rf for rf in Filtering.get_default_filters()}
    tool = Filtering(raster_filters_dict[filter], kernel_size, bands)

    # set up config with args values
    tool.with_output(output) \
        .with_windows(window_size, pad) \
        .with_filter_configuration(argsdict)

    return tool


inpt_arg = click.argument('inputs', type=str, nargs = -1, required = 1)

ker_opt = click.option('--kernel_size', type=int, help="Kernel size of the filter function, e.g. 3 means a square" 
                   "of 3x3 pixels on which the filter function is computed"
                   "(default: 8)")

out_opt = click.option('-o', '--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

win_opt = click.option('-ws', '--window_size', type=int, default = 1024, help="Size of tiles to distribute processing, default: 1024")

pad_opt = click.option('-p','--pad',default="edge", type=click.Choice(['none','edge','maximum','mean','median','minimum','reflect','symmetric','wrap']),
              help="Pad to use around the image, default : edge" 
                  "(see https://numpy.org/doc/stable/reference/generated/numpy.pad.html"
                  "for more information)")

band_opt = click.option('-b','--bands', type=int, multiple = True, help="List of bands to process")

all_opt = click.option('-a', '--all','all_bands', type=bool, is_flag=True, help="Process all bands")

@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def filter(ctx):
    """
    Apply a filter to a set of images.
    """
    ctx.ensure_object(dict)


def create_filter(filter_name : str):

    @filter.command(filter_name, context_settings=CONTEXT_SETTINGS)
    @inpt_arg
    @ker_opt
    @out_opt
    @win_opt
    @pad_opt
    @band_opt
    @all_opt
    @click.pass_context
    def filter_filtername(ctx, inputs : list, output : str, window_size : int, pad : str, kernel_size : int, bands : list, all_bands : bool):
        """
        Execute the requested filter on the input files with the specified parameters.
        The `inputs` argument can either be a single file or a `.lst` file containing a list of input files.

        Arguments:

        inputs TEXT

        Input file to process (e.g. Sentinel2 L2A MAJA from THEIA).
        You can provide a single file with extension \".lst\" (e.g. \"filtering.lst\") that lists
        the input files to process (one input file per line in .lst).
        """

        print(bands)
        # Configure the filter tool instance
        tool = create_filtering(
            output=output,
            window_size=window_size,
            pad=pad,
            argsdict={"inputs": inputs},
            filter=filter_name,
            bands=bands,
            kernel_size=kernel_size,
            all_bands=all_bands)

        apply_process(ctx, tool, inputs)


median = create_filter("median")
mean = create_filter("mean")
sum = create_filter("sum")
adaptive_gaussian = create_filter("adaptive_gaussian")

@filter.result_callback()
@click.pass_context
def handle_result(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()






