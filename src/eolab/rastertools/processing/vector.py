#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utilities methods on vector images
"""
import math
from typing import Union
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rioxarray
import shapely.geometry
from osgeo import gdal
import rasterio
from pyproj import Transformer
from rasterio import features, warp, windows
from shapely.geometry import Polygon

from eolab.rastertools import utils


def _get_geoms(geoms: Union[gpd.GeoDataFrame, Path, str]) -> gpd.GeoDataFrame:
    """Internal method to extract the geometries as a GeoDataFrame"""
    if isinstance(geoms, str):
        geoms = gpd.read_file(geoms)
    elif isinstance(geoms, Path):
        geoms = gpd.read_file(geoms.as_posix())
    return geoms


def _get_geoms_crs(geoms: Union[gpd.GeoDataFrame, Path, str]) -> rasterio.crs.CRS:
    """Internal method to extract the CRS of the geometries"""
    from packaging.version import Version
    from pyproj.enums import WktVersion

    proj_crs = _get_geoms(geoms).crs
    if Version(rasterio.__gdal_version__) < Version("3.0.0"):
        proj_crs = rasterio.crs.CRS.from_wkt(proj_crs.to_wkt(WktVersion.WKT1_GDAL))
    else:
        proj_crs = rasterio.crs.CRS.from_wkt(proj_crs.to_wkt())
    return proj_crs


def filter(geoms: Union[gpd.GeoDataFrame, Path, str], raster: Union[Path, str],
           within: bool = False, output: Union[Path, str] = None,
           driver: str = 'GeoJSON') -> gpd.GeoDataFrame:
    """Filter the geometries to keep those which intersect the raster bounds

    Args:
        geoms (str or Path or :obj:`gpd.GeoDataFrame`):
            Filename of the vector data (if str) or GeoDataFrame
        raster (str or Path):
            Raster image
        within (bool, optional, default=False):
            If true, statistics are computed for geometries within the raster shape. Otherwise
            statistics are computed for geometries that intersect the raster shape.
        output (str or Path, optional, default=None):
            File where to save the filtered geoms
            If None, nothing written to disk (only in memory)
        driver (str, optional, default=GeoJSON):
            Driver to write the output

    Returns:
        :obj:`gpd.GeoDataFrame`: The geometries that intesect the raster
    """
    geometries = _get_geoms(geoms)
    geoms_crs = _get_geoms_crs(geometries)

    file = raster.as_posix() if isinstance(raster, Path) else raster
    with rasterio.open(file) as dataset:
        l, b, r, t = dataset.bounds
        px, py = ([l, l, r, r], [b, t, t, b])

        if (geoms_crs != dataset.crs):
            px, py = warp.transform(dataset.crs, geoms_crs, [l, l, r, r], [b, t, t, b])

        polygon = shapely.geometry.Polygon([(x, y) for x, y in zip(px, py)])
        if within:
            # convert geometries into GeoPandasBaseExtended to use the new cix property
            filtered_geoms = geometries[geometries.within(polygon)]
        else:
            filtered_geoms = geometries[geometries.intersects(polygon)]

        if output:
            outfile = output.as_posix() if isinstance(output, Path) else output
            filtered_geoms.to_file(outfile, driver=driver)

        return filtered_geoms


def clip(geoms: Union[gpd.GeoDataFrame, Path, str], raster: Union[Path, str],
         output: Union[Path, str] = None, driver: str = 'GeoJSON') -> gpd.GeoDataFrame:
    """Clip the geometries to the raster bounds.
    Clipping is supposed to be a little bit faster than intersect

    Args:
        geoms (str or Path or :obj:`gpd.GeoDataFrame`):
            Filename of the vector data (if str) or GeoDataFrame
        raster (str or Path):
            Raster image
        output (str or Path, optional, default=None):
            File where to save the clipped geoms
            If None, nothing written to disk (only in memory)
        driver (str, optional, default=GeoJSON):
            Driver to write the output

    Returns:
        :obj:`gpd.GeoDataFrame`: The clipped geometries
    """
    geometries = _get_geoms(geoms)
    geoms_crs = _get_geoms_crs(geometries)

    file = raster.as_posix() if isinstance(raster, Path) else raster

    # first filter the geometries that overlap the raster bounds in order to
    # avoid computing clipping many polygons
    filtered_geoms = filter(geometries, raster)

    # then clip the resulting geometries to the raster bounds
    with rasterio.open(file) as dataset:
        l, b, r, t = dataset.bounds
        px, py = ([l, l, r, r], [b, t, t, b])

        if (geoms_crs != dataset.crs):
            # reproject bounds in geoms crs
            px, py = warp.transform(dataset.crs, geoms_crs, [l, l, r, r], [b, t, t, b])

        # then clip the resulting geometries to the raster bounds
        polygon = shapely.geometry.Polygon([(x, y) for x, y in zip(px, py)])
        clipped_geoms = gpd.clip(filtered_geoms, polygon)

        if output:
            outfile = output.as_posix() if isinstance(output, Path) else output
            clipped_geoms.to_file(outfile, driver=driver)

    return clipped_geoms


# def reproject(geoms: Union[gpd.GeoDataFrame, Path, str], raster: Union[Path, str],output: Union[Path, str] = None,driver: str = "GeoJSON",) -> gpd.GeoDataFrame:
#     """
#     Reproject the geometries to match the CRS of the raster.
#
#     Args:
#         geoms (str, Path, or gpd.GeoDataFrame): Vector data (filename or GeoDataFrame).
#         raster (str or Path): Raster file.
#         output (str or Path, optional): File to save reprojected geometries.
#         driver (str, optional): File format for saving the output (default is "GeoJSON").
#
#     Returns:
#         gpd.GeoDataFrame: Reprojected geometries in raster CRS.
#     """
#     geometries = _get_geoms(geoms)
#     geoms_crs = _get_geoms_crs(geometries)
#
#     raster_path = raster.as_posix() if isinstance(raster, Path) else raster
#
#     # Open raster with rioxarray
#     with rioxarray.open_rasterio(raster_path) as dataset:
#         raster_crs = dataset.rio.crs
#
#         if geoms_crs != raster_crs:
#             reprojected_geoms = geometries.to_crs(raster_crs)
#         else:
#             reprojected_geoms = geometries
#
#         if output:
#             outfile = output.as_posix() if isinstance(output, Path) else output
#             reprojected_geoms.to_file(outfile, driver=driver)
#
#         return reprojected_geoms


def reproject(geoms: Union[gpd.GeoDataFrame, Path, str], raster: Union[Path, str],
                                       output: Union[Path, str] = None, driver: str = 'GeoJSON') -> gpd.GeoDataFrame:
    """
    Reproject the geometries to match the CRS of the raster.

    Args:
        geoms (str, Path, or gpd.GeoDataFrame): Vector data (filename or GeoDataFrame).
        raster (str or Path): Raster file.
        output (str or Path, optional): File to save reprojected geometries.
        driver (str, optional): File format for saving the output (default is "GeoJSON").

    Returns:
        gpd.GeoDataFrame: Reprojected geometries in raster CRS.
    """
    geometries = _get_geoms(geoms)
    geoms_crs = _get_geoms_crs(geometries)

    file = raster.as_posix() if isinstance(raster, Path) else raster
    with rasterio.open(file) as dataset:
        if (geoms_crs != dataset.crs):
            reprojected_geoms = geometries.to_crs(dataset.crs)
        else:
            reprojected_geoms = geometries

        if output:
            outfile = output.as_posix() if isinstance(output, Path) else output
            reprojected_geoms.to_file(outfile, driver=driver)

        return reprojected_geoms


def dissolve(geoms: Union[gpd.GeoDataFrame, Path, str],
             output: Union[Path, str] = None, driver: str = 'GeoJSON') -> gpd.GeoDataFrame:
    """Dissolves all geometries in one

    Args:
        geoms (str or Path or :obj:`gpd.GeoDataFrame`):
            Filename of the vector data (if str) or GeoDataFrame
        output (str or Path, optional, default=None):
            File where to save the dissolved geoms
            If None, nothing written to disk (only in memory)
        driver (str, optional, default=GeoJSON):
            Driver to write the output

    Returns:
        :obj:`gpd.GeoDataFrame`: The dissolved geometries
    """
    geometries = _get_geoms(geoms)

    geometries['COMMON'] = 0
    union = geometries.dissolve(by='COMMON', as_index=False)
    union = union.drop(columns='COMMON')

    if output:
        outfile = output.as_posix() if isinstance(output, Path) else output
        union.to_file(outfile, driver=driver)

    return union


def get_raster_shape(raster: Union[Path, str], output: Union[Path, str] = None,
                     driver: str = 'GeoJSON') -> gpd.GeoDataFrame:
    """Extract the raster extent (shape where raster values are not masked)

    Args:
        raster (str or Path):
            Raster image
        output (str or Path, optional, default=None):
            File where to save the shape geom
            If None, nothing written to disk (only in memory)
        driver (str, optional, default=GeoJSON):
            Driver to write the output

    Returns:
        :obj:`gpd.GeoDataFrame`: The geometries in the raster CRS
    """
    file = raster.as_posix() if isinstance(raster, Path) else raster
    src = rioxarray.open_rasterio(file, masked=True)

    # Initialize a list to store the geometries
    geoms = []

    # Loop through each band in the raster
    for band in range(1, src.shape[0] + 1):
        # Read the mask for the current band
        mask = src.isel(band=band - 1).notnull().astype("uint8")

        # Convert the mask to geometries using rasterio features
        features_gen = features.shapes(mask.values, mask=mask.values, transform=src.rio.transform())

        # Collect the geometries where the value is greater than 0
        for geom, val in features_gen:
            if val > 0:
                # Transform the geojson-like geometry to a Shapely geometry object
                geoms.append(shapely.geometry.shape(geom))

        # create geo data frame
        df = pd.DataFrame({'geometry': geoms})
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        # set crs
        gdf.crs = src.rio.crs
        # dissolve all shapes per band in one shape
        gdf['COMMON'] = 0
        raster_shape = gdf.dissolve(by='COMMON', as_index=False)
        raster_shape = raster_shape.drop(columns='COMMON')

        if output:
            outfile = output.as_posix() if isinstance(output, Path) else output
            raster_shape.to_file(outfile, driver=driver)
        return raster_shape


def rasterize(geoms: Union[gpd.GeoDataFrame, Path, str], raster: Union[Path, str],
              burn: str = "index", burn_type=rasterio.int32, nodata=-1,
              output: Union[Path, str] = None):
    """Rasterize geometries using the raster shape and CRS. Output is a GeoTiff where every pixels
    have the value of the "burn" attribute of geometries.

    Args:
        geoms (str or Path or :obj:`gpd.GeoDataFrame`):
            Filename of the vector data (if str) or GeoDataFrame
        raster (str or Path):
            Filename of the raster image
        burn (str, optional, default='index'):
            Attribute to burn in the raster. Default is the index of the geometry.
        burn_type (rasterio.dtypes, optional, default=rasterio.int32):
            Type of the attribute values to burn. Must be coherent with actual
            burned attribute.
        nodata (value compatible with burn_type, optional, default=-1):
            Value corresponding to nodata in the generated raster.
        output (str or Path, optional, default=None):
            Output file where to save the rasterized geometries.
            If None, nothing written to disk (only in memory)

    Returns:
        np.ndarray: The dataset containing the burned values
    """
    geometries = _get_geoms(geoms)

    file = raster.as_posix() if isinstance(raster, Path) else raster
    with rasterio.open(file) as src:
        shapes = ((geom, i)
                  for geom, i in zip(geometries.geometry,
                                     geometries.index if burn == "index" else geometries[burn]))
        burned = features.rasterize(shapes=shapes,
                                    fill=nodata,
                                    out_shape=src.shape,
                                    transform=src.transform,
                                    dtype=burn_type)

        if output:
            outfile = output.as_posix() if isinstance(output, Path) else output
            profile = src.profile
            profile.update(blockxsize=utils.highest_power_of_2(min(1024, src.width)),
                           blockysize=utils.highest_power_of_2(min(1024, src.height)),
                           tiled=True, dtype=burn_type,
                           driver='GTiff', count=1, nodata=nodata)
            with rasterio.open(outfile, 'w', **profile) as dst:
                dst.write(burned, 1)

        return burned



def crop(input_image: Union[Path, str], roi: Union[gpd.GeoDataFrame, Path, str],
         output_image: Union[Path, str]):
    """Crops an input image to the roi bounds.

    Args:
        input_image (pathlib.Path or str):
            Filename of the raster image to crop
        roi (str or Path or GeoDataFrame):
            Filename of the vector data (if str) or GeoDataFrame
        output_image (pathlib.Path or str):
            Filename of the generated raster image
    """
    ### FAIRE AVEC RIOXARRAY
    pinput = input_image.as_posix() if isinstance(input_image, Path) else input_image
    poutput = output_image.as_posix() if isinstance(output_image, Path) else output_image

    geometries = reproject(dissolve(roi), pinput)
    geom_bounds = geometries.total_bounds

    raster = rasterio.open(pinput)
    rst_bounds = raster.bounds
    bounds = (math.floor(max(rst_bounds[0], geom_bounds[0])),
              math.floor(max(rst_bounds[1], geom_bounds[1])),
              math.ceil(min(rst_bounds[2], geom_bounds[2])),
              math.ceil(min(rst_bounds[3], geom_bounds[3])))
    geotransform = raster.get_transform()
    width = np.abs(geotransform[1])
    height = np.abs(geotransform[5])

    ds = gdal.Warp(destNameOrDestDS=poutput,
                   srcDSOrSrcDSTab=pinput,
                   outputBounds=bounds, targetAlignedPixels=True,
                   cutlineDSName=roi,
                   cropToCutline=False,
                   xRes=width, yRes=height,
                   format="VRT")
    del ds
    raster.close()


def vectorize(category_raster: Union[Path, str], raster: Union[Path, str],
              category_column: str = "Classe") -> gpd.GeoDataFrame:
    """Vectorize a raster containing categorical data. Only data intersecting the raster bounds
    are vectorized.

    Args:
        category_raster (str or Path):
            Raster containing categories to vectorize data (if str)
        raster (str or Path):
            Raster image defining the zone of interest
        category_column (str, optional, default="Classe"):
            Name of the column containing the category in the resulting geodataframe

    Returns:
        :obj:`gpd.GeoDataFrame`: The geometries generated by the vectorization in the category crs
    """
    file = raster.as_posix() if isinstance(raster, Path) else raster

    with rasterio.open(file) as dataset:
        with rasterio.open(category_raster) as category_dataset:
            # get the raster bounds in the classif crs
            l, b, r, t = dataset.bounds
            if(category_dataset.crs != dataset.crs):
                # reproject bounds in classif crs
                l, b, r, t = warp.transform_bounds(dataset.crs, category_dataset.crs,
                                                   *dataset.bounds)

            # Compute window bounds for crop
            window = windows.from_bounds(l, b, r, t, category_dataset.transform)
            # After reading portion of file, rasterio looses georeferencing
            # Thus, we record the georef and update it to match the cropped portion
            transform_offset = category_dataset.window_transform(window)
            # Now, read and vectorize crop
            extract = category_dataset.read(1, window=window)
            new_shapes = rasterio.features.shapes(extract, transform=transform_offset)
            # Store this vectorization in a GeoDataFrame
            geo_df = gpd.GeoDataFrame.from_records(new_shapes,
                                                   columns=['geometry', category_column])
            geo_df['geometry'] = geo_df['geometry'].apply(lambda x: shapely.geometry.shape(x))
            geo_df[category_column] = geo_df[category_column].apply(lambda x: int(x))
            geo_df = geo_df.set_geometry("geometry")
            geo_df.crs = category_dataset.crs
            return geo_df


def filter_dissolve(geom: gpd.GeoDataFrame, cat_geom: gpd.GeoDataFrame,
                    id: str = 'Classe') -> gpd.GeoDataFrame:
    """Filter a classification to the extent of a geometry. Returns a list of multipolygons
    corresponding to each category. Categories are merged according to the id label if
    entry is a geodataframe

    Args:
        geom (:obj:`gpd.GeoDataFrame`): Geometry corresponding to ROI
        cat_geom (:obj:`gpd.GeoDataFrame`): Geometries with labels, corresponding
            to a classification
        id (str, optional, default="Classe"): Name of classes label in cat_geom

    Returns:
        :obj:`gpd.GeoDataFrame`: The filtered geometries
    """
    intersection = gpd.overlay(geom, cat_geom)
    result = intersection.dissolve(by=id, as_index=False)
    return result
