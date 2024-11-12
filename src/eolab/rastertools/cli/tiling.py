#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the tiling tool
"""
from eolab.rastertools import Tiling
from eolab.rastertools.cli.utils_cli import apply_process
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


#Speed command
@click.command("tiling",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('-g','--grid','grid_file',required = True, type=str,  help="vector-based spatial data file containing the grid to"
                        " use to generate the tiles")

@click.option('--id_col','id_column', type = str, help="Name of the column in the grid"
                " file used to number the tiles. When ids are defined, this argument is required"
                "to identify which column corresponds to the define ids")

@click.option('--id', type=int, multiple = True, help="Tiles ids of the grid to export as new tile, default all")

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.option('-n','--name','output_name', default="{}_tile{}", help="Basename for the output raster tiles, default:"
                        "\"{}_tile{}\". The basename must be defined as a formatted string where tile index is at position 1"
                        " and original filename is at position 0. For instance, tile{1}.tif will generate the filename"
                        "tile75.tif for the tile id = 75")

@click.option('-d','--dir','subdir_name', help="When each tile must be generated in a different"
                        "subdirectory, it defines the naming convention for the subdirectory. It is a formatted string with one positional"
                        "parameter corresponding to the tile index. For instance, tile{} will generate the subdirectory name tile75/"
                        "for the tile id = 75. By default, subdirectory is not defined and output files will be generated directly in"
                        "the output directory")
@click.pass_context
def tiling(ctx, inputs : list, grid_file : str, id_column : str, id : list, output : str, output_name : str, subdir_name : str) :
    """
    CHANGE DOCSTRING

    ADD INPUTS
    Create and configure a new rastertool "Tiling" according to argparse args

    Generate tiles of an input raster image following the geometries defined by a
    given grid


    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Tiling`: The configured rastertool to run
    """
    if id == () :
        id = None
    else:
        id = list(id)

    # create the rastertool object
    tool = Tiling(grid_file)

    # set up config with args values
    tool.with_output(output, output_name, subdir_name)
    tool.with_id_column(id_column, id)

    apply_process(ctx, tool, inputs)


