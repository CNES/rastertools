#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the SVF (Sky View Factor) tool
"""
from eolab.rastertools import SVF
from eolab.rastertools.cli.utils_cli import apply_process, pad_opt, win_opt
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


#SVF command
@click.command("svf",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('--radius', required = True, type=int, help="Maximum distance (in pixels) around a point to evaluate horizontal elevation angle")

@click.option('--directions',required = True, type=int, help="Number of directions on which to compute the horizon elevation angle")

@click.option('--resolution', required = True, type=float, help="Pixel resolution in meter")

@click.option('--altitude', type=int, help="Reference altitude to use for computing the SVF. If this option is not"
                    " specified, SVF is computed for every point at the altitude of the point")

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@win_opt
@pad_opt

@click.pass_context
def svf(ctx, inputs : list, radius : int, directions : int, resolution : float, altitude : int, output : str, window_size : int, pad : str) :
    """
    Compute the Sky View Factor (SVF) of a Digital Height Model (DHM).

    The Sky View Factor (SVF) is a measure of the visibility of the sky from a point in a Digital Height Model
    (DHM). It is calculated by evaluating the horizontal elevation angle from a given point in multiple
    directions (as specified by the user), and is influenced by the topography and surrounding terrain features.

    Arguments:

        inputs TEXT

        Input file to process (i.e. geotiff corresponding to a
    Digital Height Model). You can provide a single file
    with extension ".lst" (e.g. "svf.lst") that
    lists the input files to process (one input file per line in .lst)
    """
    # create the rastertool object
    tool = SVF(directions, radius, resolution)

    # set up config with args values
    tool.with_output(output)
    tool.with_windows(window_size, pad)
    if altitude is not None:
        tool.with_altitude(altitude)

    apply_process(ctx, tool, inputs)
