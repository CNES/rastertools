#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines the base class for every Rastertool, namely :obj:`eolab.rastertools.Rastertool`.

It also defines a specific Exception class that shall be raised when invalid rastertool's
configuration parameters are setup.

Finally, it defines additional decorator classes that factorize some rastertool configuration
features. For example, the class :obj:`eolab.rastertools.Windowable` enables to configure a
rastertool with windowable capabilities (i.e. capability to split the raster input file in small
parts in order to distribute the processing over several cpus).
"""
from abc import ABC
from typing import List
import logging
import sys

from eolab.rastertools import utils

_logger = logging.getLogger(__name__)

class RastertoolConfigurationException(Exception):
    """This class defines an exception that is raised when the configuration of the raster tool
    is invalid (wrong input parameter)
    """
    pass


class Rastertool(ABC):
    """Base class for every raster tool which contains the common configuration:

    - the output dir where to store the results (by default, current dir)
    - whether to save to disk the intermediate VRT images that can be created when
      handling the input raster products (that can be an archive of several band files for
      example). This parameter is mainly for debug purpose and is False by default.
    """

    def __init__(self):
        """Constructor
        """
        self._outputdir = "."
        self._keep_vrt = False

    @property
    def outputdir(self) -> str:
        """Path of the output directory where are stored the results"""
        return self._outputdir

    @property
    def keep_vrt(self) -> bool:
        """Whether intermediate VRT images shall be kept"""
        return self._keep_vrt

    @property
    def vrt_dir(self) -> str:
        """Dir where to store intermediate VRT images"""
        return self.outputdir or "." if self.keep_vrt else None

    def with_output(self, outputdir: str = "."):
        """Set up the output.

        Args:
            outputdir (str, optional, default="."):
                Output dir where to store results. If none, it is set to current dir

        Returns:
            :obj:`eolab.rastertools.Rastertool`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        if outputdir and not utils.is_dir(outputdir):
            _logger.exception(
                RastertoolConfigurationException(f"Output directory \"{str(outputdir)}\" does not exist."))
            sys.exit(2)
        self._outputdir = outputdir
        return self

    def with_vrt_stored(self, keep_vrt: bool):
        """Configure if the intermediate VRT images that are generated when handling
        the input files (which can be complex raster product composed of several band files)
        shall be stored to disk or not - for debug purpose for instance.

        Args:
            keep_vrt (bool):
                Whether intermediate VRT images shall be stored or not

        Returns:
            :obj:`eolab.rastertools.Rastertool`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        self._keep_vrt = keep_vrt
        return self

    def process_files(self, inputfiles: List[str]):
        """Run the rastertool to a set of input files. By default, this implementation
        recursively calls "process_file" on each input file and then calls "postprocess_files".

        Note:
            It is not meant to be overriden by subclasses. Prefer overriding process_file
            and postproces_files instead.

        Args:
            inputfiles ([str]): Input images to process

        Returns:
            ([str]) The list of the generated files
        """
        all_outputs = []
        for filename in inputfiles:
            outputs = self.process_file(filename)
            if outputs:
                all_outputs.extend(outputs)

        # add a postprocessing call of the corresponding class
        outputs = self.postprocess_files(inputfiles, all_outputs)

        if outputs:
            all_outputs.extend(outputs)
        return all_outputs

    def process_file(self, inputfile: str) -> List[str]:
        """Run the rastertool to a single input file.

        Note:
            This implementation does nothing. Override this method in the subclass
            to achieve special processing of an inputfile.

        Args:
            inputfile (str):
                Input image to process

        Returns:
            [str]: List of generated files (by default empty list)
        """
        # nothing to do by default, just return input file as output
        return list()

    def postprocess_files(self, inputfiles: List[str], outputfiles: List[str]) -> List[str]:
        """Run a postprocess when all input files have been processed. This step may consist
        in transforming the outputs or mixing them to generate additional ones.

        Note:
            This implementation does nothing. Override this method in the subclass
            to achieve special processing that needs the whole list of inputfiles
            and/or the output files generated when processing every single file (to mix
            them for instance).

        Args:
            inputfiles ([str]): Input images to process
            outputfiles ([str]): List of generated files after executing the
                rastertool on the input files

        Returns
            [str]: Additional output files (by default empty list)
        """
        # nothing to do by default
        return list()


class Windowable:
    """Decorator of a :obj:`eolab.rastertools.Rastertool` that adds configuration
    parameters to set the windowable capability of the tool:

    - the window size
    - the mode for padding the window when at the edge of the image
    """

    @property
    def window_size(self) -> int:
        """Size of the windows to split the image in small parts"""
        return self._window_size

    @property
    def pad_mode(self) -> str:
        """
        Mode used to `pad <https://numpy.org/doc/stable/reference/generated/numpy.pad.html>`_ the image when the window is on the edge of the image
        The mode can be self defined or among [constant (default), edge, linear_ramp, maximum, mean, median, minimum, reflect, symmetric, wrap, empty].
        """
        return self._pad_mode

    def with_windows(self, window_size: int = 1024, pad_mode: str = "edge"):
        """Configure the window generation for processing image

        Args:
            window_size (int, optional, default=1024):
                Size of windows for splitting the processed image in small parts
                so that processing can be distributed on several cpus.
            pad_mode (str, optional, default="edge"):
                Mode for padding data around the windows that are on the edge of the image.
                See https://numpy.org/doc/stable/reference/generated/numpy.pad.html

        Returns:
            :obj:`eolab.rastertools.Rastertool`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        self._window_size = utils.to_tuple(window_size)
        self._pad_mode = pad_mode
        return self
