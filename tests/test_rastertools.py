#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import logging
import filecmp
from pathlib import Path
from eolab.rastertools import run_tool
from eolab.rastertools.product import RasterType

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


class TestCase:
    __test__ = False

    def __init__(self, args):
        self._args = args.split()
        self._outputs = list()
        self._logs = list()
        self._sys_exit = 0

    def __repr__(self):
        return (f"rastertools {' '.join(self._args)}"
                f"[outputs={self._outputs}][logs={self._logs}][sys_exit={self._sys_exit}]")

    @property
    def args(self):
        return self._args

    @property
    def outputs(self):
        return self._outputs

    @property
    def logs(self):
        return self._logs

    @property
    def sys_exit(self):
        return self._sys_exit

    def output(self, filenames):
        self._outputs = filenames
        return self

    def ri_output(self, indices, indice_filenames):
        self._outputs = [f.format(ind) for ind in indices.split() for f in indice_filenames]
        return self

    def zs_output(self, input_filenames, outlier=False):
        # check list of outputs
        self._outputs = [f + "-stats.geojson" for f in input_filenames]
        if outlier:
            self._outputs.extend([file + "-stats-outliers.tif" for file in input_filenames])
        return self

    def ti_output(self, input_filenames, ids, name="{}-tile{}", subdir=""):
        if subdir:
            if not(subdir.endswith("/")):
                subdir = subdir + "/"
        else:
            subdir = ""
        self._outputs = [name.format(f, id) for id in ids for f in input_filenames]
        return self

    def fi_output(self, input_filenames, filter):
        self._outputs = [name.format(filter) for name in input_filenames]
        return self

    def with_logs(self, logs=list(), loglevel=logging.INFO):
        self._logs = logs
        self._loglevel = loglevel
        return self

    def with_sys_exit(self, sys_exit):
        self._sys_exit = sys_exit
        return self

    def with_refdir(self, refdir):
        self._refdir = refdir
        return self

    def run_test(self, caplog=None, loglevel=logging.ERROR, check_outputs=True, check_sys_exit=True, check_logs=True,
                 compare=False, save_gen_as_ref=False):
        if caplog is not None:
            caplog.set_level(loglevel)
        else:
            check_logs = False

        # run rastertools
        with pytest.raises(SystemExit) as wrapped_exception:
            run_tool(args=self._args)

        # check sys_exit
        if check_sys_exit:
            assert wrapped_exception.type == SystemExit
            assert wrapped_exception.value.code == self._sys_exit

        # check list of outputs
        if check_outputs:
            outdir = Path(utils4test.outdir)
            assert sorted([x.name for x in outdir.iterdir()]) == sorted(self._outputs)

        if compare:
            match, mismatch, err = utils4test.cmpfiles(utils4test.outdir, self._refdir, self._outputs)
            assert len(match) == 3
            assert len(mismatch) == 0
            assert len(err) == 0
        elif save_gen_as_ref:
            # save the generated files in the refdir => make them the new refs.
            utils4test.copy_to_ref(self._outputs, self._refdir)

        # check logs
        if check_logs:
            for i, log in enumerate(self._logs):
                assert caplog.record_tuples[i] == log

        # clear the log recorder
        if caplog is not None:
            caplog.clear()

        # clear output dir
        utils4test.clear_outdir()


def test_rastertools_command_line_info():
    tests = [
        TestCase("--help"),
        TestCase("-h"),
        TestCase("--version"),
        TestCase(""),
        TestCase("radioindice --help"),
        TestCase("ri -h"),
        TestCase("zonalstats --help"),
        TestCase("zs -h"),
        TestCase("tiling --help"),
        TestCase("ti -h"),
        TestCase("filter --help"),
        TestCase("fi -h"),
        TestCase("timeseries --help"),
        TestCase("ts -h"),
        TestCase("speed --help"),
        TestCase("sp -h"),
        TestCase("svf --help"),
        TestCase("svf -h"),
        TestCase("hillshade --help"),
        TestCase("hs -h")
    ]
    for test in tests:
        test.run_test()


def test_radioindice_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # no indice defined
        " -v ri -o tests/tests_out tests/tests_data/listing.lst",
        # two indices with their own options, merge
        "-v ri --pvi --savi -o tests/tests_out -m tests/tests_data/listing.lst",
        # indices option, roi
        "--verbose ri --indices pvi savi -nd nir red --roi tests/tests_data/COMMUNE_32001.shp"
        " --output tests/tests_out"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
        " tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip"
    ]
    # get list of expected outputs
    indices_list = ["ndvi ndwi ndwi2", "indices", "pvi savi nd[nir-red]"]
    indices_filenames = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-{}.tif",
                         "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-{}.tif"]

    # generate test cases
    tests = [TestCase(args).ri_output(indices, indices_filenames)
             for (args, indices) in zip(argslist, indices_list)]

    # execute test cases
    for test in tests:
        test.run_test()


def test_radioindice_additional_type():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # add rastertypes to handle new data product
        "-t tests/tests_data/additional_rastertypes.json -v"
        " ri -o tests/tests_out --ndvi tests/tests_data/RGB_TIF_20170105_013442_test.tif"
    ]
    # get list of expected outputs
    indices_list = "ndvi"
    indices_filenames = ["RGB_TIF_20170105_013442_test-{}.tif"]

    # generate test cases
    tests = [TestCase(args).ri_output(indices_list, indices_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test()

    assert RasterType.get("RGB_TIF") is not None
    assert RasterType.get("RGB_TIF_ARCHIVE") is not None


def test_radioindice_command_line_errors(caplog):
    # list of commands to test
    argslist = [
        # missing positional argument
        "ri --ndvi",
        # unkwnow indice
        "ri tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip --indices strange",
        # unknown raster type: unrecognized raster type
        "-v ri --ndvi -o tests/tests_out tests/tests_data/OCS_2017_CESBIO_extract.tif",
        # unknown raster type: unsupported extension
        "-v ri --ndvi -o tests/tests_out tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.aaa",
        # output dir does not exist
        "-v ri -o ./toto --ndvi tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
        # unknown band in normalized difference
        "-v ri -nd unknown red tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
    ]

    # expected logs
    logslist = [
        [],
        [("eolab.rastertools.main", logging.ERROR, "Invalid indice name: strange")],
        [("eolab.rastertools.main", logging.ERROR,
          "Unsupported input file, no matching raster type identified to handle the file")],
        [("eolab.rastertools.main", logging.ERROR,
          "Unsupported input file tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.aaa")],
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.rastertools.main", logging.ERROR,
          "Invalid band(s) in normalized difference: unknown and/or red")]
    ]
    sysexitlist = [2, 2, 1, 1, 2, 2]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_speed_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default with a listing of S2A products
        "-v sp -b 1 -o tests/tests_out tests/tests_data/listing.lst",
        # default with a list of files
        "--verbose speed --output tests/tests_out"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        " tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
    ]
    speed_filenames = [
        ["SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-speed-20180928-105515.tif"],
        ["SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi-speed-20180928-105515.tif"]
    ]

    # generate test cases
    tests = [TestCase(args).output(f)
             for args, f in zip(argslist, speed_filenames)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test()


def test_speed_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v sp -o ./toto tests/tests_data/listing2.lst",
        # missing one file for speed
        "-v sp -o tests/tests_out tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
        # different types for input files
        "-v sp -a -o tests/tests_out"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
        " tests/tests_data/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.zip"
    ]
    # expected logs
    logslist = [
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.rastertools.main", logging.ERROR,
          "Can not compute speed with 1 input image. Provide at least 2 images.")],
        [("eolab.rastertools.main", logging.ERROR,
          "Speed can only be computed with images of the same type")]
    ]
    sysexitlist = [2, 1, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sys_exit)
             for args, logs, sys_exit in zip(argslist, logslist, sysexitlist)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_timeseries_command_line_default(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default with a list of files
        "--verbose ts --output tests/tests_out"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        " tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
        " -s 2018-09-26 -e 2018-11-07 -p 20 -ws 512"
    ]
    timeseries_filenames = [
        ["SENTINEL2A_20180926-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif",
         "SENTINEL2A_20181016-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif",
         "SENTINEL2A_20181105-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif"]
    ]
    refdir = utils4test.get_refdir("test_timeseries/")

    # generate test cases
    tests = [TestCase(args).output(f)
             for args, f in zip(argslist, timeseries_filenames)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.with_refdir(refdir)
        test.run_test(compare=compare, save_gen_as_ref=save_gen_as_ref)


def test_timeseries_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    period = " -s 2018-09-26 -e 2018-11-07 -p 20"
    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v ts -o ./toto tests/tests_data/listing2.lst" + period,
        # missing one file for timeseries
        "-v ts -o tests/tests_out tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif" + period,
        # unknown raster type
        "-v ts -o tests/tests_out -a"
        " tests/tests_data/DSM_PHR_Dunkerque.tif"
        " tests/tests_data/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.zip" + period,
        # different types for input files
        "-v ts -o tests/tests_out"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
        " tests/tests_data/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.zip" + period,
        # invalid date format
        "-v ts --o tests/tests_out"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        " tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
        " -s 20180926 -e 2018-11-07 -p 20",
        # invalid date format
        "-v ts --o tests/tests_out"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        " tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
        " -s 2018-09-26 -e 20181107 -p 20"
    ]
    # expected logs
    logslist = [
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.rastertools.main", logging.ERROR,
          "Can not compute a timeseries with 1 input image. Provide at least 2 images.")],
        [("eolab.rastertools.main", logging.ERROR,
          "Unknown rastertype for input file tests/tests_data/DSM_PHR_Dunkerque.tif")],
        [("eolab.rastertools.main", logging.ERROR,
          "Timeseries can only be computed with images of the same type")],
        [("eolab.rastertools.main", logging.ERROR,
          "Invalid format for start date: 20180926 (must be %Y-%m-%d)")],
        [("eolab.rastertools.main", logging.ERROR,
          "Invalid format for end date: 20181107 (must be %Y-%m-%d)")]
    ]
    sysexitlist = [2, 1, 1, 1, 2, 2]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sys_exit)
             for args, logs, sys_exit in zip(argslist, logslist, sysexitlist)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test(caplog, check_outputs=False)



def test_zonalstats_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # specify stats to compute and sigma, 1st band computed
        "-v zs -o tests/tests_out -f GeoJSON"
        " -g tests/tests_data/COMMUNE_32xxx.geojson --stats min max --sigma 1.0"
        " tests/tests_data/listing2.lst",
        # default stats, all bands computed
        "-v zs -o tests/tests_out -f GeoJSON"
        " --all -g tests/tests_data/COMMUNE_32xxx.geojson"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        " tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
    ]
    files = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi",
             "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi"]
    outliers = [True, False]

    # generate test cases
    tests = [TestCase(args).zs_output(files, outlier)
             for (args, outlier) in zip(argslist, outliers)]

    # execute test cases
    for test in tests:
        test.run_test()


def test_zonalstats_command_line_product():
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # input file is a S2A product
        "-v zs -o tests/tests_out -f GeoJSON"
        " --all -g tests/tests_data/COMMUNE_32xxx.geojson"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
    ]
    files = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D"]

    # generate test cases
    tests = [TestCase(args).zs_output(files) for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test()


def test_zonalstats_command_line_categorical():
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # input file is a S2A product
        "-v zs -o tests/tests_out -f GeoJSON --categorical"
        " tests/tests_data/OCS_2017_CESBIO_extract.tif"
    ]
    files = ["OCS_2017_CESBIO_extract"]

    # generate test cases
    tests = [TestCase(args).zs_output(files) for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test()


def test_zonalstats_command_line_errors():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v zs tests/tests_data/listing2.lst -o ./toto -f GeoJSON"
        " -g tests/tests_data/COMMUNE_32xxx.geojson --stats mean"
        " -b 0",
        # band 0 does not exist
        "-v zs tests/tests_data/listing2.lst -o tests/tests_out -f GeoJSON"
        " -g tests/tests_data/COMMUNE_32xxx.geojson --stats mean"
        " -b 0",
        # invalid format
        "-v zs -o tests/tests_out -f Truc tests/tests_data/listing2.lst",
        # invalid geometry index name
        "-v zs -o tests/tests_out -f GeoJSON --stats mean"
        " -g tests/tests_data/COMMUNE_32xxx.geojson -gi truc"
        " -c tests/tests_out/chart.png"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
        # invalid prefix length
        "-v zs -o tests/tests_out -f GeoJSON --prefix band1"
        " --all -g tests/tests_data/COMMUNE_32xxx.geojson"
        " tests/tests_data/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
    ]

    logslist = [
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.rastertools.main", logging.ERROR,
          "Invalid bands, all values are not in range [1, 1]")],
        [("eolab.rastertools.main", logging.ERROR,
          "Unrecognized output format Truc. Possible values are ")],
        [("eolab.rastertools.main", logging.ERROR,
          "Index 'truc' is not present in the geometries."
          " Please provide a valid value for -gi option.")],
        [("eolab.rastertools.main", logging.ERROR,
          "Number of prefix does not equal the number of bands.")],
    ]

    sysexitlist = [2, 1, 2, 1, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)


def test_tiling_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default case with listing of input files
        "-v ti -o tests/tests_out -g tests/tests_data/grid.geojson tests/tests_data/listing3.lst",
        # default case with input file
        "--verbose ti -o tests/tests_out -g tests/tests_data/grid.geojson"
        " tests/tests_data/tif_file.tif",
        # specify specific ids
        "-v ti -o tests/tests_out -g tests/tests_data/grid.geojson --id 77 93 --id_col id"
        " tests/tests_data/tif_file.tif"
    ]
    input_filenames = ["tests/tests_data/tif_file.tif"]

    # generate test cases
    tests = [TestCase(args).ti_output(input_filenames, [77, 93]) for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)

    # Additional tests to check naming and subdir options
    # specify naming convention
    args = ("-v ti -o tests/tests_out -g tests/tests_data/grid.geojson -n tile{}"
            " --id_col id tests/tests_data/tif_file.tif")
    test = TestCase(args).ti_output(input_filenames, [77, 93], name="tile{}")
    test.run_test(check_outputs=False)

    # specify subdir naming convetion
    args = ("-v ti -o tests/tests_out -g tests/tests_data/grid.geojson -d tile{}"
            " --id_col id tests/tests_data/tif_file.tif")
    test = TestCase(args).ti_output(input_filenames, [77, 93], subdir="tile{}")
    # create one subdir to check if it is not re-created
    subdir = Path("tests/tests_out/tile77")
    subdir.mkdir()
    test.run_test(check_outputs=False)


def test_tiling_command_line_special_case(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # some invalid ids
        "-v ti -o tests/tests_out -g tests/tests_data/grid.geojson --id 1 2 93 --id_col id"
        " tests/tests_data/tif_file.tif",
        # a geometry does not overlap raster
        "-v ti -o tests/tests_out -g tests/tests_data/grid.geojson --id 78 93 --id_col id"
        " tests/tests_data/tif_file.tif"
    ]

    # expected logs
    logslist = [
        [("eolab.rastertools.tiling", logging.ERROR,
          "The grid column \"id\" does not contain the following values: [1, 2]")],
        [("eolab.rastertools.tiling", logging.ERROR,
          "Input shape 78 does not overlap raster")]
    ]

    # generate test cases
    tests = [TestCase(args).with_logs(logs) for (args, logs) in zip(argslist, logslist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_tiling_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # ids without id_col
        "-v ti --id 77 93 -o tests/tests_out -g tests/tests_data/grid.geojson"
        " tests/tests_data/tif_file.tif",
        # invalid id column
        "-v ti -o tests/tests_out -g tests/tests_data/grid.geojson --id 77 93 --id_col truc"
        " tests/tests_data/tif_file.tif",
        # output dir does not exist
        "-v ti -o tests/truc -g tests/tests_data/grid.geojson"
        " tests/tests_data/tif_file.tif",
        # all invalid ids
        "-v ti -o tests/tests_out -g tests/tests_data/grid.geojson --id 1 2 --id_col id"
        " tests/tests_data/tif_file.tif"
    ]

    # expected logs
    logslist = [
        [("eolab.rastertools.main", logging.ERROR,
          "Ids cannot be specified when id_col is not defined")],
        [("eolab.rastertools.main", logging.ERROR,
          "Invalid id column named \"truc\": it does not exist in the grid")],
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [("eolab.rastertools.main", logging.ERROR,
          "No value in the grid column \"id\" are matching the given list of ids [1, 2]")]
    ]
    sysexitlist = [2, 2, 2, 2]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_filtering_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default case: median
        "-v --max_workers 1 fi median -a --kernel_size 8 -o tests/tests_out"
        " tests/tests_data/RGB_TIF_20170105_013442_test.tif",
        # default case: local sum
        "-v fi sum -b 1 2 --kernel_size 8 -o tests/tests_out"
        " tests/tests_data/RGB_TIF_20170105_013442_test.tif",
        # default case: local mean
        "-v fi mean -b 1 --kernel_size 8 -o tests/tests_out"
        " tests/tests_data/RGB_TIF_20170105_013442_test.tif",
        # default case: adaptive gaussian
        "-v fi adaptive_gaussian -b 1 --kernel_size 32 --sigma 1 -o tests/tests_out"
        " tests/tests_data/RGB_TIF_20170105_013442_test.tif",
    ]
    input_filenames = ["RGB_TIF_20170105_013442_test-{}.tif"]
    names = ["median", "sum", "mean", "adaptive_gaussian"]

    # generate test cases
    tests = [TestCase(args).fi_output(input_filenames, name)
             for args, name in zip(argslist, names)]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)


def test_filtering_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v fi median --kernel_size 8 -o tests/truc"
        " tests/tests_data/tif_file.tif",
        # missing required argument
        "-v fi adaptive_gaussian --kernel_size 32 -o tests/tests_out"
        " tests/tests_data/RGB_TIF_20170105_013442_test.tif",
        # kernel_size > window_size
        "-v fi median -a --kernel_size 15 --window_size 16 -o tests/tests_out"
        " tests/tests_data/RGB_TIF_20170105_013442_test.tif",
    ]

    # expected logs
    logslist = [
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [],
        [("eolab.rastertools.main", logging.ERROR,
          "The kernel size (option --kernel_size, value=15) must be strictly less than the "
          "window size minus 1 (option --window_size, value=16)")]
    ]
    sysexitlist = [2, 2, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_svf_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default case: svf at the point height
        "-v svf --radius 50 --directions 16 --resolution 0.5 -o tests/tests_out"
        " tests/tests_data/toulouse-mnh.tif",
        # default case: svf on ground
        # "-v svf --radius 50 --directions 16 --resolution 0.5 --altitude 0 -o tests/tests_out"
        # " tests/tests_data/toulouse-mnh.tif",
    ]
    output_filenames = ["toulouse-mnh-svf.tif"]

    # generate test cases
    tests = [TestCase(args).output(output_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)


def test_svf_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v svf --radius 50 --directions 16 --resolution 0.5 -o tests/truc"
        " tests/tests_data/toulouse-mnh.tif",
        # missing required argument
        "-v svf --directions 16 --resolution 0.5 -o tests/tests_out"
        " tests/tests_data/toulouse-mnh.tif",
        # radius > window_size / 2
        "-v svf --radius 100 --window_size 128 --directions 16 --resolution 0.5"
        " --altitude 0 -o tests/tests_out tests/tests_data/toulouse-mnh.tif",
    ]

    # expected logs
    logslist = [
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [],
        [("eolab.rastertools.main", logging.ERROR,
          "The radius (option --radius, value=100) must be strictly less than half the"
          " size of the window (option --window_size, value=128)")]
    ]
    sysexitlist = [2, 2, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_hillshade_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    # elevation / azimuth are retrieved from https://www.sunearthtools.com/dp/tools/pos_sun.php
    argslist = [
        # default case: hillshade at Toulouse the September, 21 solar noon
        "-v hs --elevation 27.2 --azimuth 82.64 --resolution 0.5 -o tests/tests_out"
        " tests/tests_data/toulouse-mnh.tif",
        # default case: hillshade at Toulouse the June, 21, solar 6PM
        # "-v hs --elevation 25.82 --azimuth 278.58 --resolution 0.5 -o tests/tests_out"
        # " tests/tests_data/toulouse-mnh.tif",
        # # default case: hillshade at Toulouse the June, 21, solar noon
        # "-v hs --elevation 69.83 --azimuth 180 --resolution 0.5 -o tests/tests_out"
        # " tests/tests_data/toulouse-mnh.tif",
        # # default case: hillshade at Toulouse the June, 21, solar 8AM
        # "-v hs --elevation 27.2 --azimuth 82.64 --resolution 0.5 -o tests/tests_out"
        # " tests/tests_data/toulouse-mnh.tif",
    ]
    output_filenames = ["toulouse-mnh-hillshade.tif"]

    # generate test cases
    tests = [TestCase(args).output(output_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)


def test_hillshade_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v hs --elevation 46.81 --azimuth 180.0 --resolution 0.5 -o tests/truc"
        " tests/tests_data/toulouse-mnh.tif",
        # missing required argument
        "-v hs --elevation 46.81 --resolution 0.5 "
        " tests/tests_data/toulouse-mnh.tif",
        # input file has more than 1 band
        "-v hs --elevation 46.81 --azimuth 180.0 --resolution 0.5 -o tests/tests_out"
        " tests/tests_data/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.vrt",
        # radius > window_size / 2
        "-v hs --elevation 27.2 --azimuth 82.64 --resolution 0.5"
        " --radius 100 --window_size 128 -o tests/tests_out"
        " tests/tests_data/toulouse-mnh.tif",
    ]

    # expected logs
    logslist = [
        [("eolab.rastertools.main", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [],
        [("eolab.rastertools.main", logging.ERROR,
          "Invalid input file, it must contain a single band.")],
        [("eolab.rastertools.main", logging.ERROR,
          "The radius (option --radius, value=100) must be strictly less than half"
          " the size of the window (option --window_size, value=128)")]
    ]
    sysexitlist = [2, 2, 1, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)
