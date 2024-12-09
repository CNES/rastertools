#!/usr/bin/env python
# -*- coding: utf-8 -*-

import filecmp
import geopandas as gpd
from pathlib import Path

from eolab.rastertools.processing import vector

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


__refdir = utils4test.get_refdir("test_vector/")


def test_reproject_filter(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    reproj_geoms = vector.reproject(
        utils4test.indir + "COMMUNE_32xxx.geojson",
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    filtered_geoms = vector.filter(
        reproj_geoms,
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(filtered_geoms) == 19

    filtered_geoms = vector.filter(
        reproj_geoms,
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
        within=True)
    assert len(filtered_geoms) == 2

    geoms = vector.reproject(
        vector.filter(utils4test.indir + "COMMUNE_32xxx.geojson",
                      utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 19

    geoms = vector.reproject(
        vector.filter(utils4test.indir + "COMMUNE_32xxx.geojson",
                      utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
                      within=True),
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 2

    geoms = vector.reproject(
        vector.filter(Path(utils4test.indir + "COMMUNE_32xxx.geojson"),
                      Path(utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")),
        Path(utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        output=Path(utils4test.outdir + "reproject_filter.geojson"))
    assert len(geoms) == 19
    gen_files = ["reproject_filter.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, __refdir, gen_files, tolerance = 1.e-8)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    geometries = gpd.read_file(utils4test.indir + "COMMUNE_32xxx.geojson")
    geoms = vector.reproject(
        vector.filter(geometries,
                      Path(utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")),
        Path(utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        output=Path(utils4test.outdir + "reproject_filter.geojson"))
    assert len(geoms) == 19
    gen_files = ["reproject_filter.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, __refdir, gen_files, tolerance = 1.e-8)
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
        vector.dissolve(utils4test.indir + "COMMUNE_32xxx.geojson"),
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 1

    geoms = vector.reproject(
        vector.dissolve(Path(utils4test.indir + "COMMUNE_32xxx.geojson")),
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
        output=Path(utils4test.outdir + "reproject_dissolve.geojson"))
    assert len(geoms) == 1
    gen_files = ["reproject_dissolve.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, __refdir, gen_files, tolerance = 1.e-8)
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

    geoms = vector.clip(utils4test.indir + "COMMUNE_32xxx.geojson",
                        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 19

    geoms = vector.clip(
        Path(utils4test.indir + "COMMUNE_32xxx.geojson"),
        Path(utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        output=Path(utils4test.outdir + "clip.geojson"))
    assert len(geoms) == 19
    gen_files = ["clip.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, __refdir, gen_files, tolerance = 1.e-8, column_sortby = 'ID')
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
        utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif")
    assert len(geoms) == 1

    geoms = vector.get_raster_shape(
        Path(utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"),
        Path(utils4test.outdir + "raster_outline.geojson"))
    assert len(geoms) == 1
    gen_files = ["raster_outline.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, __refdir, gen_files)
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
