#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a command line named radioindice that computes radiometric
indices on raster images: ndvi, ndwi, etc..
"""
import logging.config
from pathlib import Path
from typing import List
import numpy as np
import rasterio
import rioxarray

from eolab.rastertools import utils
import xarray as xr
from eolab.rastertools import Rastertool, Windowable
from eolab.rastertools.processing import algo
from eolab.rastertools.processing import RadioindiceProcessing
from eolab.rastertools.product import BandChannel, RasterProduct


_logger = logging.getLogger(__name__)


class Radioindice(Rastertool, Windowable):
    """Raster tool that computes radiometric indices of a raster product.

    If several indices are requested, the tool can generate one output image with one
    band per indice (merge=True), or it can generate several images, one image per indice
    (merge=False).

    The computation can be realized on a subset of the input image (a Region Of Interest)
    defined by a vector file (e.g. shapefile, geojson).

    The radiometric indice is an instance of
    :obj:`eolab.rastertools.processing.RadioindiceProcessing`
    which defines the list of channels it needs to compute the indice. The input raster product
    must be of a recognized raster type so that it is possible to match every channels required by
    the indice with an existing band in the raster product.
    """
    # Preconfigured radioindices
    # Vegetation indices: ndvi
    ndvi = RadioindiceProcessing("ndvi").with_channels(
        [BandChannel.red, BandChannel.nir])
    """Normalized Difference Vegetation Index (red, nir channels)

    .. math::

        ndvi = \\frac{nir - red}{nir + red}

    References:
        Rouse J.W., Haas R.H., Schell J.A., Deering D.W., 1973. Monitoring vegetation systems in
        the great plains with ERTS. Third ERTS Symposium, NASA SP-351. 1:309-317

        Tucker C.J., 1979. Red and photographic infrared linear combinations for monitoring
        vegetation. Remote Sens Environ 8:127-150

    """

    # Vegetation indices: tndvi
    tndvi = RadioindiceProcessing("tndvi", algo=algo.tndvi).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Transformed Normalized Difference Vegetation Index (red, nir channels)

    .. math::
        :nowrap:

        \\begin{eqnarray}
            ndvi & = & \\frac{nir - red}{nir + red} \\\\
            tndvi & = & \\sqrt{ndvi + 0.5}
        \\end{eqnarray}

    References:
        `Deering D.W., Rouse J.W., Haas R.H., and Schell J.A., 1975. Measuring forage production
        of grazing units from Landsat MSS data. Pages 1169-1178 In: Cook J.J. (Ed.), Proceedings
        of the Tenth International Symposium on Remote Sensing of Environment (Ann Arbor, 1975),
        Vol. 2, Ann Arbor, Michigan, USA. <https://www.scirp.org/reference/referencespapers?referenceid=1046714>`_

    """

    # Vegetation indices: rvi
    rvi = RadioindiceProcessing("rvi", algo=algo.rvi).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Ratio Vegetation Index (red, nir channels)

    .. math::

        rvi = \\frac{nir}{red}

    References:
        `Jordan C.F., 1969. Derivation of leaf area index from quality of light on the forest
        floor. Ecology 50:663-666 <https://esajournals.onlinelibrary.wiley.com/doi/10.2307/1936256>`_
    """

    # Vegetation indices: pvi
    pvi = RadioindiceProcessing("pvi", algo=algo.pvi).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Perpendicular Vegetation Index (red, nir channels)

    .. math::

        pvi = (nir - 0.90893 * red - 7.46216) * 0.74

    References:
        `Richardson A.J., Wiegand C.L., 1977. Distinguishing vegetation from soil background
        information. Photogramm Eng Rem S 43-1541-1552 <https://www.asprs.org/wp-content/uploads/pers/1977journal/dec/1977_dec_1541-1552.pdf>`_
    """

    # Vegetation indices: savi
    savi = RadioindiceProcessing("savi", algo=algo.savi).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Soil Adjusted Vegetation Index (red, nir channels)

    .. math::

        savi = \\frac{(nir - red) * (1. + 0.5)}{nir + red + 0.5}

    References:
        `Huete A.R., 1988. A soil-adjusted vegetation index (SAVI). Remote Sens Environ 25:295-309 <https://www.sciencedirect.com/science/article/abs/pii/003442578890106X>`_
    """

    # Vegetation indices: tsavi
    tsavi = RadioindiceProcessing("tsavi", algo=algo.tsavi).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Transformed Soil Adjusted Vegetation Index (red, nir channels)

    .. math::

        tsavi = \\frac{0.7 * (nir - 0.7 * red - 0.9)}{0.7 * nir + red + 0.08 * (1 + 0.7^2)}

    References:
        `Baret F., Guyot G., Major D., 1989. TSAVI: a vegetation index which minimizes soil
        brightness effects on LAI or APAR estimation. 12th Canadian Symposium on Remote
        Sensing and IGARSS 1990, Vancouver, Canada, 07/10-14. <https://www.researchgate.net/publication/3679422_TSAVI_A_vegetation_index_which_minimizes_soil_brightness_effects_on_LAI_and_APAR_estimation>`_
    """

    # Vegetation indices: msavi
    msavi = RadioindiceProcessing("msavi", algo=algo.msavi).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Modified Soil Adjusted Vegetation Index (red, nir channels)

    .. math::
        :nowrap:

        \\begin{eqnarray}
            wdvi & = & nir - 0.4 * red \\\\
            ndvi & = & \\frac{nir - red}{nir + red} \\\\
            L & = & 1 - 2 * 0.4 * ndvi * wdvi \\\\
            msavi & = & \\frac{(nir - red) * (1 + L)}{nir + red + L}
        \\end{eqnarray}

    References:
        `Qi J., Chehbouni A., Huete A.R., Kerr Y.H., 1994. Modified Soil Adjusted Vegetation
        Index (MSAVI). Remote Sens Environ 48:119-126 <https://www.researchgate.net/publication/223906415_A_Modified_Soil_Adjusted_Vegetation_Index>`_

        `Qi J., Kerr Y., Chehbouni A., 1994. External factor consideration in vegetation index
        development. Proc. of Physical Measurements and Signatures in Remote Sensing,
        ISPRS, 723-730. <https://www.academia.edu/20596726/External_factor_consideration_in_vegetation_index_development>`_
    """

    # Vegetation indices: msavi2
    msavi2 = RadioindiceProcessing("msavi2", algo=algo.msavi2).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Modified Soil Adjusted Vegetation Index (red, nir channels)

    .. math::
        :nowrap:

        \\begin{eqnarray}
            val & = & (2 * nir + 1)^2 - 8 * (nir - red) \\\\
            msavi2 & = & (2 * nir + 1 - \\sqrt{val}) / 2
        \\end{eqnarray}
    """

    # Vegetation indices: ipvi
    ipvi = RadioindiceProcessing("ipvi", algo=algo.ipvi).with_channels(
        [BandChannel.red, BandChannel.nir])
    """Infrared Percentage Vegetation Index (red, nir channels)

    .. math::
        ipvi = \\frac{nir}{nir + red}

    References:
        `Crippen, R. E. 1990. Calculating the Vegetation Index Faster, Remote Sensing of
        Environment, vol 34., pp. 71-73. <https://www.sciencedirect.com/science/article/abs/pii/003442579090085Z>`_
    """

    # Vegetation indices: evi
    evi = RadioindiceProcessing("evi", algo=algo.evi).with_channels(
        [BandChannel.red, BandChannel.nir, BandChannel.blue])
    """Enhanced vegetation index (red, nir, blue channels)

    .. math::
        evi = \\frac{2.5 * (nir - red)}{nir + 6.0 * red - 7.5 * blue + 1.0}

    """

    # Water indices: ndwi
    ndwi = RadioindiceProcessing("ndwi").with_channels(
        [BandChannel.mir, BandChannel.nir])
    """Normalized Difference Water Index (mir, nir channels)

    .. math::

        ndwi = \\frac{nir - mir}{nir + mir}

    References:
        Gao, B. C., 1996. NDWI - A normalized difference water index for remote sensing
        of vegetation liquid water from space. Remote Sensing of Environment 58, 257-266.
    """

    # Water indices: ndwi2
    ndwi2 = RadioindiceProcessing("ndwi2").with_channels(
        [BandChannel.nir, BandChannel.green])
    """Normalized Difference Water Index (nir, green channels)

    .. math::

        ndwi2 = \\frac{green - nir}{green + nir}
    """

    # Water indices: mdwi
    mndwi = RadioindiceProcessing("mndwi").with_channels(
        [BandChannel.mir, BandChannel.green])
    """Modified Normalized Difference Water Index (green, mir channels)

    .. math::

        mndwi = \\frac{green - mir}{green + mir}

    References:
        Xu, H. Q., 2006. Modification of normalised difference water index (NDWI) to enhance
        open water features in remotely sensed imagery. International Journal of Remote Sensing
        27, 3025-3033

    """

    # Water indices: ndpi
    ndpi = RadioindiceProcessing("ndpi").with_channels(
        [BandChannel.green, BandChannel.mir])
    """Normalized Difference Pond Index (green, mir channels)

    .. math::

        ndpi = \\frac{mir - green}{mir + green}

    References:
        J-P. Lacaux, Y. M. Tourre, C. Vignolle, J-A. Ndione, and M. Lafaye, "Classification
        of Ponds from High-Spatial Resolution Remote Sensing: Application to Rift Valley Fever
        Epidemics in Senegal," Remote Sensing of Environment 106 66–74, Elsevier Publishers: 2007
    """

    # Water indices: ndti
    ndti = RadioindiceProcessing("ndti").with_channels(
        [BandChannel.green, BandChannel.red])
    """Normalized Difference Turbidity Index (green, red channels)

    .. math::

        ndti = \\frac{red - green}{red + green}

    References:
        J-P. Lacaux, Y. M. Tourre, C. Vignolle, J-A. Ndione, and M. Lafaye, "Classification
        of Ponds from High-Spatial Resolution Remote Sensing: Application to Rift Valley Fever
        Epidemics in Senegal," Remote Sensing of Environment 106 66–74, Elsevier Publishers: 2007
    """

    # urban indices: ndbi
    ndbi = RadioindiceProcessing("ndbi").with_channels(
        [BandChannel.nir, BandChannel.mir])
    """Normalized Difference Built Up Index (nir, mir channels)
    
    .. math::

        ndbi = \\frac{mir - nir}{mir + nir}

    """

    # Soil indices: ri
    ri = RadioindiceProcessing("ri", algo=algo.redness_index).with_channels(
        [BandChannel.red, BandChannel.green])
    """Redness index (red, green channels)

    .. math::

        ri = \\frac{red^2}{green^3}

    """

    # Soil indices: bi
    bi = RadioindiceProcessing("bi", algo=algo.brightness_index).with_channels(
        [BandChannel.red, BandChannel.green])
    """Brightness index (red, green channels)

    .. math::

        bi = \\frac{red^2 + green^2}{2}

    """

    # Soil indices: bi2
    bi2 = RadioindiceProcessing("bi2", algo=algo.brightness_index2).with_channels(
        [BandChannel.nir, BandChannel.red, BandChannel.green])
    """Brightness index (nir, red, green channels)

    .. math::

        bi2 = \\frac{nir^2 + red^2 + green^2}{3}

    """

    @staticmethod
    def get_default_indices():
        """Get the list of predefined radiometric indices

        Returns:
            [:obj:`eolab.rastertools.processing.RadioindiceProcessing`]: list of
            predefined radioindice.
        """
        # returns all predefined radiometric indices
        return [
            Radioindice.ndvi, Radioindice.tndvi, Radioindice.rvi, Radioindice.pvi,
            Radioindice.savi, Radioindice.tsavi, Radioindice.msavi, Radioindice.msavi2,
            Radioindice.ipvi, Radioindice.evi, Radioindice.ndwi, Radioindice.ndwi2,
            Radioindice.mndwi, Radioindice.ndpi, Radioindice.ndti, Radioindice.ndbi,
            Radioindice.ri, Radioindice.bi, Radioindice.bi2
        ]

    def __init__(self, indices: List[RadioindiceProcessing]):
        """ Constructor

        Args:
            indices ([:obj:`eolab.rastertools.processing.RadioindiceProcessing`]):
                List of indices to compute (class Indice)
        """
        super().__init__()
        self.with_windows()

        self._indices = indices
        self._merge = False
        self._roi = None

    @property
    def indices(self) -> List[RadioindiceProcessing]:
        """List of radiometric indices to compute"""
        return self._indices

    @property
    def merge(self) -> bool:
        """If true, all indices are in the same output image (one band per indice).
        Otherwise, each indice is in its own output image."""
        return self._merge

    @property
    def roi(self) -> str:
        """Filename of the vector data defining the ROI"""
        return self._roi

    def with_output(self, outputdir: str = ".", merge: bool = False):
        """Set up the output.

        Args:
            outputdir (str, optional, default="."):
                Output dir where to store results. If none, it is set to current dir
            merge (bool, optional, default=False):
                Whether to merge all indices in the same image (i.e. one band per indice)

        Returns:
            :obj:`eolab.rastertools.Radioindice`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        super().with_output(outputdir)
        self._merge = merge
        return self

    def with_roi(self, roi: str):
        """Set up the region of interest

        Args:
            roi (str):
                Filename of the vector data defining the ROI
                (output images will be cropped to the geometry)

        Returns:
            :obj:`eolab.rastertools.Radioindice`: The current instance so that it is
            possible to chain the with... calls (fluent API)
        """
        self._roi = roi

    def process_file(self, inputfile: str) -> List[str]:
        """Compute the indices for a single file

        Args:
            inputfile (str):
                Input image to process

        Returns:
            [str]: List of indice images (posix paths) that have been generated
        """
        _logger.info(f"Processing file {inputfile}")

        outdir = Path(self.outputdir)

        # Prepare the input image so that it can be processed
        with RasterProduct(inputfile, vrt_outputdir=self.vrt_dir) as product:
            _logger.debug(f"Raster product is : {product}")

            if product.rastertype is None:
                raise ValueError("Unsupported input file, no matching raster type "
                                 "identified to handle the file")
            else:
                filename = utils.to_path(inputfile).name
                _logger.info(f"Raster type of image {filename} is {product.rastertype.name}")

                # check if all indices can be computed for this raster
                indices = list()
                for indice in self.indices:
                    # check if the rastertype has all channels
                    if not(product.rastertype.has_channels(indice.channels)):
                        _logger.error(f"Can not compute {indice} for {filename}: "
                                      "raster product does not contain all required bands.")
                    else:
                        # indice is valid, add it to the list of indices to compute
                        indices.append(indice)

            # get the raster
            raster = product.get_raster(roi=self.roi)

            # STEP 2: Compute the indices
            outputs = []
            if self.merge:
                # merge is True, compute all indices and generate a single image
                _logger.info(f"Compute indices: {' '.join(indice.name for indice in indices)}")
                indice_image = outdir.joinpath(f"{utils.get_basename(inputfile)}-indices.tif")
                compute_indices(raster, product.channels, indice_image.as_posix(),
                                indices, self.window_size)
                outputs.append(indice_image.as_posix())
            else:
                # merge is False, compute all indices and generate one image per indice
                for i, indice in enumerate(indices):
                    _logger.info(f"Compute {indice.name}")
                    indice_image = outdir.joinpath(
                        f"{utils.get_basename(inputfile)}-{indice.name}.tif")
                    compute_indices(raster, product.channels, indice_image.as_posix(),
                                    [indice], self.window_size)
                    outputs.append(indice_image.as_posix())

        # return the list of generated files
        return outputs

def compute_indices(input_image: str, image_channels: List[BandChannel],
                    indice_image: str, indices: List[RadioindiceProcessing],
                    window_size: tuple = (1024, 1024)):
    """
    Compute the indices on the input image and produce a multiple bands
    image (one band per indice)

    The possible indices are the following :
    ndvi, tndvi, rvi, pvi, savi, tsavi, msavi, msavi2, ipvi, evi, ndwi, ndwi2, mndwi, ndpi, ndti, ndbi, ri, bi, bi2

    Args:
        input_image (str):
            Path of the raster to compute
        image_channels ([:obj:`eolab.rastertools.product.BandChannel`]):
            Ordered list of bands in the raster
        indice_image (str):
            Path of the output raster image
        indices ([:obj:`eolab.rastertools.processing.RadioindiceProcessing`]):
            List of indices to compute
        window_size (tuple(int, int), optional, default=(1024, 1024)):
            Size of windows for splitting the processed image in small parts
    """
    with rasterio.Env(GDAL_VRT_ENABLE_PYTHON=True):

        with rioxarray.open_rasterio(input_image, masked=True, chunks=True, cache=False, lock = False) as src_array:

            # dtype of output data
            dtype = indices[0].dtype or rasterio.float32
            src_array.load()
            src_array = src_array.astype(dtype)
            nodata = -10000
            crs = src_array.rio.crs
            #Replace nodata values with np.nan
            src_array = src_array.where(src_array != nodata, other=np.nan)

            # Prepare an empty DataArray for the result
            result = xr.DataArray(
                np.zeros((len(indices), src_array.shape[1], src_array.shape[2]), dtype=dtype),
                dims=["band", "y", "x"],
                coords={"band": [indice.name for indice in indices],
                        "y": src_array.coords["y"],
                        "x": src_array.coords["x"]})

            # compute every indices
            for i, indice in enumerate(indices, 1):
                # Get the bands necessary to compute the indice
                bands = [image_channels.index(channel) + 1 for channel in indice.channels]

                res = indice.algo(src_array.sel(band=bands)).astype(dtype)
                res = res.where(~res.isnull(), other=-2)
                result.loc[{"band": indice.name}]  = res

            # Create the file and compute
            result.rio.write_crs(crs, inplace=True)
            result.rio.to_raster(indice_image, nodata=-2, dtype=dtype)

            # Attach statistics to the raster using Rasterio
            with rasterio.open(indice_image, "r+") as dataset:

                dataset.nodata = -2.0
                for band_idx in range(1, dataset.count + 1):

                    band = dataset.read(band_idx, masked=True)
                    band = np.ma.masked_invalid(band)  # Handle NaN values

                    # Calculate statistics
                    stats = {
                        "STATISTICS_MINIMUM": float(np.nanmin(band)),
                        "STATISTICS_MAXIMUM": float(np.nanmax(band)),
                        "STATISTICS_MEAN": float(np.nanmean(band)),
                        "STATISTICS_STDDEV": float(np.nanstd(band))
                    }

                    # Write metadata to the band
                    dataset.update_tags(band_idx, **stats)


