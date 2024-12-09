#!/usr/bin/env python
# -*- coding: utf-8 -*-

import geopandas as gpd
from pathlib import Path

from eolab.georastertools.processing import vector

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"

from .utils4test import RastertoolsTestsData

__refdir = utils4test.get_refdir("test_vector/")


def test_reproject_filter(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    reproj_geoms = vector.reproject(
        RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson",
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    filtered_geoms = vector.filter(
        reproj_geoms,
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(filtered_geoms) == 19

    filtered_geoms = vector.filter(
        reproj_geoms,
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
        within=True)
    assert len(filtered_geoms) == 2

    geoms = vector.reproject(
        vector.filter(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson",
                      RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 19

    geoms = vector.reproject(
        vector.filter(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson",
                      RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
                      within=True),
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 2

    geoms = vector.reproject(
        vector.filter(Path(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson"),
                      Path(RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")),
        Path(RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        output=Path(RastertoolsTestsData.tests_output_data_dir + "/" + "reproject_filter.geojson"))
    assert len(geoms) == 19
    gen_files = ["reproject_filter.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files, tolerance = 1.e-8)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    geometries = gpd.read_file(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson")
    geoms = vector.reproject(
        vector.filter(geometries,
                      Path(RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")),
        Path(RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        output=Path(RastertoolsTestsData.tests_output_data_dir + "/" + "reproject_filter.geojson"))
    assert len(geoms) == 19
    gen_files = ["reproject_filter.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files, tolerance = 1.e-8)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_reproject_dissolve(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    geoms = vector.reproject(
        vector.dissolve(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson"),
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 1

    geoms = vector.reproject(
        vector.dissolve(Path(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson")),
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
        output=Path(RastertoolsTestsData.tests_output_data_dir + "/" + "reproject_dissolve.geojson"))
    assert len(geoms) == 1
    gen_files = ["reproject_dissolve.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files, tolerance = 1.e-8)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_clip(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    geoms = vector.clip(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson",
                        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 19

    geoms = vector.clip(
        Path(RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson"),
        Path(RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        output=Path(RastertoolsTestsData.tests_output_data_dir + "/" + "clip.geojson"))
    assert len(geoms) == 19
    gen_files = ["clip.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files, tolerance = 1.e-8, column_sortby = 'ID')
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_get_raster_shape(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    geoms = vector.get_raster_shape(
        RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 1

    geoms = vector.get_raster_shape(
        Path(RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        Path(RastertoolsTestsData.tests_output_data_dir + "/" + "raster_outline.geojson"))
    assert len(geoms) == 1
    gen_files = ["raster_outline.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_rasterize():
    # tested by test_stats
    assert True


def test_crop():
    # tested by test_rasterproduct
    assert True
