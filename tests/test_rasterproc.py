#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rasterio as rio

from eolab.rastertools.processing import RasterProcessing, compute_sliding

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"

from .utils4test import RastertoolsTestsData

__refdir = utils4test.get_refdir("test_rasterproc/")


def algo2D(bands):
    """
    Apply a scaling factor to each band independently.

    Parameters:
    bands (numpy.ndarray): A 2D array containing a single band of raster data.

    Returns:
    numpy.ndarray: An array with each element scaled by a factor of 2.
    """
    out = 2. * bands
    return out


def algo3D(bands):
    """
    Apply a scaling factor to all bands simultaneously.

    Parameters:
    bands (numpy.ndarray): A 3D array containing multiple bands of raster data.

    Returns:
    numpy.ndarray: An array with each element in all bands scaled by a factor of 2.
    """
    out = 2. * bands
    return out


def test_compute_sliding():
    """
    Test the compute_sliding function with 2D and 3D raster data.
    It verifies that the computed output matches the expected transformation.
    """
    # create output dir and clear its content if any
    utils4test.create_outdir()

    input_image = RastertoolsTestsData.tests_input_data_dir + "/" + "RGB_TIF_20170105_013442_test.tif"
    output_image = RastertoolsTestsData.tests_output_data_dir + "/" + "RGB_TIF_20170105_013442_test-out.tif"

    # Test 2D
    proc2D = RasterProcessing("Processing per band", algo=algo2D, per_band_algo=True)
    compute_sliding(input_image, output_image, proc2D, window_size=(2048, 2048), window_overlap=32)

    with rio.open(input_image) as orig, rio.open(output_image) as dest:
        data_orig = orig.read()
        data_transform = data_orig * 2.0
        data_dest = dest.read()
        assert (data_transform == data_dest).all()

    # Test 3D
    proc3D = RasterProcessing("Processing all bands", algo=algo3D)
    compute_sliding(input_image, output_image, proc3D, window_size=(128, 128), window_overlap=32)

    with rio.open(input_image) as orig, rio.open(output_image) as dest:
        data_orig = orig.read()
        data_transform = data_orig * 2.0
        data_dest = dest.read()
        assert (data_transform == data_dest).all()

    utils4test.clear_outdir()
