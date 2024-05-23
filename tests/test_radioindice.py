#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import filecmp
import logging
from eolab.rastertools import Radioindice
from eolab.rastertools.processing.rasterproc import RadioindiceProcessing
from eolab.rastertools.product.rastertype import BandChannel

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


__refdir = utils4test.get_refdir("test_radioindice/")


def test_radioindice_process_file_merge():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    inputfile = utils4test.indir + "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip"
    indices = [indice for indice in Radioindice.get_default_indices()]

    tool = Radioindice(indices)
    tool.with_output(utils4test.outdir, merge=True)
    tool.with_roi(utils4test.indir + "COMMUNE_32001.shp")
    outputs = tool.process_file(inputfile)

    assert outputs == [
        utils4test.outdir + "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-indices.tif"]

    utils4test.clear_outdir()


def test_radioindice_process_file_separate(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    inputfile = "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D"
    indices = [Radioindice.ndvi, Radioindice.ndwi]

    tool = Radioindice(indices)
    tool.with_output(utils4test.outdir, merge=False)
    tool.with_vrt_stored(False)
    outputs = tool.process_file(utils4test.indir + inputfile + ".zip")

    # check outputs
    assert outputs == [utils4test.outdir + inputfile + "-ndvi.tif",
                       utils4test.outdir + inputfile + "-ndwi.tif"]

    gen_files = [inputfile + "-ndvi.tif", inputfile + "-ndwi.tif"]
    if compare:
        match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, __refdir, gen_files)
        assert len(match) == 2
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_radioindice_process_files():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    inputfiles = [utils4test.indir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
                  utils4test.indir + "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip"]
    indices = [Radioindice.ndvi, Radioindice.ndwi]

    tool = Radioindice(indices)
    tool.with_output(utils4test.outdir, merge=True)
    tool.with_roi(utils4test.indir + "COMMUNE_32001.shp")
    outputs = tool.process_files(inputfiles)

    assert outputs == [
        utils4test.outdir + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-indices.tif",
        utils4test.outdir + "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-indices.tif"]

    utils4test.clear_outdir()


def test_radioindice_incompatible_indice_rastertype(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    file = "SPOT6_2018_France-Ortho_NC_DRS-MS_SPOT6_2018_FRANCE_ORTHO_NC_GEOSUD_MS_82.tar.gz"
    inputfile = utils4test.indir + file
    indice = RadioindiceProcessing("my_indice").with_channels([BandChannel.mir, BandChannel.swir])

    tool = Radioindice([indice])
    tool.with_output(utils4test.outdir)

    caplog.set_level(logging.ERROR)
    outputs = tool.process_file(inputfile)

    assert len(outputs) == 0
    exp_log = ("eolab.rastertools.radioindice", logging.ERROR,
               f"Can not compute my_indice for {file}: "
               "raster product does not contain all required bands.")
    assert caplog.record_tuples[0] == exp_log

    utils4test.clear_outdir()
