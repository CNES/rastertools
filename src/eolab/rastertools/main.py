#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains the rastertools command line interface. The command line
has several subcommands such as *radioindice* and *zonalstats*.

Usage examples::

  rastertools radioindice --help
  rastertools zonalstats --help

"""
import argparse
import logging
import logging.config
import os
import sys
import json

from eolab.rastertools import __version__
from eolab.rastertools import RastertoolConfigurationException
from eolab.rastertools.cli import radioindice, zonalstats, tiling, speed
from eolab.rastertools.cli import filtering, svf, hillshade, timeseries
from eolab.rastertools.product import RasterType


_logger = logging.getLogger(__name__)


def add_custom_rastertypes(rastertypes):
    """Add definition of new raster types. The json string shall have the following format:

    .. code-block:: json

      {
        "rastertypes": [
          {
            "name": "RGB_TIF",
            "product_pattern": "^RGB_TIF_(?P<date>[0-9_]*)\\.(tif|TIF)$",
            "bands": [
              {
                "channel": "red",
                "description": "red"
              },
              {
                "channel": "green",
                "description": "green"
              },
              {
                "channel": "blue",
                "description": "blue"
              },
              {
                "channel": "nir",
                "description": "nir"
              }
            ],
            "date_format": "%Y%m%d_%H%M%S",
            "nodata": 0
          },
          {
            "name": "RGB_TIF_ARCHIVE",
            "product_pattern": "^RGB_TIF_(?P<date>[0-9\\_]*).*$",
            "bands_pattern": "^TIF_(?P<bands>{}).*\\.(tif|TIF)$",
            "bands": [
              {
                "channel": "red",
                "identifier": "r",
                "description": "red"
              },
              {
                "channel": "green",
                "identifier": "g",
                "description": "green"
              },
              {
                "channel": "blue",
                "identifier": "b",
                "description": "blue"
              },
              {
                "channel": "nir",
                "identifier": "n",
                "description": "nir"
              }
            ],
            "date_format": "%Y%m%d_%H%M%S",
            "nodata": 0
          }
        ]
      }

    - name : unique name of raster type
    - product_pattern: regexp to identify raster product matching the raster type. Regexp can
      contain catching groups that identifies metadata: date (groupe name=date), relative
      orbit number (relorbit), tile number (tile), any other group (free name of the group).
    - bands_pattern (optional) : when the raster product of this type is an archive
      (zip, tar, tar.gz, etc.), the pattern enables to identify the files of the different
      raster bands. The raster product can contain one raster file per band or one multi-bands
      raster file. In the first case, the pattern must contain a group that identify
      the band to which the file corresponds. This group must be defined as follows (?P<bands>{})
      in which the variable part {} will be replaced by the identifier of the band (see below).
    - date_format (optional): date format in the product name. By default: %Y%m%d-%H%M%S
    - nodata (optional): no data value of raster bands. By default: -10000
    - masknnodata (optional): nodata value in the mask band
    - For every bands:

      * channel: channel of the band. Must be one of: blue, green, red, nir, mir, swir,
        red_edge1, red_edge2, red_edge3, red_edge4, blue_60m, nir_60m and mir_60m.
      * identifier (optional): string that identifies the band in the filenames of a raster
        product that it is an archive. This identifier is inserted in the group ``bands`` of
        the bands_pattern.
      * description (optional): band description that will be reused in the generated products.

    - For every masks:

      * identifier (optional): string that identifies the mask band in the filenames of a raster
        product that it is an archive. This identifier is inserted in the group ``bands`` of
        the bands_pattern.
      * description (optional): mask band description that will be reused in the generated products.
      * maskfunc (optional): fully qualified name of the python function that converts the mask
        band values to a binary mask (0 = masked; 1 = unmasked)

    Args:
        rastertypes: JSON string that contains the new raster types definition
    """
    RasterType.add(rastertypes)


def run_tool(args):
    """Main entry point allowing external calls

    sys.exit returns:

    - 0: everything runs fine
    - 1: processing errors occured
    - 2: wrong execution configuration

    Args:
        args ([str]): command line parameter list
    """
    parser = argparse.ArgumentParser(
        description="Collection of tools on raster data")
    # add an argument to define custom raster types
    parser.add_argument(
        '-t',
        '--rastertype',
        dest="rastertype",
        help="JSON file defining additional raster types of input files")
    parser.add_argument(
        '--version',
        action='version',
        version=f'rastertools {__version__}')
    parser.add_argument(
        '--max_workers',
        dest="max_workers",
        type=int,
        help="Maximum number of workers for parallel processing. If not given, it will default to "
             "the number of processors on the machine. When all processors are not allocated to "
             "run rastertools, it is thus recommended to set this option.")
    parser.add_argument(
        '--debug',
        dest="keep_vrt",
        action="store_true",
        help="Store to disk the intermediate VRT images that are generated when handling "
             "the input files which can be complex raster product composed of several band files.")
    parser.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO)
    parser.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG)

    rastertools_parsers = parser.add_subparsers(title='Commands')
    # add sub parser for filtering
    rastertools_parsers = filtering.create_argparser(rastertools_parsers)
    # add sub parser for hillshade
    rastertools_parsers = hillshade.create_argparser(rastertools_parsers)
    # add sub parser for radioindice
    rastertools_parsers = radioindice.create_argparser(rastertools_parsers)
    # add sub parser for speed
    rastertools_parsers = speed.create_argparser(rastertools_parsers)
    # add sub parser for svf
    rastertools_parsers = svf.create_argparser(rastertools_parsers)
    # add sub parser for tiling
    rastertools_parsers = tiling.create_argparser(rastertools_parsers)
    # add sub parser for timeseries
    rastertools_parsers = timeseries.create_argparser(rastertools_parsers)
    # add sub parser for zonalstats
    rastertools_parsers = zonalstats.create_argparser(rastertools_parsers)

    # analyse arguments
    args = parser.parse_args(args)
    argsdict = vars(args)

    # setup logging
    logformat = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
    logging.basicConfig(level=args.loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")

    if "RASTERTOOLS_NOTQDM" not in os.environ:
        os.environ["RASTERTOOLS_NOTQDM"] = "True" if logging.root.level > logging.INFO else "False"

    if "RASTERTOOLS_MAXWORKERS" not in os.environ and args.max_workers is not None:
        os.environ["RASTERTOOLS_MAXWORKERS"] = f"{args.max_workers}"

    # handle rastertype option
    if args.rastertype:
        with open(args.rastertype) as json_content:
            RasterType.add(json.load(json_content))

    # call function corresponding to the subcommand
    if "func" in argsdict:
        try:
            print("before tool = args.func(args)")
            # initialize the rastertool to execute
            # initialize the rastertool to execut
            tool = args.func(args)
            print("after tool = args.func(args)")

            # handle the input file of type "lst"
            inputs = _extract_files_from_list(args.inputs)

            # setup debug mode in which intermediate VRT files are stored to disk or not
            tool.with_vrt_stored(args.keep_vrt)

            print("before tool.process_files(inputs)")
            # launch process
            tool.process_files(inputs)
            print("after tool.process_files(inputs)")

            _logger.info("Done!")
        except RastertoolConfigurationException as rce:
            _logger.exception(rce)
            sys.exit(2)
        except Exception as err:
            _logger.exception(err)
            sys.exit(1)
    else:
        parser.print_help()

    sys.exit(0)


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


def run():
    """Entry point for console_scripts
    """
    run_tool(sys.argv[1:])


if __name__ == "__main__":
    run()
