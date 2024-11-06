#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the SVF (Sky View Factor) tool
"""
from eolab.rastertools import SVF
from eolab.rastertools.cli.utils_cli import apply_process
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


#Speed command
@click.command("svf",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('--radius',required = True, type=int, default = 16, help="Maximum distance (in pixels) around a point to evaluate horizontal elevation angle")

@click.option('--directions',required = True, type=int, default = 12, help="Number of directions on which to compute the horizon elevation angle")

@click.option('--resolution',default=0.5, type=float, help="Pixel resolution in meter")

@click.option('--altitude', type=int, help="Reference altitude to use for computing the SVF. If this option is not"
                    " specified, SVF is computed for every point at the altitude of the point")

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.option('-ws', '--window_size', type=int, default = 1024, help="Size of tiles to distribute processing, default: 1024")

@click.option('-p', '--pad',default="edge", type=click.Choice(['none','edge','maximum','mean','median','minimum','reflect','symmetric','wrap']),
              help="Pad to use around the image, default : edge" 
                  "(see https://numpy.org/doc/stable/reference/generated/numpy.pad.html"
                  "for more information)")

@click.pass_context
def svf(ctx, inputs : list, radius : int, directions : int, resolution : float, altitude : int, output : str, window_size : int, pad : str) :
    """
    CHANGE DOCSTRING

    ADD INPUTS
    Create and configure a new rastertool "Speed" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Speed`: The configured rastertool to run
    """
    # create the rastertool object
    tool = SVF(directions, radius, resolution)

    # set up config with args values
    tool.with_output(output)
    tool.with_windows(window_size, pad)
    if altitude is not None:
        tool.with_altitude(altitude)

    apply_process(ctx, tool, inputs)
