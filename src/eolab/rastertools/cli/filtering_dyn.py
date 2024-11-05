#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the filtering tool
"""
from eolab.rastertools import Filtering
from eolab.rastertools.main import get_logger
from eolab.rastertools import RastertoolConfigurationException
#from eolab.rastertools.main import rastertools #Import the click group named rastertools
import sys
import click
import os

_logger = get_logger()

def _extract_files_from_list(cmd_inputs):
    """Extract the list of files from a file of type ".lst" which
    contains one line per file

    Args:
        cmd_inputs (str):
            Value of the inputs arguments of the command line. Either
            a file with a suffix lst from which the list of files shall
            be extracted or directly the list of files (in this case, the
            list is returned without any change).

    Returns:
        The list of input files read from the command line
    """

    # handle the input file of type "lst"
    if len(cmd_inputs) == 1 and cmd_inputs[0][-4:].lower() == ".lst":
        # parse the listing
        with open(cmd_inputs[0]) as f:
            inputs = f.read().splitlines()
    else:
        inputs = cmd_inputs

    return inputs

def create_filtering(output : str, window_size : int, pad : str, argsdict : dict, filter : str, bands : list, kernel_size : int, all_bands : bool) -> Filtering:
    """
    CHANGE DOCSTRING
    Create and configure a new rastertool "Filtering" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Filtering`: The configured rastertool to run
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


def apply_filter(ctx, tool : Filtering, inputs : str):
    """
    CHANGE DOCSTRING
    Apply the chosen filter
    """
    try:
        # handle the input file of type "lst"
        inputs_extracted = _extract_files_from_list(inputs)

        # setup debug mode in which intermediate VRT files are stored to disk or not
        tool.with_vrt_stored(ctx.obj.get('keep_vrt'))

        # launch process
        tool.process_files(inputs_extracted)

        _logger.info("Done!")

    except RastertoolConfigurationException as rce:
        _logger.exception(rce)
        sys.exit(2)

    except Exception as err:
        _logger.exception(err)
        sys.exit(1)

    sys.exit(0)


inpt_arg = click.argument('inputs', type=str, help="Input file to process (e.g. Sentinel2 L2A MAJA from THEIA). "
                 "You can provide a single file with extension \".lst\" (e.g. \"filtering.lst\") "
                 "that lists the input files to process (one input file per line in .lst)")

ker_opt = click.option('--kernel-size', type=int, help="Kernel size of the filter function, e.g. 3 means a square" 
                   "of 3x3 pixels on which the filter function is computed"
                   "(default: 8)")

out_opt = click.option('-o', '--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

win_opt = click.option('-ws', '--window-size', type=int, default = 1024, help="Size of tiles to distribute processing, default: 1024")

pad_opt = click.option('-p','--pad',default="edge", type=click.Choice(['none','edge','maximum','mean','median','minimum','reflect','symmetric','wrap']),
              help="Pad to use around the image, default : edge" 
                  "(see https://numpy.org/doc/stable/reference/generated/numpy.pad.html"
                  "for more information)")

band_opt = click.option('-b','--bands', type=list, help="List of bands to process")

all_opt = click.option('-a', '--all','all_bands', type=bool, is_flag=True, help="Process all bands")

@click.group()
@click.pass_context
def filter(ctx):
    '''
    Apply a filter to a set of images.
    '''
    ctx.ensure_object(dict)


def create_filter(filter_name : str):

    @filter.command(filter_name)
    @inpt_arg
    @ker_opt
    @out_opt
    @win_opt
    @pad_opt
    @band_opt
    @all_opt
    @click.pass_context
    def filter_filtername(ctx, inputs : str, output : str, window_size : int, pad : str, kernel_size : int, bands : list, all_bands : bool):
        '''
        COMPLETE THE SECTION should display for : rastertools filter median --help
        Execute the filtering tool with the specified filter and parameters. name=rasterfilter.name, help=rasterfilter.help

        do not remove :
        inputs : Input file to process (e.g. Sentinel2 L2A MAJA from THEIA).
             You can provide a single file with extension \".lst\" (e.g. \"filtering.lst\")
             that lists the input files to process (one input file per line in .lst)"
        '''
        ctx.obj["inputs"] = inputs

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

        apply_filter(ctx, tool, inputs)


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






