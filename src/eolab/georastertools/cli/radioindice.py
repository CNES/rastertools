#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the radioindice tool
"""
import logging

from eolab.georastertools import RastertoolConfigurationException, Radioindice
from eolab.georastertools.cli.utils_cli import apply_process, win_opt
from eolab.georastertools.product import BandChannel
from eolab.georastertools.processing import RadioindiceProcessing
import sys
import click
import os

_logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def indices_opt(function):
    """
    Create options for all the possible indices
    """
    dict_indices = {'--ndvi' : "ndvi", '--tndvi' : "tndvi", '--rvi' : "rvi", '--pvi' : "pvi", '--savi' : "savi", '--tsavi' : "tsavi",
                    '--msavi' : "msavi", '--msavi2' : "msavi2", '--ipvi' : "ipvi",
                    '--evi' : "evi", '--ndwi' : "ndwi", '--ndwi2' : "ndwi2", '--mndwi' : "mndwi",
                    '--ndpi' : "ndpi", '--ndti' : "ndti", '--ndbi' : "ndbi", '--ri' : "ri", '--bi' : "bi", '--bi2' : "bi2"}

    for idc in dict_indices.keys():
        function = click.option(idc, is_flag=True, help=f"Compute " + dict_indices[idc] + " indice")(function)
    return function


#Radioindice command
@click.command("radioindice",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.option('-m', '--merge', is_flag =  True, help="Merge all indices in the same image (i.e. one band per indice)")

@click.option('-r', '--roi', type= str, help="Region of interest in the input image (vector)")

@win_opt

@click.option('-i', '--indices', type=str, multiple = True,
                    help=" List of indices to compute. Possible indices are: bi, bi2, evi, ipvi, mndwi, msavi, msavi2, ndbi, ndpi,"
                        " ndti, ndvi, ndwi, ndwi2, pvi, ri, rvi, savi, tndvi, tsavi")


@indices_opt

@click.option('-nd', '--normalized_difference','nd',type=str,
    multiple=True, nargs=2, metavar="band1 band2",
              help="Compute the normalized difference of two bands defined"
                        " as parameter of this option, e.g. \"-nd red nir\" will compute (red-nir)/(red+nir). "
                        "See eolab.georastertools.product.rastertype.BandChannel for the list of bands names. "
                        "Several nd options can be set to compute several normalized differences.")


@click.pass_context
def radioindice(ctx, inputs : list, output : str, indices : list, merge : bool, roi : str, window_size : int, nd : str, **kwargs) :
    """
    Compute the requested radio indices on raster data.

    This command computes various vegetation and environmental indices on satellite or raster data based on the
    provided input images and options. The tool can compute specific indices, merge the results into one image,
    compute normalized differences between bands, and apply processing using a region of interest (ROI) and specified
    tile/window size.

    Arguments:

        inputs TEXT

        Input file to process (e.g. Sentinel2 L2A MAJA from THEIA).
    You can provide a single file with extension \".lst\" (e.g. \"radioindice.lst\") that lists
    the input files to process (one input file per line in .lst).
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
                _logger.exception(RastertoolConfigurationException(f"Invalid indice name: {ind}"))
                sys.exit(2)

    if nd:
        for nd_bands in nd:
            if nd_bands[0] in BandChannel.__members__ and nd_bands[1] in BandChannel.__members__:
                channel1 = BandChannel[nd_bands[0]]
                channel2 = BandChannel[nd_bands[1]]
                new_indice = RadioindiceProcessing(f"nd[{nd_bands[0]}-{nd_bands[1]}]").with_channels(
                    [channel2, channel1])
                indices_to_compute.append(new_indice)
            else:
                _logger.exception(RastertoolConfigurationException(f"Invalid band(s) in normalized difference: {nd_bands[0]} and/or {nd_bands[1]}"))
                sys.exit(2)

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


