#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the radioindice tool
"""
from eolab.rastertools import RastertoolConfigurationException, Radioindice
from eolab.rastertools.cli.utils_cli import apply_process
from eolab.rastertools.product import BandChannel
from eolab.rastertools.processing import RadioindiceProcessing
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def indices_opt(function):
    list_indices = ['--ndvi', '--tndvi', '--rvi', '--pvi', '--savi', '--tsavi', '--msavi', '--msavi2', '--ipvi',
                    '--evi', '--ndwi', '--ndwi2', '--mndwi', '--ndpi', '--ndti', '--ndbi', '--ri', '--bi', '--bi2']

    for idc in list_indices:
        function = click.option(idc, is_flag=True, help=f"Compute {id} indice")(function)
    return function


#Radioindice command
@click.command("radioindice",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.option('-m', '--merge', is_flag =  True, help="Merge all indices in the same image (i.e. one band per indice)")

@click.option('-r', '--roi', type= str, help="Region of interest in the input image (vector)")

@click.option('-ws', '--window_size', type=int, default = 1024, help="Size of tiles to distribute processing, default: 1024")

@click.option('-i', '--indices', type=click.Choice(['ndvi', 'tndvi', 'rvi', 'pvi', 'savi', 'tsavi', 'msavi', 'msavi2', 'ipvi',
                    'evi', 'ndwi', 'ndwi2', 'mndwi', 'ndpi', 'ndti', 'ndbi', 'ri', 'bi', 'bi2']), multiple = True,
                    help=" List of indices to computePossible indices are: bi, bi2, evi, ipvi, mndwi, msavi, msavi2, ndbi, ndpi,"
                        " ndti, ndvi, ndwi, ndwi2, pvi, ri, rvi, savi, tndvi, tsavi")


@indices_opt

@click.option('-nd', '--normalized_difference','nd',type=str,
    multiple=True, nargs=2, metavar="band1 band2",
              help="Compute the normalized difference of two bands defined"
                        "as parameter of this option, e.g. \"-nd red nir\" will compute (red-nir)/(red+nir). "
                        "See eolab.rastertools.product.rastertype.BandChannel for the list of bands names. "
                        "Several nd options can be set to compute several normalized differences.")


@click.pass_context
def radioindice(ctx, inputs : list, output : str, indices : list, merge : bool, roi : str, window_size : int, nd : bool, **kwargs) :
    """Create and configure a new rastertool "Radioindice" according to argparse args

        Args:
            args: args extracted from command line

        Returns:
            :obj:`eolab.rastertools.Radioindice`: The configured rastertool to run
    """
    indices_opt = [key for key, value in kwargs.items() if value]
    indices_to_compute = []

    # append indices defined with --<name_of_indice>
    indices_to_compute.extend([indice for indice in Radioindice.get_default_indices()
                               if indice.name in indices_opt])

    # append indices defined with --indices
    if indices:
        indices_dict = {indice.name: indice for indice in Radioindice.get_default_indices()}
        for ind in indices:
            if ind in indices_dict:
                indices_to_compute.append(indices_dict[ind])
            else:
                raise RastertoolConfigurationException(f"Invalid indice name: {ind}")

    if nd:
        for nd in nd:
            if nd[0] in BandChannel.__members__ and nd[1] in BandChannel.__members__:
                channel1 = BandChannel[nd[0]]
                channel2 = BandChannel[nd[1]]
                new_indice = RadioindiceProcessing(f"nd[{nd[0]}-{nd[1]}]").with_channels(
                    [channel2, channel1])
                indices_to_compute.append(new_indice)
            else:
                raise RastertoolConfigurationException(
                    f"Invalid band(s) in normalized difference: {nd[0]} and/or {nd[1]}")

    # handle special case: no indice setup
    if len(indices_to_compute) == 0:
        indices_to_compute.append(Radioindice.ndvi)
        indices_to_compute.append(Radioindice.ndwi)
        indices_to_compute.append(Radioindice.ndwi2)

    # create the rastertool object
    tool = Radioindice(indices_to_compute)

    # set up config with args values
    tool.with_output(output, merge)
    tool.with_roi(roi)
    tool.with_windows(window_size)

    apply_process(ctx, tool, inputs)


