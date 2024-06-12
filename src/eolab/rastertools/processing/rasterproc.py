#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Definition of a radiometric indice and functions to compute it.
"""
from typing import List, Callable, Union

import numpy as np

from eolab.rastertools.processing import algo
from eolab.rastertools.product import BandChannel


class RasterProcessing:
    """This class defines a processing on a raster image.
    """

    def __init__(self, name: str,
                 algo: Callable = None,
                 nodata: float = None,
                 dtype: np.dtype = None,
                 processing_dtype: np.dtype = None,
                 compress: str = None,
                 nbits: int = False,
                 per_band_algo: bool = False):
        """Constructor

        Args:
            name (str):
                Display name of the processing
            algo (Callable[[List[np.ndarray], kwargs], np.ndarray], optional, default=None):
                Lambda function used to compute the indice. The lambda function
                takes as input a multidimensional array of data to process and the list of
                the arguments values of the processing (see with\\_argument()).
                It returns the processed data.
            nodata (float, optional, default=None):
                Nodata value for the output data
            dtype (rasterio or numpy data type, optional, default=None):
                Type of generated data. When None, the generated data are supposed
                to be of the same type as input data.
            processing_dtype (rasterio or numpy data type, optional, default=None):
                Type of processed data. When None, the processed data are supposed
                to be of the same type as input data.
            compress (str, optional, default=None):
                Set the compression to use.
            nbits (int, optional, default=None):
                Create a file with less than 8 bits per sample by passing a value from
                1 to 7. The apparent pixel type should be Byte.
            per_band_algo (bool, optional, default=False):
                Whether the algo is applied on a dataset that contains only one band
                (per_band_algo=True) or on a dataset with all bands (per_band_algo=False)
        """
        self._name = name
        self._algo = algo
        self._per_band_algo = per_band_algo
        self._nodata = nodata
        self._dtype = dtype
        self._processing_dtype = processing_dtype
        self._compress = compress
        self._nbits = nbits
        self._arguments = dict()

    def __repr__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        """Name of the processing"""
        return self._name

    @property
    def algo(self) -> Callable:
        """Processing algo that is called on a multidimensional array of data"""
        return self._algo

    @property
    def per_band_algo(self) -> bool:
        """Whether the algo is applied on a dataset that contains only one band
        (per_band_algo=True) or on a dataset with all bands (per_band_algo=False)"""
        return self._per_band_algo

    @property
    def nodata(self) -> float:
        """No data value of the generated data"""
        return self._nodata

    @property
    def dtype(self):
        """Type of the generated data"""
        return self._dtype

    @property
    def processing_dtype(self):
        """Type of the processed data"""
        return self._processing_dtype

    @property
    def compress(self) -> str:
        """Set the compression to use"""
        return self._compress

    @property
    def nbits(self) -> int:
        """bits size of the generated data"""
        return self._nbits

    @property
    def description(self):
        """Long description of the processing"""
        return self._description

    @property
    def help(self):
        """Help message of the processing"""
        return self._help

    @property
    def aliases(self):
        """Aliases of the processing"""
        return self._aliases

    @property
    def arguments(self):
        """Definition of Arguments that parametrize the processing algorithm (see with_arguments for
           the description of the data structure)"""
        return self._arguments

    def with_documentation(self, aliases: List[str] = None,
                           help: str = "", description: str = ""):
        """Set up the documentation for the processing

        Args:
            aliases ([str], optional, default=None):
                List of command aliases
            help (str, optional, default=""):
                Help message
            description (str, optional, default=""):
                Long description

        Returns:
            self: Current instance so that it is possible to chain the with... calls (fluent API)
        """
        self._aliases = aliases or list()
        self._help = help
        self._description = description
        return self

    def with_arguments(self, arguments):
        """Add new arguments that parametrize the processing algorithm.

        Args:
            arguments (Dict[str, Dict]):
                Dictionary where the keys are the arguments' names and the values are dictionaries
                of arguments' properties as defined in ArgumentParser.add_argument - see
                https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.
                The properties dictionaries are used to configure the command line 'rastertools'.
                The possible keys are: action, nargs, const, default, type, choices, required, help,
                metavar and dest

        Returns:
            self: Current instance so that it is possible to chain the with... calls (fluent API)
        """
        self._arguments.update(arguments)
        return self

    def configure(self, argsdict):
        """Configure the processing algo with its specific arguments' values

        Args:
            argsdict (dict):
                Dictionary of arguments names and values, for instance {"kernel_size": 8}
        """
        [setattr(self, argument, argsdict[argument])
         for argument in self.arguments if argument in argsdict]

    def compute(self, input_data: Union[List[np.ndarray], np.ndarray]):
        """Compute the output from the different bands of the input data. Output
        data are supposed to be the same size as input_data.

        Args:
            input_data ([np.ndarray] or np.ndarray):
                List of input data (one np.ndarray per band) or a 3 dimensions np.ndarray
                with all bands

        Returns:
            Output data
        """
        if self.algo is not None:
            argparameters = {arg: getattr(self, arg, None) for arg in self.arguments}
            output = self.algo(input_data, **argparameters)
        else:
            output = input_data
        return output


class RadioindiceProcessing(RasterProcessing):
    """Class that defines a raster processing for computing radiometric indice.
    This class defines the list of BandChannel necessary to compute the radiometric indice.
    """

    def __init__(self, name: str,
                 algo: Callable = algo.normalized_difference,
                 nodata: float = -2.0,
                 dtype: np.dtype = np.float32):
        """Constructor. See documentation of RasterProcessing.__init__ for
        the description of input arguments.
        """
        super().__init__(name, algo=algo, nodata=nodata, dtype=dtype, per_band_algo=False)

    @property
    def channels(self) -> List[BandChannel]:
        """List of channels necessary to compute the radiometric indice"""
        return self._channels

    def with_channels(self, channels: List[BandChannel]):
        """Set the BandChannels necessary to compute the radiometric indice

        Args:
            channels ([:obj:`eolab.rastertools.product.BandChannel`]):
                Channels to process, default None

        Returns:
            The current instance so that it is possible to chain the with... calls (fluent API)
        """
        self._channels = channels
        return self


class RasterFilter(RasterProcessing):
    """Class that defines a raster processing for applying a filter on a kernel (square of
    configurable size).
    """

    def __init__(self, name: str,
                 algo: Callable = None,
                 nodata: float = -2.0,
                 dtype: np.dtype = np.float32,
                 per_band_algo: bool = False):
        """Constructor. See documentation of RasterProcessing.__init__ for
        the description of input arguments.
        """
        super().__init__(name, algo=algo, nodata=nodata, dtype=dtype, per_band_algo=per_band_algo)

        # kernel size of the filter
        self._kernel_size = 8
        # define an argument for the kernel size
        self.with_arguments({
            "kernel_size": {
                "default": 8,
                "required": True,
                "type": int,
                "help": "Kernel size of the filter function, e.g. 3 means a square of 3x3 pixels"
                        " on which the filter function is computed (default: 8)"
            }
        })
        self.with_documentation(f"Apply {name} filter", f"Apply {name} filter")
