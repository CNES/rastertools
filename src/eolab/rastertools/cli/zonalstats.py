#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the zonalstats tool
"""
import eolab.rastertools.cli as cli
from eolab.rastertools import Zonalstats


def create_argparser(rastertools_parsers):
    """Adds the zonalstats subcommand to the given rastertools subparser

    Args:
        rastertools_parsers:
            The rastertools subparsers to which this subcommand shall be added.

            This argument provides from a code like this::

                import argparse
                main_parser = argparse.ArgumentParser()
                rastertools_parsers = main_parser.add_subparsers()
                zonalstats.create_argparser(rastertools_parsers)

    Returns:
        The rastertools subparsers updated with this subcommand
    """
    parser = rastertools_parsers.add_parser(
        "zonalstats", aliases=["zs"],
        help="Compute zonal statistics",
        description="Compute zonal statistics of a raster image.\n Available statistics are: "
                    "min max range mean std percentile_x (x in [0, 100]) median mad "
                    "count valid nodata sum majority minority unique",
        epilog="By default only first band is computed.")
    parser.add_argument(
        "inputs",
        nargs='+',
        help="Raster files to process. "
             "You can provide a single file with extension \".lst\" (e.g. \"zonalstats.lst\") "
             "that lists the input files to process (one input file per line in .lst)")
    cli.with_outputdir_arguments(parser)
    parser.add_argument(
        '-f',
        '--format',
        dest="output_format",
        help="Output format of the results when input geometries are provided (by default ESRI "
             f"Shapefile). Possible values are {', '.join(Zonalstats.supported_output_formats)}")
    parser.add_argument(
        '-g',
        '--geometry',
        dest="geometries",
        help="List of geometries where to compute statistics (vector like a shapefile or geojson)")
    parser.add_argument(
        '-w',
        '--within',
        dest="within",
        action="store_true",
        help="When activated, statistics are computed for the geometries that are within "
             "the raster shape. The default behaviour otherwise is to compute statistics "
             "for all geometries that intersect the raster shape.")
    parser.add_argument(
        '--stats',
        dest="stats",
        nargs="+",
        help="List of stats to compute. Possible stats are: "
             "min max range mean std percentile_x (x in [0, 100]) median mad "
             "count valid nodata sum majority minority unique")
    parser.add_argument(
        '--categorical',
        dest="categorical",
        action="store_true",
        help="If the input raster is categorical (i.e. raster values represent discrete classes) "
             "compute the counts of every unique pixel values.")
    parser.add_argument(
        '--valid_threshold',
        dest="valid_threshold",
        type=float,
        help="Minimum percentage of valid pixels in a shape to compute its statistics.")
    parser.add_argument(
        '--area',
        dest='area',
        action="store_true",
        help="Whether to multiply all stats by the area of a cell of the input raster."
    )
    parser.add_argument(
        '--prefix',
        dest="prefix",
        help="Add a prefix to the keys (default: None). One prefix per band (e.g. 'band1 band2')")

    cli.with_bands_arguments(parser)

    # argument group for the outliers image generation
    outliers_pc = parser.add_argument_group("Options to output the outliers")
    outliers_pc.add_argument(
        '--sigma',
        dest="sigma",
        help="Distance to the mean value (in sigma) in order to produce a raster "
             "that highlights outliers.")

    # argument group for generating stats charts
    chart_pc = parser.add_argument_group('Options to plot the generated stats')
    chart_pc.add_argument(
        '-c',
        '--chart',
        dest="chartfile",
        help="Generate a chart per stat and per geometry "
             "(x=timestamp of the input products / y=stat value) and "
             "store it in the file defined by this argument")
    chart_pc.add_argument(
        '-d',
        '--display',
        dest="display",
        action="store_true",
        help="Display the chart")
    chart_pc.add_argument(
        '-gi',
        '--geometry-index',
        dest="geom_index",
        default='ID',
        help="Name of the geometry index used for the chart (default='ID')")

    # argument group to generate stats per category
    group_pc = parser.add_argument_group('Options to compute stats per category in geometry. '
                                         'If activated, the generated geometries will contain '
                                         'stats for every categories present in the geometry')
    group_pc.add_argument(
        '--category_file',
        help="File (raster or geometries) containing discrete classes classifying the ROI."
    )
    group_pc.add_argument(
        '--category_index',
        help="Column name identifying categories in categroy_file "
             "(only if file format is geometries)",
        default="Classe"
    )
    group_pc.add_argument(
        '--category_names',
        help="JSON files containing a dict with classes index as keys and names "
             "to display classes as values.",
        default=""
    )

    # set the function to call when this subcommand is called
    parser.set_defaults(func=create_zonalstats)

    return rastertools_parsers


def create_zonalstats(args) -> Zonalstats:
    """Create and configure a new rastertool "Zonalstats" according to argparse args

    Args:
        args: args extracted from command line

    Returns:
        :obj:`eolab.rastertools.Zonalstats`: The configured rastertool to run
    """
    # get and check the list of stats to compute
    if args.stats:
        stats_to_compute = args.stats
    elif args.categorical:
        stats_to_compute = []
    else:
        stats_to_compute = ['count', 'min', 'max', 'mean', 'std']

    # get the bands to process
    if args.all_bands:
        bands = None
    else:
        bands = list(map(int, args.bands)) if args.bands else [1]

    # create the rastertool object
    tool = Zonalstats(stats_to_compute, args.categorical, args.valid_threshold,
                      args.area, args.prefix, bands)

    # set up config with args values
    tool.with_output(args.output, args.output_format) \
        .with_geometries(args.geometries, args.within) \
        .with_outliers(args.sigma) \
        .with_chart(args.chartfile, args.geom_index, args.display) \
        .with_per_category(args.category_file, args.category_index, args.category_names)

    return tool
