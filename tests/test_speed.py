#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import filecmp
from eolab.rastertools import Speed
from eolab.rastertools.product import RasterType

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


__refdir = utils4test.get_refdir("test_radioindice/")


def test_speed_process_files(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    name1 = "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D"
    name2 = "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D"

    date1 = RasterType.get("S2_L2A_MAJA").get_date(name1)

    files = [utils4test.indir + name1 + "-ndvi.tif",
             utils4test.indir + name2 + "-ndvi.tif"]

    tool = Speed()
    tool.with_output(utils4test.outdir)

    outputs = tool.process_files(files)
    exp_outs = [name2 + "-ndvi-speed-" + date1.strftime('%Y%m%d-%H%M%S') + ".tif"]

    assert outputs == [utils4test.outdir + exp_out for exp_out in exp_outs]

    if compare:
        match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, __refdir, exp_outs)
        assert len(match) == 1
        assert len(mismatch) == 0
        assert len(err) == 0
    elif save_gen_as_ref:
        # save the generated files in the refdir => make them the new refs.
        utils4test.copy_to_ref(exp_outs, __refdir)

    utils4test.clear_outdir()
