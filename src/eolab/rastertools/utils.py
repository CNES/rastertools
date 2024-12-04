#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines several utility methods for:

- handling path
- transforming data
- computing sliding windows
- ...
"""
import math
import tempfile
from pathlib import Path

import rasterio
from osgeo import gdal


def vsimem_to_rasterio(vsimem_file:str, nodata=None) -> rasterio.io.DatasetReader:
    """
    Converts a VSIMEM (in-memory) raster dataset to a Rasterio dataset with optional nodata masking.

    This function opens a raster dataset stored in VSIMEM (virtual file system in memory)
    using GDAL, extracts its metadata and data, handles optional nodata values and masks,
    and saves it to a temporary GeoTIFF file. It then reopens the file with Rasterio and
    returns a Rasterio dataset reader.

    Parameters
    ----------
    vsimem_file : str
        The path to the VSIMEM file to be converted. This file should be an in-memory GDAL dataset.

    nodata : float, optional
        A user-defined nodata value to override the nodata value in the GDAL dataset.
        If not provided, the nodata value from the GDAL dataset is used (if available).

    Returns
    -------
    rasterio.io.DatasetReader
        A Rasterio dataset reader object corresponding to the temporary GeoTIFF created from the VSIMEM file.

    Notes
    -----
    - The function assumes the dataset is in a format that is compatible with both GDAL and Rasterio.
    - The created temporary file is not deleted automatically. It can be removed manually after use.
    - The function reads all raster bands from the dataset, applies the optional nodata masking,
      and writes the data to a new GeoTIFF file.
    - If a nodata value is provided, the function will apply the mask based on that value to each band.
      If no nodata value is set, no mask is applied.
    """
    gdal_ds = gdal.Open(vsimem_file)
    cols = gdal_ds.RasterXSize
    rows = gdal_ds.RasterYSize
    bands = gdal_ds.RasterCount
    geo_transform = gdal_ds.GetGeoTransform()
    projection = gdal_ds.GetProjection()

    gdal_dtype_to_numpy = {
        gdal.GDT_Byte: "uint8",
        gdal.GDT_UInt16: "uint16",
        gdal.GDT_Int16: "int16",
        gdal.GDT_UInt32: "uint32",
        gdal.GDT_Int32: "int32",
        gdal.GDT_Float32: "float32",
        gdal.GDT_Float64: "float64",
    }
    dtype = gdal_dtype_to_numpy[gdal_ds.GetRasterBand(1).DataType]

    data = [gdal_ds.GetRasterBand(i + 1).ReadAsArray() for i in range(bands)]

    masks = []
    for i in range(bands):
        band = gdal_ds.GetRasterBand(i + 1)
        band_nodata = band.GetNoDataValue()
        # Prioriser la valeur nodata de l'utilisateur
        nodata_value = nodata if nodata is not None else band_nodata
        if nodata_value is not None:
            masks.append(data[i] == nodata_value)
        else:
            masks.append(None)

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmpfile:
        temp_filename = tmpfile.name

    profile = {
        "driver": "GTiff",
        "height": rows,
        "width": cols,
        "count": bands,
        "dtype": dtype,
        "crs": projection,
        "transform": rasterio.transform.Affine.from_gdal(*geo_transform),
        "nodata": nodata_value,
    }

    with rasterio.open(temp_filename, "w", **profile) as dst:
        # Écrire les données
        for i, band_data in enumerate(data, start=1):
            dst.write(band_data, i)
            # Si un masque est défini, l'écrire
            if masks[i - 1] is not None:
                dst.write_mask((~masks[i - 1]).astype("uint8") * 255)

    return rasterio.open(temp_filename)


def to_tuple(val):
    """Convert val as a tuple of two val"""
    return val if type(val) == tuple else (val, val)


def highest_power_of_2(n):
    """Get the highest power of 2 that is less than n
    """
    p = int(math.log(n, 2))
    return int(pow(2, p))


def is_dir(file) -> bool:
    """Check if file is a dir or not
    """
    path = to_path(file)
    return path.is_dir()


def to_path(file, default=None) -> Path:
    """Transform a file name to a Path
    """
    path = None
    if file:
        path = Path(file) if isinstance(file, str) else file
    else:
        path = Path(default) if isinstance(default, str) else default
    return path


def get_basename(file) -> str:
    """Get the basename of a Path
    """
    path = to_path(file)
    suffix = ''.join(path.suffixes).lower()
    basename = path.name
    if len(suffix) > 0:
        basename = path.name[:-len(suffix)]
    return basename


def get_suffixes(file) -> str:
    """Get the suffixes of a filename as a concatenated string
    """
    return ''.join(to_path(file).suffixes).lower()


def get_metadata_name(band: int, prefix: str, metadata: str):
    """Get the metadata name for the statistics to generate"""
    name = None
    if prefix is None or prefix == "":
        name = f"b{str(band)}.{metadata}"
    else:
        name = f"{prefix}.{metadata}"
    return name


def slices_1d(window_width, shift, stop, start=0):
    """Yield 1 dimension sliding windows according to the given parameters

    Args:
        window_width: window width
        shift: shift to apply between two consecutive windows
        stop: max value
        start: min value (default 0)

    Returns:
        min, max (int, int): start and end index of the sliding windows.
    """
    nb_iter = math.ceil(1 + max(0, (stop - start - window_width) / shift))
    return ((start + i * shift, min(start + window_width + i * shift, stop))
            for i in range(nb_iter))


def slices_2d(window_size, shift, stop, start=0):
    """Yield 2 dimensions sliding windows according to the given parameters.

    Args:
        window_size: window width and height
        shift: shift to apply between two consecutive windows
        stop: max value
        start: min value (default 0)

    Returns: Firstly yield number of windows, then
             window y_min, y_max, x_min, x_max for each windoww
    """
    width, height = to_tuple(window_size)
    shift_c, shift_r = to_tuple(shift)
    start_c, start_r = to_tuple(start)
    stop_c, stop_r = to_tuple(stop)

    window_c = list(slices_1d(width, shift_c, stop_c, start_c))
    window_r = list(slices_1d(height, shift_r, stop_r, start_r))

    return ((r_min, r_max, c_min, c_max)
            for r_min, r_max in window_r
            for c_min, c_max in window_c)
