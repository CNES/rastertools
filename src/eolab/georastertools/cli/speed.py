#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the speed tool
"""
from eolab.georastertools import Speed
from eolab.georastertools.cli.utils_cli import apply_process, band_opt, all_opt
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


#Speed command
@click.command("speed",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@band_opt
@all_opt

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.pass_context
def speed(ctx, inputs : list, bands : list, all_bands : bool, output : str) :
    """
    Compute the speed of radiometric values for multiple raster images.

    This command calculates the speed of radiometric values for raster data,
    optionally processing specific bands or all bands from the input images.
    The results are saved to a specified output directory.

    Arguments:

        inputs TEXT

        Input file to process (e.g. Sentinel2 L2A MAJA from THEIA).
    You can provide a single file with extension \".lst\" (e.g. \"speed.lst\") that lists
    the input files to process (one input file per line in .lst).
    """

    # get the bands to process
    if all_bands:
        bands = None
    else:
        bands = list(map(int, bands)) if bands else [1]

    # create the rastertool object
    tool = Speed(bands)

    # set up config with args values
    tool.with_output(output)

    apply_process(ctx, tool, inputs)
