#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import pytest
from pathlib import Path
from eolab.rastertools import Zonalstats
from eolab.rastertools import RastertoolConfigurationException

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"

from .utils4test import RastertoolsTestsData

__refdir = utils4test.get_refdir("test_zonalstats/")


def test_zonalstats_global(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # cas 1
    inputfile = RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
    outformat = "ESRI Shapefile"
    statistics = "min max mean std count range sum".split()
    categorical = False

    tool = Zonalstats(statistics, categorical)
    tool.with_output(RastertoolsTestsData.tests_output_data_dir + "/", output_format=outformat)
    tool.with_outliers(1.0)
    tool.process_file(inputfile)

    gen_files = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-stats.shp",
                 "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-stats-outliers.tif"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files)
        assert len(match) == 2
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    # cas 2
    inputfile = RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
    outformat = "GeoJSON"
    statistics = "median majority minority unique percentile_10 percentile_90".split()
    categorical = False

    tool = Zonalstats(statistics, categorical)
    tool.with_output(RastertoolsTestsData.tests_output_data_dir + "/", output_format=outformat)
    tool.process_file(inputfile)

    gen_files = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-stats.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    # cas 3 : unrecognized rastertype that disables charting capability, no output file for stats
    inputfile = RastertoolsTestsData.tests_input_data_dir + "/" + "toulouse-mnh.tif"
    statistics = "mean std".split()
    categorical = False

    tool = Zonalstats(statistics, categorical)
    tool.with_output(None)
    tool.with_chart(RastertoolsTestsData.tests_output_data_dir + "/" + "chart.png")
    tool.process_file(inputfile)
    assert len(tool.generated_stats) == 1
    assert len(tool.generated_stats_per_date) == 0

    utils4test.clear_outdir()


def test_zonalstats_zonal(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # cas 1
    inputfile = RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
    outformat = "ESRI Shapefile"
    statistics = "min max mean std count range sum".split()
    categorical = False

    tool = Zonalstats(statistics, categorical)
    tool.with_output(RastertoolsTestsData.tests_output_data_dir + "/", output_format=outformat)
    tool.with_geometries(geometries=RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson")
    tool.with_outliers(sigma=1.0)
    tool.process_file(inputfile)

    gen_files = ["SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi-stats.shp",
                 "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi-stats-outliers.tif"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files)
        assert len(match) == 2
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    # cas 2
    inputfile = RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
    outformat = "GeoJSON"
    statistics = "median majority minority unique percentile_10 percentile_90".split()
    categorical = False

    tool = Zonalstats(statistics, categorical)
    tool.with_output(RastertoolsTestsData.tests_output_data_dir + "/", output_format=outformat)
    tool.with_geometries(geometries=RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson")
    tool.process_file(inputfile)

    gen_files = ["SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi-stats.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_zonalstats_process_files(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    data_path = RastertoolsTestsData.tests_input_data_dir.replace(os.getcwd() + "/", "") + "/"
    out_path = RastertoolsTestsData.tests_output_data_dir.replace(os.getcwd() + "/", "") + "/"

    utils4test.create_outdir()

    inputfiles = [data_path + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
                  data_path + "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"]
    outformat = "GeoJSON"
    statistics = "min max mean std count range sum".split()

    tool = Zonalstats(statistics, prefix="indice")
    tool.with_output(None, output_format=outformat)
    tool.with_geometries(geometries=data_path + "COMMUNE_32xxx.geojson")
    tool.with_chart(chart_file=out_path + "chart.png")
    tool.process_files(inputfiles)

    gen_files = ["chart.png"]
    assert Path(out_path + "chart.png").exists()
    if compare:
        match, mismatch, err = utils4test.cmpfiles(out_path, __refdir, gen_files)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_zonalstats_category(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # cas 1 - classif shapefile sur une ROI composée de plusieurs géométries
    inputfile = RastertoolsTestsData.tests_input_data_dir + "/" + "DSM_PHR_Dunkerque.tif"
    outformat = "GeoJSON"
    statistics = "min max mean std count range sum".split()
    # Category inputs
    categoryfile = RastertoolsTestsData.tests_input_data_dir + "/" + "OSO_2017_classification_dep59.shp"
    categorydic = RastertoolsTestsData.tests_input_data_dir + "/" + "OSO_nomenclature_2017.json"

    tool = Zonalstats(statistics, area=True)
    tool.with_output(RastertoolsTestsData.tests_output_data_dir + "/", output_format=outformat)
    tool.with_geometries(geometries=RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_59xxx.geojson")
    tool.with_per_category(category_file=categoryfile, category_index="Classe",
                           category_labels_json=categorydic)
    tool.process_file(inputfile)

    gen_files = ["DSM_PHR_Dunkerque-stats.geojson"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    # cas 2 - classif raster sur l'emprise globale du DSM
    inputfile = RastertoolsTestsData.tests_input_data_dir + "/" + "DSM_PHR_Dunkerque.tif"
    outformat = "GeoJSON"
    categoryfile = RastertoolsTestsData.tests_input_data_dir + "/" + "OCS_2017_CESBIO_extract.tif"
    categorydic = RastertoolsTestsData.tests_input_data_dir + "/" + "OSO_nomenclature_2017.json"

    tool = Zonalstats(statistics, area=True)
    tool.with_output(RastertoolsTestsData.tests_output_data_dir + "/", output_format=outformat)
    tool.with_per_category(category_file=categoryfile, category_index="Classe",
                           category_labels_json=categorydic)
    tool.process_file(inputfile)

    # gen_files = ["DSM_PHR_Dunkerque-stats.geojson"]
    # do not compare, order of features can change in output
    # if compare:
    #     match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", __refdir, gen_files)
    #     assert len(match) == 1
    #     assert len(mismatch) == 0
    #     assert len(err) == 0
    # elif save_gen_as_ref:
    #     # save the generated files in the refdir => make them the new refs.
    #     utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_zonalstats_errors():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # cas 1 - Invalid "valid threshold" value
    with pytest.raises(RastertoolConfigurationException) as err:
        tool = Zonalstats(["min"], valid_threshold=1.2)
    assert f"Valid threshold must be in range [0.0, 1.0]." in str(err.value)

    # cas 1 - valid stats is missing
    with pytest.raises(RastertoolConfigurationException) as err:
        tool = Zonalstats(["min"], valid_threshold=0.8)
    assert ("Cannot apply a valid threshold when the computation of the valid "
            "stat has not been requested.") in str(err.value)

    utils4test.clear_outdir()


def test_zonalstats_category_errors():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # cas 1 - Invalid category file
    statistics = "min max mean std count range sum".split()
    # Category inputs
    categoryfile = RastertoolsTestsData.tests_input_data_dir + "/" + "unknown.tif"
    categorydic = RastertoolsTestsData.tests_input_data_dir + "/" + "OSO_nomenclature_2017.json"

    tool = Zonalstats(statistics)
    with pytest.raises(RastertoolConfigurationException) as err:
        tool.with_per_category(category_file=categoryfile, category_index="Classe",
                               category_labels_json=categorydic)
    assert f"File {categoryfile} cannot be read: check format and existence" in str(err.value)

    # cas 2 - invalid category dictionary
    categoryfile = RastertoolsTestsData.tests_input_data_dir + "/" + "OCS_2017_CESBIO_extract.tif"
    categorydic = RastertoolsTestsData.tests_input_data_dir + "/" + "OSO_nomenclature_2017_wrong.json"

    tool = Zonalstats(statistics)
    with pytest.raises(RastertoolConfigurationException) as err:
        tool.with_per_category(category_file=categoryfile, category_index="Classe",
                               category_labels_json=categorydic)
    assert f"File {categorydic} does not contain a valid dict." in str(err.value)

    with pytest.raises(RastertoolConfigurationException) as err:
        tool = Zonalstats(["percentile_110"])
    assert f"percentiles must be <= 100" in str(err.value)

    with pytest.raises(RastertoolConfigurationException) as err:
        tool = Zonalstats(["percentile_-10"])
    assert f"percentiles must be >= 0" in str(err.value)

    with pytest.raises(RastertoolConfigurationException) as err:
        tool = Zonalstats(["strange_stat"])
    msg = f"Invalid stat strange_stat: must be percentile_xxx or one of {Zonalstats.valid_stats}"
    assert msg in str(err.value)

    utils4test.clear_outdir()
