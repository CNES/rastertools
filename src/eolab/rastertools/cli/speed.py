#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the speed tool
"""
from eolab.rastertools import Speed
from eolab.rastertools.cli.utils_cli import apply_process
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


#Speed command
@click.command("speed",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('-b','--bands', type=int, multiple = True, help="List of bands to process")

@click.option('-a', '--all','all_bands', type=bool, is_flag=True, help="Process all bands")

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.pass_context
def speed(ctx, inputs : list, bands : list, all_bands : bool, output : str) :
    """
    CHANGE DOCSTRING
    Create and configure a new rastertool "Speed" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Speed`: The configured rastertool to run
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
