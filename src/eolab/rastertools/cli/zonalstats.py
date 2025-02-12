#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI definition for the zonalstats tool
"""
from eolab.rastertools import Zonalstats
from eolab.rastertools.cli.utils_cli import apply_process, all_opt, band_opt
import click
import os

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


#Zonalstats command
@click.command("zonalstats",context_settings=CONTEXT_SETTINGS)
@click.argument('inputs', type=str, nargs = -1, required = 1)

@click.option('-o','--output', default = os.getcwd(), help="Output directory to store results (by default current directory)")

@click.option('-f', '--format', "output_format", type = str, help="Output format of the results when input geometries are provided (by default ESRI "
             "Shapefile). Possible values are ESRI Shapefile, GeoJSON, CSV, GPKG, GML")

@click.option('-g','--geometry',"geometries",type = str, help="List of geometries where to compute statistics (vector like a shapefile or geojson)")

@click.option('-w','--within',is_flag = True, help="When activated, statistics are computed for the geometries that are within "
             "the raster shape. The default behaviour otherwise is to compute statistics "
             "for all geometries that intersect the raster shape.")

@click.option('--stats', multiple = True,help="List of stats to compute. Possible stats are: "
             "min max range mean std percentile_x (x in [0, 100]) median mad count valid nodata sum majority minority unique")

@click.option('--categorical',is_flag = True,help="If the input raster is categorical (i.e. raster values represent discrete classes) "
             "compute the counts of every unique pixel values.")

@click.option('--valid_threshold',"valid_threshold",type=float,help="Minimum percentage of valid pixels in a shape to compute its statistics.")

@click.option('--area',is_flag=True,help="Whether to multiply all stats by the area of a cell of the input raster.")

@click.option('--prefix', default = None, help="Add a prefix to the keys (default: None). One prefix per band (e.g. 'band1 band2')")

@click.option('--sigma',help="Distance to the mean value (in sigma) in order to produce a raster that highlights outliers.")

@click.option('-c','--chart',"chartfile", help="Generate a chart per stat and per geometry (x=timestamp of the input products / y=stat value) and "
             "store it in the file defined by this argument")

@click.option('-d','--display',is_flag=True, help="Display the chart")

@click.option('-gi','--geometry-index', "geom_index",type = str,default='ID',help="Name of the geometry index used for the chart (default='ID')")

@click.option('--category_file',type = str, help="File (raster or geometries) containing discrete classes classifying the ROI.")

@click.option('--category_index',type = str, default="Classe",help="Column name identifying categories in categroy_file (only if file format is geometries)")

@click.option('--category_names',type = str, default="", help="JSON files containing a dict with classes index as keys and names to display classes as values.")

@band_opt
@all_opt
@click.pass_context
def zonalstats(ctx, inputs : list, output : str, output_format : str, geometries : str, within : str, stats : list, categorical : bool, valid_threshold : float ,area : bool, prefix, bands : list, all_bands : bool, sigma, chartfile, display : bool, geom_index : str, category_file : str, category_index : str, category_names : str) :
    """
    Compute zonal statistics of a raster image.

    Available statistics are:
    min, max, range, mean, std, percentile_x (x in [0, 100]), median, mad, count, valid, nodata, sum, majority, minority, unique.

    By default, only the first band is computed unless specified otherwise.

    Arguments:

        inputs TEXT

        Raster files to process. You can provide a single filewith extension ".lst" (e.g. "zonalstats.lst") that
    lists the input files to process (one input file per line in .lst)
    """
    # get and check the list of stats to compute
    if stats:
        stats_to_compute = list(stats)
    elif categorical:
        stats_to_compute = []
    else:
        stats_to_compute = ['count', 'min', 'max', 'mean', 'std']

    # get the bands to process
    if all_bands:
        bands = None
    else:
        bands = list(map(int, bands)) if bands else [1]

    # create the rastertool object
    tool = Zonalstats(stats_to_compute, categorical, valid_threshold,
                      area, prefix, bands)

    # set up config with args values
    tool.with_output(output, output_format) \
        .with_geometries(geometries, within) \
        .with_outliers(sigma) \
        .with_chart(chartfile, geom_index, display) \
        .with_per_category(category_file, category_index, category_names)

    apply_process(ctx, tool, inputs)
