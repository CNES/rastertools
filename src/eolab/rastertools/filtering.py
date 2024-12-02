#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named Filtering that can apply different kind
of filters on raster images.
"""
import logging.config
from typing import List, Dict
from pathlib import Path

from eolab.rastertools import utils
from eolab.rastertools import Rastertool, Windowable
from eolab.rastertools.processing import algo
from eolab.rastertools.processing import RasterFilter, compute_sliding
from eolab.rastertools.product import RasterProduct


_logger = logging.getLogger(__name__)


class Filtering(Rastertool, Windowable):
    """Raster tool that applies a filter on a raster image.

    Predefined filters are available:

    - Median filter
    - Local sum
    - Local mean
    - Adaptive gaussian filter.

    A filter is applied on a kernel of a configurable size. To set the kernel size, you need
    to call:

    .. code-block:: python

        tool = Filtering(Filtering.median_filter, kernel_size=16)

    Custom additional filters can be easily added by instanciating a RasterFilter (see
    :obj:`eolab.rastertools.processing.RasterFilter`).

    The parameters that customize the filter algo can be passed by following this procedure:

    .. code-block:: python

        def myalgo(input_data, **kwargs):
            # kwargs contain the values of the algo parameters
            kernel_size = kwargs.get('kernel_size', 8)
            myparam = kwargs.get('myparam', 1)
            # ... do someting ...

        my_filter = RasterFilter(
            "myfilter", algo=myalgo
        ).with_documentation(
            help="Apply my filter",
            description="Apply my filter"
        ).with_arguments({
            "myparam": {
                # configure the command line interface for this param, this can be skipped
                "default": 8,
                "required": True,
                "type": int,
                "help": "my configuration param for myalgo"
            }
        })

        # create the raster tool
        tool = Filtering(my_filter, kernel_size=16)
        my_filter.with_output(".")
        my_filter.with_window(1024, "edge")
        # set the configuration parameter of the algo
        my_filter.with_filter_configuration({"myparam": 1024})
        # run the tool
        tool.process_file("./mytif.tif")
    """
    median_filter = RasterFilter(
        "median", algo=algo.median
    ).with_documentation(
        help="Apply median filter",
        description="Apply a median filter (see scipy median_filter for more information)"
    )
    """
    Applies a Median Filter to the input data using 
    `scipy.ndimage.median_filter <https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.median_filter.html>`_.
    The filter computes the median contained in the sliding window determined by kernel_size.

    Returns:
        Numpy array containing the input data filtered by the median filter
    """

    local_sum = RasterFilter(
        "sum", algo=algo.local_sum
    ).with_documentation(
        help="Apply local sum filter",
        description="Apply a local sum filter using integral image method"
    )
    """Computes the local sums of the input data.
    Each element is the sum of the pixels contained in the sliding window determined by kernel_size.

    Returns:
        Numpy array of the size of input_data containing the computed local sums
    """

    local_mean = RasterFilter(
        "mean", algo=algo.local_mean
    ).with_documentation(
        help="Apply local mean filter",
        description="Apply a local mean filter using integral image method",
    )
    """Computes the local means of the input data.
    Each element is the mean of the pixels contained in the sliding window determined by kernel_size.

    Returns:
        Numpy array of the size of input_data containing the computed local means
    """

    adaptive_gaussian = RasterFilter(
        "adaptive_gaussian", algo=algo.adaptive_gaussian, per_band_algo=True
    ).with_documentation(
        help="Apply adaptive gaussian filter",
        description="Apply an adaptive (Local gaussian of 3x3) recursive filter on the input image",
    ).with_arguments({
        "sigma": {
            "default": 1,
            "required": True,
            "type": float,
            "help": "Standard deviation of the Gaussian distribution (sigma)"
        },
    })
    """RasterFilter that applies an adaptive gaussian filter to the kernel. The parameter sigma defines the standard deviation 
    of the Gaussian distribution.

    Returns:
        Numpy array containing the input data filtered by the Gaussian filter.
    """

    @staticmethod
    def get_default_filters():
        """Get the list of predefined raster filters

        Returns:
            [:obj:`eolab.rastertools.processing.RasterFilter`] List of the predefined
            raster filters ([Median, Local sum, Local mean, Adaptive gaussian])
        """
        return [
            Filtering.median_filter, Filtering.local_sum,
            Filtering.local_mean, Filtering.adaptive_gaussian
        ]

    def __init__(self, raster_filter: RasterFilter, kernel_size: int, bands: List[int] = [1]):
        """Constructor

        Args:
            raster_filter (:obj:`eolab.rastertools.processing.RasterFilter`):
                The instance of RasterFilter to apply
            kernel_size (int):
                Size of the kernel on which the filter is applied
            bands ([int], optional, default=[1]):
                List of bands in the input image to process.
                Set None if all bands shall be processed.
        """
        super().__init__()
        # initialize default windowing configuration
        self.with_windows()
        # the raster filter processing
        self._raster_filter = raster_filter
        self._raster_filter.configure({"kernel_size": kernel_size})

        self._bands = bands

    @property
    def bands(self) -> List[int]:
        """List of bands to process"""
        return self._bands

    @property
    def raster_filter(self) -> RasterFilter:
        """Name of the filter to apply to the raster"""
        return self._raster_filter

    def with_filter_configuration(self, argsdict: Dict):
        """Configure the filter with its specific arguments' values

        Args:
            argsdict (dict):
                Dictionary of filter's arguments names and values. Shall contain at least
                the kernel size (key="kernel")

        Returns:
            :obj:`eolab.rastertools.Filtering`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        self.raster_filter.configure(argsdict)
        return self

    def process_file(self, inputfile: str) -> List[str]:
        """Apply the filter to the input file

        Args:
            inputfile (str):
                Input image to process

        Returns:
            ([str]) A list of one element containing the path of the generated filtered image.
        """
        _logger.info(f"Processing file {inputfile}")

        overlap = (self.raster_filter.kernel_size + 1) // 2
        if overlap >= min(self.window_size) / 2:
            raise ValueError("The kernel size (option --kernel_size, "
                             f"value={self.raster_filter.kernel_size}) "
                             "must be strictly less than the window size minus 1 "
                             f"(option --window_size, value={min(self.window_size)})")

        # STEP 1: Prepare the input image so that it can be processed
        with RasterProduct(inputfile, vrt_outputdir=self.vrt_dir) as product:

            # STEP 2: apply filter
            outdir = Path(self.outputdir)
            output_image = outdir.joinpath(
                f"{utils.get_basename(inputfile)}-{self.raster_filter.name}.tif")

            compute_sliding(
                product.get_raster(), output_image, self.raster_filter,
                window_size=self.window_size,
                window_overlap=(self.raster_filter.kernel_size + 1) // 2,
                pad_mode=self.pad_mode,
                bands=self.bands)

            return [output_image.as_posix()]
