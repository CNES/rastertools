#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the filtering tool
"""
from eolab.georastertools import Filtering
from eolab.georastertools.cli.utils_cli import apply_process, pad_opt, win_opt, all_opt, band_opt
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

        pad (str): Padding method used for windowing (default : 'edge').

        argsdict (dict): Dictionary of additional filter configuration arguments.

        filter (str): The filter type to apply (must be a valid name in `Filtering` filters).

        bands (list): List of bands to process. If empty and `all_bands` is False, defaults to [1].

        kernel_size (int): Size of the kernel used by the filter.

        all_bands (bool): Whether to apply the filter to all bands (True) or specific bands (False).

    Returns:
        :obj:`eolab.georastertools.Filtering`: A configured `Filtering` instance ready for execution.
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


def filter_options(options : list):
    def wrapper(function):
        for option in options:
            function = option(function)
        return function
    return wrapper


inpt_arg = click.argument('inputs', type=str, nargs = -1, required = 1)

ker_opt = click.option('--kernel_size', type=int, help="Kernel size of the filter function, e.g. 3 means a square" 
                   " of 3x3 pixels on which the filter function is computed"
                   " (default: 8)")

out_opt = click.option('-o', '--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

sigma = click.option('--sigma', type=int, required = True, help="Standard deviation of the Gaussian distribution")

@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def filter(ctx):
    """
    Apply a filter to a set of images.
    """
    ctx.ensure_object(dict)


def create_filter(filter_name : str):

    list_opt = [inpt_arg, ker_opt, out_opt, win_opt, pad_opt, band_opt, all_opt]
    if filter_name == 'adaptive_gaussian':
        list_opt.append(sigma)

    @filter.command(filter_name, context_settings=CONTEXT_SETTINGS)
    @filter_options(list_opt)
    @click.pass_context
    def filter_filtername(ctx, inputs : list, output : str, window_size : int, pad : str, kernel_size : int, bands : list, all_bands : bool, **kwargs):
        """
        Execute the requested filter on the input files with the specified parameters.
        The `inputs` argument can either be a single file or a `.lst` file containing a list of input files.

        Arguments:

            inputs TEXT

            Input file to process (e.g. Sentinel2 L2A MAJA from THEIA).
        You can provide a single file with extension \".lst\" (e.g. \"filtering.lst\") that lists
        the input files to process (one input file per line in .lst).
        """
        argsdict = {"inputs": inputs}

        if filter_name == 'adaptive_gaussian':
            argsdict = {"sigma" : kwargs["sigma"]}

        # Configure the filter tool instance
        tool = create_filtering(
            output=output,
            window_size=window_size,
            pad=pad,
            argsdict=argsdict,
            filter=filter_name,
            bands=bands,
            kernel_size=kernel_size,
            all_bands=all_bands)

        apply_process(ctx, tool, inputs)


median = create_filter("median")
mean = create_filter("mean")
sum = create_filter("sum")
adaptive_gaussian = create_filter("adaptive_gaussian")