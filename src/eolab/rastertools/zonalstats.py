#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named zonalstats that compute several statistics
(mean, median, std dev, etc) on one or several bands of a raster image. The statistics
can be computed on the whole image or by zones defined by a vector file (e.g. shapefile,
geojson).

Several options are provided:

* compute outliers: enable to generate an image that emphasizes the outliers pixels
  (i.e. pixels with values greater that mean + n x stddev where n can be parametrized).
* generate a chart: if several raster images are computed and if we can extract a date from the
  filenames (because the raster is of a known type), generate one chart
  per statistics (x=time, y=stats)

"""
from typing import List, Dict
import datetime
import logging.config
from pathlib import Path
import json
import numpy as np
import geopandas as gpd
import sys

import rasterio

from eolab.rastertools import utils
from eolab.rastertools import Rastertool, RastertoolConfigurationException
from eolab.rastertools.processing import compute_zonal_stats, compute_zonal_stats_per_category
from eolab.rastertools.processing import extract_zonal_outliers, plot_stats
from eolab.rastertools.processing import vector
from eolab.rastertools.product import RasterProduct

_logger = logging.getLogger(__name__)


class Zonalstats(Rastertool):
    """
    Raster tool that computes zonal statistics of a raster product.
    """

    supported_output_formats = {
        'ESRI Shapefile': 'shp',
        'GeoJSON': 'geojson',
        'CSV': 'csv',
        'GPKG': 'gpkg',
        'GML': 'gml'
    }
    """List of all possible output format are provided by fiona.supported_drivers.keys()"""

    valid_stats = ['count', 'valid', 'nodata',
                   'min', 'max', 'mean', 'std', 'sum', 'median', "mad", 'range',
                   'majority', 'minority', 'unique']
    """List of stats that can be computed. In addition to this list, "percentile_xx" is
    also a valid stat where xx is the percentile value, e.g. percentile_70"""

    def __init__(self, stats: List[str], categorical: bool = False, valid_threshold: float = 0.0,
                 area: bool = False, prefix: str = None, bands: List[int] = [1]):
        """ Constructor

        Args:
            stats ([str]):
                List of stats to compute. Zonalstats.valid_stats defined the list of valid stats
                except percentile which can be defined as string concatenating percentile\\_ with
                the percentile value (from 0 to 100).
            categorical (bool, optional, default=False):
                If true and input raster is "categorical", add the counts of every unique
                raster values to the stats
            valid_threshold (float, optional, default=0.0):
                Minimum percentage of valid pixels in a shape to compute its statistics ([0.0, 1.0])
            area (bool, optional, default=False):
                If true, statistics are multiplied by the pixel area of the raster input
            prefix (str, optional, default=None]):
                Add a prefix to the stats keys, one prefix per band. The argument is a string
                with all prefixes separated by a space.
            bands ([int], optional, default=[1]):
                List of bands in the input image to process.
                Set None if all bands shall be processed.
        """
        super().__init__()

        self._stats = stats
        self._categorical = categorical
        value = valid_threshold or 0.0
        if value < 0.0 or value > 1.0:
            raise RastertoolConfigurationException(
                f"Valid threshold must be in range [0.0, 1.0].")
        if value > 1e-5 and "valid" not in stats:
            raise RastertoolConfigurationException(
                "Cannot apply a valid threshold when the computation "
                "of the valid stat has not been requested.")
        self._valid_threshold = value
        self._area = area
        self._prefix = prefix.split() if prefix else None
        self.__check_stats()

        self._bands = bands

        self._output_format = "ESRI Shapefile"

        self._geometries = None
        self._within = False

        self._sigma = None

        self._chart_file = None
        self._geometry_index = 'ID'
        self._display_chart = False

        self._category_file = None
        self._category_file_type = None
        self._category_index = None
        self._category_labels = None

        self._generated_stats = list()
        self._generated_stats_dates = list()

    @property
    def generated_stats_per_date(self):
        """After processing one or several files, this method enables to retrieve a dictionary
        that contains the statistics for each inputfile's date:

        - keys are timestamps
        - values are the statistics at the corresponding timestamp

        Warning:
            When the timestamp of the input raster cannot be retrieved, the dictionary does not
            contain the generated statistics for this input raster. In this case, prefer calling
            generated_stats to get the stats as a list (one item per input file).
        """
        out = dict()
        if len(self._generated_stats_dates) > 0:
            out = {date: stats
                   for (date, stats) in zip(self.generated_stats_dates, self.generated_stats)}
        return out

    @property
    def generated_stats(self):
        """The list of generated stats in the same order as the input files"""
        return self._generated_stats

    @property
    def generated_stats_dates(self):
        """The list of dates when they can be extracted from the input files' names"""
        return self._generated_stats_dates

    @property
    def stats(self) -> List[str]:
        """List of stats to compute"""
        return self._stats

    @property
    def categorical(self) -> bool:
        """Whether to compute the counts of every unique pixel values"""
        return self._categorical

    @property
    def valid_threshold(self) -> float:
        """Minimum percentage of valid pixels in a shape to compute its statistics"""
        return self._valid_threshold

    @property
    def area(self) -> bool:
        """Whether to compute the statistics multiplied by the pixel area"""
        return self._area

    @property
    def prefix(self) -> str:
        """Prefix of the features stats (one per band)"""
        return self._prefix

    @property
    def bands(self) -> List[int]:
        """List of bands to process"""
        return self._bands

    @property
    def output_format(self) -> str:
        """Output format for the features stats"""
        return self._output_format

    @property
    def geometries(self) -> str:
        """The geometries where to compute zonal statistics"""
        return self._geometries

    @property
    def within(self) -> bool:
        """Whether to compute stats for geometries within the raster (if False, stats for
           all geometries intersecting the raster are computed)"""
        return self._within

    @property
    def sigma(self) -> float:
        """Number of sigmas for identifying outliers"""
        return self._sigma

    @property
    def chart_file(self) -> str:
        """Name of the chart file to generate"""
        return self._chart_file

    @property
    def geometry_index(self) -> str:
        """The column name identifying the name of the geometry"""
        return self._geometry_index

    @property
    def display_chart(self) -> bool:
        """Whether to display the chart"""
        return self._display_chart

    @property
    def category_file(self) -> str:
        """Filename containing the categories when computing stats per
           categories in the geometries"""
        return self._category_file

    @property
    def category_file_type(self) -> str:
        """Type of the category file, either 'raster' or 'vector'"""
        return self._category_file_type

    @property
    def category_index(self) -> str:
        """Column name identifying categories in categroy_file (only if file format
           is geometries)
        """
        return self._category_index

    @property
    def category_labels(self) -> str:
        """Dict with classes index as keys and names to display as values"""
        return self._category_labels

    def __check_stats(self):
        """Check that the requested stats are valid.

        Args:
            stats_to_compute ([str]):
                List of stats to compute
        """
        for x in self._stats:
            # check percentile format
            if x.startswith("percentile_"):
                q = float(x.replace("percentile_", ''))
                # percentile must be in range [0, 100]
                if q > 100.0:
                    raise RastertoolConfigurationException('percentiles must be <= 100')
                if q < 0.0:
                    raise RastertoolConfigurationException('percentiles must be >= 0')

            elif x not in Zonalstats.valid_stats:
                raise RastertoolConfigurationException(
                    f"Invalid stat {x}: must be "
                    f"percentile_xxx or one of {Zonalstats.valid_stats}")

    def with_output(self, outputdir: str = ".", output_format: str = "ESRI Shapefile"):
        """Set up the output.

        Args:
            outputdir (str, optional, default="."):
                Output dir where to store results. If none, results are not dumped to a file.
            output_format (str, optional, default="ESRI Shapefile"):
                Format of the output 'ESRI Shapefile', 'GeoJSON', 'CSV', 'GPKG', 'GML'
                (see supported_output_formats). If None, it is set to ESRI Shapefile

        Returns:
            :obj:`eolab.rastertools.Zonalstats`: the current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        super().with_output(outputdir)
        self._output_format = output_format or 'ESRI Shapefile'
        # check if output_format exists
        if self._output_format not in Zonalstats.supported_output_formats:
            _logger.exception(RastertoolConfigurationException(
                f"Unrecognized output format {output_format}. "
                f"Possible values are {', '.join(Zonalstats.supported_output_formats)}"))
            sys.exit(2)
        return self

    def with_geometries(self, geometries: str, within: bool = False):
        """Set up the geometries where to compute stats.

        Args:
            geometries (str):
                Name of the file containing the geometries where to compute zonal stats. If not set,
                stats are computed on the whole raster image
            within (bool, optional, default=False):
                Whether to compute stats only for geometries within the raster. If False,
                statistics are computed for geometries that intersect the raster shape.

        Returns:
            :obj:`eolab.rastertools.Zonalstats`: the current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        self._geometries = geometries
        self._within = within
        return self

    def with_outliers(self, sigma: float):
        """Set up the computation of outliers

        Args:
            sigma (float):
                Distance to the mean value to consider a pixel as an outlier (expressed
                in sigma, e.g. the value 2 means that pixels values greater than
                mean value + 2 * std are outliers)

        Returns:
            :obj:`eolab.rastertools.Zonalstats`: the current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        # Manage sigma computation option that requires mean + std dev computation
        if "mean" not in self._stats:
            self._stats.append("mean")
        if "std" not in self._stats:
            self._stats.append("std")
        self._sigma = sigma
        return self

    def with_chart(self, chart_file: str = None, geometry_index: str = 'ID', display: bool = False):
        """Set up the charting capability

        Args:
            chart_file (str, optional, default=None):
                If not None, generate a chart with the statistics and saves it to str
            geometry_index (str, optional, default='ID'):
                Name of the index in the geometry file
            display (bool, optional, default=False):
                If true, display the chart with the statistics

        Returns:
            :obj:`eolab.rastertools.Zonalstats`: the current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        self._chart_file = chart_file
        self._geometry_index = geometry_index
        self._display_chart = display
        return self

    def with_per_category(self, category_file: str, category_index: str = 'Classe',
                          category_labels_json: str = None):
        """Set up the zonal stats computation per categories

        Args:
            category_file (str):
                Name of the file containing the categories
            category_index (str, optional, default='Classe'):
                Name of column containing the category value (if category_file is a vector)
            category_labels_json (str, optional, default=None):
                Name of json file containing the dict that associates category values
                to category names

        Returns:
            :obj:`eolab.rastertools.Zonalstats`: the current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        self._category_file = category_file
        self._category_index = category_index
        # get the category file type
        if category_file:
            suffix = utils.get_suffixes(category_file)
            if suffix[1:] in Zonalstats.supported_output_formats.values():
                self._category_file_type = "vector"
            else:
                # not a vector, maybe a raster? try to open it with rasterio
                try:
                    rasterio.open(category_file)
                except IOError:
                    raise RastertoolConfigurationException(
                        f"File {category_file} cannot be read: check format and existence")
                self._category_file_type = "raster"
        # get the dict of category labels
        if category_labels_json:
            try:
                with open(category_labels_json) as f:
                    self._category_labels = json.load(f)
            except Exception as err:
                raise RastertoolConfigurationException(
                    f"File {category_labels_json} does not contain a valid dict.") from err

        return self

    def process_file(self, inputfile: str) -> List[str]:
        """Compute the stats for a single input file

        Args:
            inputfile (str):
                Input image to process

        Returns:
            [str]: List of generated statistical images (posix paths) that have been generated
        """
        _logger.info(f"Processing file {inputfile}")

        # STEP 1: Prepare the input image so that it can be processed
        _logger.info("Prepare the input for computation")
        with RasterProduct(inputfile, vrt_outputdir=self.vrt_dir) as product:

            if product.rastertype is None and self.chart_file:
                _logger.error("Unrecognized raster type of input file,"
                              " cannot extract date for plotting")

            # open raster to get metadata
            raster = product.get_raster()

            rst = rasterio.open(raster)
            bound = int(rst.count)
            indexes = rst.indexes
            descr = rst.descriptions

            geotransform = rst.get_transform()
            width = np.abs(geotransform[1])
            height = np.abs(geotransform[5])
            area_square_meter = width * height
            rst.close()

            date_str = product.get_date_string('%Y%m%d-%H%M%S')


            # check band index and handle all bands options (when bands is None)
            if self.bands is None or len(self.bands) == 0:
                bands = list(indexes)
            else:
                bands = self.bands
            if min(bands) < 1 or max(bands) > bound:
                raise ValueError(f"Invalid bands, all values are not in range [1, {bound}]")

            # check the prefix
            if self.prefix and len(self.prefix) != len(bands):
                raise ValueError("Number of prefix does not equal the number of bands.")

            # STEP 2: Prepare the geometries where to compute zonal stats
            if self.geometries:
                # reproject & filter input geometries to fit the raster extent
                geometries = vector.reproject(
                    vector.filter(self.geometries, raster, self.within), raster)
            else:
                # if no geometry is defined, get the geometry from raster shape
                geometries = vector.get_raster_shape(raster)

            # STEP 3: Compute the statistics
            geom_stats = self.compute_stats(raster, bands, geometries, descr, date_str, area_square_meter)

            self._generated_stats.append(geom_stats)
            if date_str:
                timestamp = datetime.datetime.strptime(date_str, '%Y%m%d-%H%M%S')
                self._generated_stats_dates.append(timestamp)

            # STEP 4: Generate outputs
            outputs = []
            if self.outputdir:
                outdir = Path(self.outputdir)
                ext = Zonalstats.supported_output_formats[self.output_format]
                outputname = f"{utils.get_basename(inputfile)}-stats.{ext}"
                outputfile = outdir.joinpath(outputname)
                geom_stats.to_file(outputfile.as_posix(), driver=self.output_format)
                outputs.append(outputfile.as_posix())

                # if sigma is not None, generate the outliers image
                if self.sigma:
                    _logger.info("Extract outliers")
                    outliersfile = outdir.joinpath(
                        f"{utils.get_basename(inputfile)}-stats-outliers.tif")
                    extract_zonal_outliers(geom_stats, raster, outliersfile.as_posix(),
                                           prefix=self.prefix or [""] * len(bands),
                                           bands=bands, sigma=self.sigma)
                    outputs.append(outliersfile.as_posix())

            return outputs

    def postprocess_files(self, inputfiles: List[str], outputfiles: List[str]) -> List[str]:
        """Generate the chart if requested after computing stats for each input file

        Args:
            inputfiles ([str]): Input images to process
            outputfiles ([str]): List of generated files after executing the
                rastertool on the input files

        Returns:
            [str]: A list containing the chart file if requested
        """
        additional_outputs = []
        if self.chart_file and len(self.generated_stats_per_date) > 0:
            _logger.info("Generating chart")
            plot_stats(self.chart_file, self.generated_stats_per_date,
                       self.stats, self.geometry_index, self.display_chart)
            additional_outputs.append(self.chart_file)

        return additional_outputs

    def compute_stats(self, raster: str, bands: List[int],
                      geometries: gpd.GeoDataFrame,
                      descr: List[str], date: str,
                      area_square_meter: int) -> List[List[Dict[str, float]]]:
        """Compute the statistics of the input data. [Minimum, Maximum, Mean, Standard deviation]

        Args:
            raster (str):
                Input image to process
            bands ([int]):
                List of bands in the input image to process. Empty list means all bands
            geometries (GeoDataFrame):
                Geometries where to add statistics (geometries must be in the same
                projection as the raster)
            descr ([str]):
                Band descriptions
            date (str):
                Timestamp of the input raster
            area_square_meter (int):
                Area represented by a pixel

        Returns:
        list[list[dict]]
        The dictionnary associates the name of the statistics to its value.
        """
        _logger.info("Compute statistics")
        # Compute zonal statistics
        if self.category_file is not None:
            # prepare the categories data
            if self.category_file_type == "vector":
                # clip categories to the raster bounds and reproject in the raster crs
                class_geom = vector.reproject(
                    vector.clip(self.category_file, raster),
                    raster)
            else:  # filetype is raster
                # vectorize the raster and reproject in the raster crs
                class_geom = vector.reproject(
                    vector.vectorize(self.category_file, raster, self.category_index),
                    raster)

            # compute the statistics per category
            statistics = compute_zonal_stats_per_category(
                geometries, raster,
                bands=bands,
                stats=self.stats,
                categories=class_geom,
                category_index=self.category_index)
        else:
            statistics = compute_zonal_stats(
                geometries, raster,
                bands=bands,
                stats=self.stats,
                categorical=self.categorical)


        # apply area
        if self.area:
            [d.update({key: area_square_meter * val})
             for s in statistics
             for d in s for key, val in d.items() if not np.isnan(val)]

        # convert statistics to GeoDataFrame
        geom_stats = self.__stats_to_geoms(statistics, geometries, bands, descr, date)
        return geom_stats

    def __stats_to_geoms(self, statistics_data: List[List[Dict[str, float]]],
                         geometries: gpd.GeoDataFrame,
                         bands: List[int], descr: List[str], date: str) -> gpd.GeoDataFrame:
        """Appends statistics to the geodataframe.

        Args:
            statistics_data:
                A list of list of dictionnaries. Dict associates the stat names and the stat values.
            geometries (GeoDataFrame):
                Geometries where to add statistics
            bands ([int]):
                List of bands in the input image to process. Empty list means all bands
            descr ([str]):
                Bands descriptions to add to global metadata
            date (str):
                Date of raster to add to global metadata

        Returns:
            GeoDataFrame: The updated geometries with statistics saved in metadata of
            the following form: b{band_number}.{metadata_name} where metadata_name is
            successively the band name, the date and the statistics names (min, mean, max, median, std)
        """
        prefix = self.prefix or [""] * len(bands)

        for i, band in enumerate(bands):
            # add general metadata to geometries
            if descr and descr[i]:
                geometries[utils.get_metadata_name(band, prefix[i], "name")] = descr[i]
            if date:
                geometries[utils.get_metadata_name(band, prefix[i], "date")] = date



            # get all statistics names since additional statistics coming from categorical
            # option may have been computed
            stats = self.stats.copy()
            categorical_stats = set()
            [categorical_stats.update(s[i].keys()) for s in statistics_data]

            if self.category_file is None:
                # remove stats from the categorical stats
                # and add the categorical stats to the stats
                # remark: this operation seems strange but it ensures that stats are
                # in the correct order
                categorical_stats -= set(stats)
                stats.extend(categorical_stats)
            else:
                # per_category mode do not compute overall stats.
                # So stats is not exended but replaced
                stats = categorical_stats

            for stat in stats:
                cond = self.valid_threshold < 1e-5 or stat == "valid"
                metadataname = utils.get_metadata_name(band, prefix[i], stat)
                geometries[metadataname] = [
                    s[i][stat]
                    if stat in s[i] and (cond or s[i]["valid"] > self.valid_threshold) else np.nan
                    for s in statistics_data
                ]

        return geometries
