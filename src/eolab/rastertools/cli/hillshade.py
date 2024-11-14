#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the hillshade tool
"""
from eolab.rastertools import Hillshade
from eolab.rastertools.cli.utils_cli import apply_process
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


#Hillshade command
@click.command("hillshade",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('--elevation', type=float, required = True, help="Elevation of the sun in degrees, [0°, 90°] where"
                        " 90°=zenith and 0°=horizon")

@click.option('--azimuth', type=float, required = True, help="Azimuth of the sun in degrees, [0°, 360°] where"
                        " 0°=north, 90°=east, 180°=south and 270°=west")

@click.option('--radius', type=int, help="Maximum distance (in pixels) around a point to evaluate"
                        " horizontal elevation angle. If not set, it is automatically computed from"
                        " the range of altitudes in the digital model.")

@click.option('--resolution', required = True, type=float, help="Pixel resolution in meter")

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.option('-ws', '--window_size', type=int, default = 1024, help="Size of tiles to distribute processing, default: 1024")

@click.option('-p', '--pad',default="edge", type=click.Choice(['none','edge','maximum','mean','median','minimum','reflect','symmetric','wrap']),
              help="Pad to use around the image, default : edge" 
                  " (see https://numpy.org/doc/stable/reference/generated/numpy.pad.html"
                  " for more information)")

@click.pass_context
def hillshade(ctx, inputs : list, elevation : float, azimuth : float, radius : int, resolution : float, output : str, window_size : int, pad : str) :
    """
    Execute the hillshade subcommand on a Digital Height Model (DHM) using the given solar
    parameters (elevation, azimuth), resolution, and optional parameters for processing the raster.

    Arguments:

        inputs TEXT

        Input file to process (i.e. geotiff corresponding to a
    Digital Height Model). You can provide a single file
    with extension ".lst" (e.g. "hillshade.lst") that
    lists the input files to process (one input file per line in .lst)
    """
    # create the rastertool object
    tool = Hillshade(elevation, azimuth, resolution, radius)

    # set up config with args values
    tool.with_output(output)
    tool.with_windows(window_size, pad)

    apply_process(ctx, tool, inputs)



