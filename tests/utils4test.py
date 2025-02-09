#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path

from . import cmptools

__author = "Olivier Queyrut"
__copyright = "Copyright 2019, CNES"
__license = "Apache v2.0"


indir = "tests/tests_data/"
outdir = "tests/tests_out/"
__root_refdir = "tests/tests_refs/"


def get_refdir(testname: str):
    return __root_refdir + testname


def clear_outdir(subdirs=True):
    """function to clear content of a dir"""
    for file in os.listdir(outdir):
        file_path = os.path.join(outdir, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif subdirs:
            # delete the subdir
            delete_dir(file_path)


def create_outdir():
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    clear_outdir()


def delete_dir(dir):
    shutil.rmtree(dir)


def copy_to_ref(files, refdir):
    for f in files:
        os.replace(outdir + f, refdir + f)


def basename(infile):
    """function to get basename of file"""
    file = Path(infile) if isinstance(infile, str) else infile
    suffix = len("".join(file.suffixes))
    return file.name if suffix == 0 else file.name[:-suffix]


def cmpfiles(a, b, common, tolerance=1e-9):
    """Compare common files in two directories.

    a, b -- directory names
    common -- list of file names found in both directories
    shallow -- if true, do comparison based solely on stat() information

    Returns a tuple of three lists:
      files that compare equal
      files that are different
      filenames that aren't regular files.

    """
    res = ([], [], [])
    for x in common:
        new = os.path.join(a, x)
        golden = os.path.join(b, x)
        res[_cmp(golden, new, tolerance)].append(x)
    return res


def _cmp(gld, new, tolerance):
    ftype = os.path.splitext(gld)[-1].lower()
    cmp = cmptools.CMP_FUN[ftype]
    try:
        return not cmp(gld, new, tolerance=tolerance)
    except OSError:
        return 2
