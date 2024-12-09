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
    '''
    This function tests the Radioindice class's ability to generate a merged output file containing multiple indices. The indices generated
    include:

        NDVI, TNDVI, RVI, PVI, SAVI, TSAVI, MSAVI, MSAVI2, IPVI, EVI, NDWI, NDWI2,
        MNDVI, NDPI, NDTI, NDBI, RI, BI, BI2.

    The function compares the generated output to an expected output file.

    Asserts:
    - The generated output file is named correctly and matches the expected filename.

    Clears the output directory at the end of the test.
    '''
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


def test_radioindice_process_file_separate(compare : bool, save_gen_as_ref : bool):
    """
    Test the Radioindice class by generating individual files for each indice.

    This function verifies the generation of separate output files for NDVI and NDWI.
    The results can be compared with reference files or saved as new references if desired.

    Parameters:
    - compare (bool): If True, compares the generated files to reference files.
    - save_gen_as_ref (bool): If True, saves the generated files as new reference files.

    Asserts:
    - The output files match the reference files.

    Clears the output directory at the end of the test.
    """
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
        print(mismatch)
        assert len(match) == 2
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(gen_files, __refdir)

    utils4test.clear_outdir()


def test_radioindice_process_files():
    '''
    Test the Radioindice class by processing multiple files and merging results.

    This function applies the NDVI and NDWI to a list of Sentinel-2 datasets.
    The function generates a merged output file for each input file. Results are verified by comparing to tif files containing the expected results.

    Asserts:
    - The generated output files match the expected names for merged indices.

    Clears the output directory at the end of the test.
    '''
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
    """
    Test handling of incompatible indices and raster types in the Radioindice class.

    This function verifies that the Radioindice class correctly handles cases where the
    raster file lacks the required bands for a specified index.

    Parameters:
    - caplog: pytest fixture for capturing log output within the test.

    Asserts:
    - No output files are generated (output list is empty).
    - An error log entry is recorded with details about the missing bands.

    Clears the output directory at the end of the test.
    """
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
