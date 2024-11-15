#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Model for raster product enabling to extract bands, timestamp, etc.
"""
from typing import Dict, List, Union, Tuple
from pathlib import Path
from datetime import datetime
import logging
import re
import tarfile
import zipfile
import tempfile
from uuid import uuid4
import xml.etree.ElementTree as ET

from numpy import dtype
from rasterio.io import MemoryFile
from rasterio.vrt import WarpedVRT
from osgeo import gdal
import rasterio

from eolab.rastertools import utils
from eolab.rastertools.product import RasterType
from eolab.rastertools.product.vrt import add_masks_to_vrt, set_band_descriptions
from eolab.rastertools.processing.vector import crop

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


_logger = logging.getLogger(__name__)


class RasterProduct:
    """Data model for a raster product that handles :

       - a raster type
       - the list of available bands
       - the path to the product

    A raster product can be easily like this::

        with RasterProduct("my_product_filename.zip") as product:
            rastertype = product.rastertype()
            raster = product.get_raster()  # raster is an in-memory VRT that can
                                           # be opened using rasterio
            with rasterio.open(raster) as rst:
                print(rst.count)
                data = rst.read([1, 2, 3], masked=True)  # data is a numpy masked array

    A raster product handles several in-memory VRTs that must be properly released. The
    with statement enables this. If you want to control the clean-up of the in-memory VRTs
    you have to call ``free_in_memory_vrts()``.
    """

    def __init__(self, file: Union[Path, str], vrt_outputdir: Union[Path, str] = None):
        """Constructor

        Args:
            file (Path or str):
                Path to the raster product
            vrt_outputdir (Path or str, optional, default=None):
                Dir where to store the generated VRT image(s). If None, output is in memory.
        """
        if file is None:
            raise ValueError("'file' cannot be None")

        self._file = utils.to_path(file)
        self._vrt_outputdir = vrt_outputdir
        self._in_memory_vrts = []

        # try to identify the type of raster product from the input file name
        self._rastertype = RasterType.find(self._file)

        # if input file is an archive (or a dir)
        suffix = utils.get_suffixes(self._file)
        self._is_archive = suffix in [".zip", ".gz", ".tar", ".tar.gz"] or self._file.is_dir()

        # check if we will be able to open the raster and gets the list of bands and masks
        if self._is_archive:
            # inputfile is an archive, need to know its rastertype to open it
            if self.rastertype is None:
                _logger.error("Unrecognized raster type, "
                              "can not create a raster product from an archive of "
                              "unknown raster type")
                raise ValueError(f"Unrecognized raster type for input file {file}")

            # extract bands files and masks files
            bands_regexp = self.rastertype.get_bands_regexp()
            masks_regexp = self.rastertype.get_mask_regexp()
            self._bands_files, self._masks_files = \
                _extract_bands(self.file, bands_regexp, masks_regexp)

        else:
            # inputfile is a regular image file.
            # Check if the file can be opened using rasterio directly
            try:
                dataset = rasterio.open(self._file.as_posix())
                dataset.close()
                self._bands_files = {"all": self._file.as_posix()}
                self._masks_files = {}
            except Exception:
                raise ValueError(f"Unsupported input file {file}")

    def __repr__(self):
        return f"{self._file.name} [{self._rastertype}]"

    def __enter__(self):
        """Enter method for with statement"""
        return self

    def __exit__(self, *args):
        """Exit method for with statement, it cleans the in memory vrt products"""
        self.free_in_memory_vrts()

    def create_in_memory_vrt(self, vrt_content):
        """
        Create an in-memory VRT using Rasterio's MemoryFile.

        Args:
            vrt_content (str): The XML content of the VRT file.
        """
        with MemoryFile() as memfile:
            # Write the VRT content into the memory file
            memfile.write(vrt_content.encode('utf-8'))
            dataset = memfile.open()  # Open the VRT as a dataset
            self._in_memory_vrts.append(memfile)

    def free_in_memory_vrts(self):
        """
        Free in-memory VRTs by closing all MemoryFile objects.
        """
        for vrt in self._in_memory_vrts:
            gdal.Unlink(vrt.as_posix())
        self._in_memory_vrts = []
        # for vrt in self._in_memory_vrts:
        #     vrt.close()  # Closes and cleans up the memory file
        # self._in_memory_vrts = []

    @property
    def file(self) -> Path:
        """Product path"""
        return self._file

    @property
    def rastertype(self) -> RasterType:
        """Type of the raster"""
        return self._rastertype

    @property
    def channels(self):
        """List of available channels in the product"""
        return self._rastertype.channels if self._rastertype is not None else []

    @property
    def bands_files(self):
        """Dictionary of available bands. Key is the identifier of the band,
        value is the path to the band. If all bands are in the same file, the
        dictionary contains only one key named "all".
        """
        return self._bands_files

    @property
    def masks_files(self):
        """Dictionary of available mask bands. Key is the identifier of the mask band,
        value is the path to the band.
        """
        return self._masks_files

    @property
    def is_archive(self):
        """Whether the raster product is an archive (zip, tar, dir, ...) or
        a regular raster image"""
        return self._is_archive

    def get_date(self) -> datetime:
        """Extracts the timestamp of the raster

        Returns:
            :obj:`datetime.datetime`: Timestamp of the raster
        """
        return self._rastertype.get_date(self._file) if self._rastertype is not None else None

    def get_date_string(self, strformat: str = None) -> str:
        """Extracts the timestamp of the raster and returns it as a formatted string

        Returns:
            str: String formatted timestamp of the raster
        """
        date = self.get_date()
        f = strformat
        if f is None:
            f = self._rastertype.date_format if self._rastertype else "%Y%m%dT%H%M%S"
        return date.strftime(f) if date is not None else ""

    def get_tile(self) -> str:
        """Extracts the tile identifier of the raster

        Returns:
            str: Tile tile identifier of the raster
        """
        return self._rastertype.get_group(self._file,
                                          'tile') if self._rastertype is not None else None

    def get_relative_orbit(self) -> int:
        """Extracts the relative orbit number of the raster

        Returns:
            int: Relative orbit number of the raster
        """
        relorbit = None
        if self._rastertype is not None:
            strval = self._rastertype.get_group(self._file, 'relorbit')
            relorbit = int(strval) if strval is not None else None
        return relorbit

    def get_satellite(self) -> str:
        """Extracts the satellite's name of the raster

        Returns:
            str: Name of the satellite
        """
        return self._rastertype.get_group(self._file,
                                          'satellite') if self._rastertype is not None else None

    def open(self,
             bands: Union[str, List[str]] = "all",
             masks: Union[str, List[str]] = "all",
             roi: Union[Path, str] = None):
        """Proxy method to rasterio.open(rasterproduct.get_raster(...))"""
        return rasterio.open(self.get_raster(bands=bands, masks=masks, roi=roi))

    def get_raster(self,
                   bands: Union[str, List[str]] = "all",
                   masks: Union[str, List[str]] = "all",
                   roi: Union[Path, str] = None,
                   create_maskband: bool = True):
        """Gets the path to the raster corresponding to this product.
        This method allows to crop the raster to a specified ROI and to apply the band masks.

        Args:
            bands (str or [str], default="all"):
                List of bands ids to get in the generated raster. If "all", all bands
                defined in the rastertype will be present in the raster.
            masks (str or [str], default="all"):
                List of masks bands ids to get in the generated raster. If "all", all
                masks bands defined in the rastertype will be present in the raster. If
                None, no mask band will be present in the rastertype.
            roi (Path or str, optional, default=None):
                Region of interest defined by a vector data (e.g. GeoJSON) for
                cropping the raster.
            create_maskband (bool, optional, default=True):
                Whether to create the VRT product with a maskband that is a composition
                of all the given masks.

        Returns:
            str: Raster path (either a path to a regular image or
                 a memory path such as /vsimem/...)"""

        if self.is_archive is False:
            # general case: product is a regular raster image
            rasterfile = self.file
        else:
            selected_bands, band_descriptions = self.__get_bands(bands)
            selected_masks, mask_descriptions = self.__get_masks(masks)
            in_memory = self._vrt_outputdir is None
            if in_memory:
                uuid = f"{uuid4()}_"
            else:
                uuid = ""

            # create the raster
            rasterfile = self.__create_vrt(selected_bands, selected_masks, uuid=uuid)
            if in_memory:
                self._in_memory_vrts.append(rasterfile)

            # add band descriptions to the vrt
            descr = band_descriptions + mask_descriptions
            set_band_descriptions(rasterfile, descr)

            # clip the vrt to the ROI
            if roi:
                wrapped_vrt = self.__wrap(rasterfile, utils.to_path(roi), uuid=uuid)
                if in_memory:
                    self._in_memory_vrts.append(wrapped_vrt)

                # add band descriptions
                set_band_descriptions(wrapped_vrt, descr)

                rasterfile = wrapped_vrt

            # apply masks bands
            if create_maskband and len(selected_masks):
                # get the number of bands and masks to separate them in the generated VRT
                nb_bands = len(selected_bands)
                nb_masks = len(selected_masks)
                masked_image = self.__apply_masks(rasterfile, nb_bands, nb_masks, uuid=uuid)
                if in_memory:
                    self._in_memory_vrts.append(masked_image)

                # add band descriptions only
                set_band_descriptions(masked_image, band_descriptions)

                rasterfile = masked_image

        return rasterfile.as_posix()

    def __get_bands(self, bands: Union[str, List[str]] = "all"):
        """Gets the bands files and descriptions corresponding to the given bands ids.

        Args:
            bands (str or [str], default="all"):
                List of bands ids to get in the generated raster. If "all", all bands
                defined in the rastertype will be present in the raster.

        Returns:
            List of bands files and descriptions
        """
        # select the bands to include in the raster
        if isinstance(bands, list) and len(bands):
            for band in bands:
                if band not in self.bands_files.keys():
                    raise ValueError(
                        f"Invalid band id {band}: it does not exist in raster product")
            selected_bands = {k: d for k, d in self.bands_files.items() if k in bands}
        elif bands == "all":
            selected_bands = self.bands_files
        else:
            raise ValueError("Invalid bands list: must be 'all' or a valid no "
                             "empty list of band ids")

        bl = bands if bands != "all" else self.rastertype.get_band_ids()
        band_descriptions = [self.rastertype.get_band_description(channel)
                             for channel in self.channels
                             if self.rastertype.get_band_id(channel) in bl]

        return selected_bands, band_descriptions

    def __get_masks(self, masks: Union[str, List[str]] = "all"):
        """Gets the masks files and descriptions corresponding to the given bands ids.

        Args:
            masks (str or [str], default="all"):
                List of bands ids to get in the generated raster. If "all", all bands
                defined in the rastertype will be present in the raster.

        Returns:
            List of masks files and descriptions
        """
        # select the masks to include in the raster
        if isinstance(masks, list):
            for mask in masks:
                if mask not in self.masks_files.keys():
                    raise ValueError(
                        f"Invalid mask id {mask}: it does not exist in raster product")
            selected_masks = {k: d for k, d in self.masks_files.items() if k in masks}
        elif masks == "all":
            # all masks
            selected_masks = self.masks_files
        else:
            # no mask
            selected_masks = {}

        # generate the descriptions of the bands and masks
        # need to get bands descriptions in the order of channels
        if masks is not None:
            ml = masks if masks != "all" else self.rastertype.get_mask_ids()
        else:
            ml = []
        mask_descriptions = [self.rastertype.get_mask(mask_id).description
                             for mask_id in self.rastertype.get_mask_ids()
                             if mask_id in ml]

        return selected_masks, mask_descriptions

    def __create_vrt(self,
                     bands_files: Dict[str, str],
                     masks_files: Dict[str, str],
                     uuid: str = "") -> Path:
        """Create a VRT for the product archive.

        If the product is a regular raster image then the raster file is simply the product file.

        If the product is an archive (tar, zip, dir, ...), a VRT is created using GDAL BuildVRT. It
        contains the given bands and masks.

        TODO: add arguments to select the resolution and resampling algorithm

        Args:
            bands_files (Dict[str, str]):
                Bands files indexed by the bands ids
            masks_files (Dict[str, str]):
                Masks files indexed by the bands ids
            uuid (str):
                Unique identifier when the VRT is created in memory

        Returns:
            Path: path to the raster file
        """
        # convert parameters defined as str to Path
        outdir = utils.to_path(self._vrt_outputdir, "/vsimem/")
        print(bands_files)
        print(outdir)
        basename = utils.get_basename(self.file)

        _logger.debug("Creating a VRT that handles the bands of the archive product")

        if 'all' in bands_files:
            # one file contains all channels
            bands = [bands_files['all']]
        else:
            # create the list of bands in the same order as rastertype's channels
            bands = [bands_files[id]
                     for id in self.rastertype.get_band_ids()
                     if id in bands_files.keys()]

        # create the list of nodata values for every bands
        nodatavals = [str(self.rastertype.nodata)] * len(bands)

        # when band masks exist, add them to the lists
        if len(masks_files) > 0:
            # add the list of masks in the same order as masks' ids
            bands.extend([masks_files[id] for id in self.rastertype.get_mask_ids()])
            nodatavals.append(str(self.rastertype.masknodata))

        # Create a VRT image with GDAL
        rasterfile = outdir.joinpath(f"{uuid}{basename}.vrt")
        # rasterfile = rasterfile.as_posix()
        ds = gdal.BuildVRT(rasterfile.as_posix(),
                           bands,
                           VRTNodata=' '.join(nodatavals),
                           resolution='highest',
                           # resampleAlg='nearest',
                           separate='all' not in bands_files)
        _logger.debug(f"Generated VRT has {ds.RasterCount} bands")
        # free resource from GDAL
        del ds

        # with rasterio.open(list(bands_files.values())[0]) as src:
        #     width = src.width
        #     height = src.height
        #
        # # with rasterio.open(rasterfile, 'w', driver="GTiff", width=width, height=height, count=1) as dataset:
        # #     dataset.write(bands[0])
        #
        # with rasterio.open(rasterfile, 'w', driver="GTiff", width=width, height=height) as src:
        #     with WarpedVRT(src) as vrt:
        #         print("VRT created with dimensions:", vrt.width, vrt.height)


        # free resource from GDAL
        # - - - - - -
        # # convert parameters defined as str to Path
        # outdir = utils.to_path(self._vrt_outputdir, "/vsimem/")
        # print(outdir)
        # basename = utils.get_basename(self.file)
        # rasterfile = outdir.joinpath(f"{uuid}{basename}.vrt")
        #
        # _logger.debug("Creating a VRT that handles the bands of the archive product")
        #
        # # Initialize VRT XML structure
        # vrt_root = ET.Element("VRTDataset")
        #
        # # Open the first band to get metadata
        # with rasterio.open(list(bands_files.values())[0]) as src:
        #     vrt_root.set("rasterXSize", str(src.width))
        #     vrt_root.set("rasterYSize", str(src.height))
        #     vrt_root.set("subClass", "VRTDataset")
        #     crs_element = ET.SubElement(vrt_root, "SRS")
        #     crs_element.text = src.crs.to_wkt()
        #
        # # Add bands
        # for i, (band_id, band_path) in enumerate(bands_files.items(), start=1):
        #     with rasterio.open(band_path) as src_band:
        #         band_element = ET.SubElement(vrt_root, "VRTRasterBand", attrib={
        #             "dataType": src_band.dtypes[0].upper(),
        #             "band": str(i)
        #         })
        #         source_element = ET.SubElement(band_element, "SimpleSource")
        #         ET.SubElement(source_element, "SourceFilename", attrib={"relativeToVRT": "1"}).text = str(band_path)
        #         ET.SubElement(source_element, "SourceBand").text = "1"
        #         ET.SubElement(source_element, "SourceProperties", attrib={
        #             "RasterXSize": str(src_band.width),
        #             "RasterYSize": str(src_band.height),
        #             "DataType": src_band.dtypes[0].upper(),
        #             "BlockXSize": str(src_band.block_shapes[0][0]),
        #             "BlockYSize": str(src_band.block_shapes[0][1])
        #         })
        #         ET.SubElement(source_element, "SrcRect", attrib={
        #             "xOff": "0", "yOff": "0",
        #             "xSize": str(src_band.width), "ySize": str(src_band.height)
        #         })
        #         ET.SubElement(source_element, "DstRect", attrib={
        #             "xOff": "0", "yOff": "0",
        #             "xSize": str(src_band.width), "ySize": str(src_band.height)
        #         })
        #
        # # Add masks
        # for i, (mask_id, mask_path) in enumerate(masks_files.items(), start=len(bands_files) + 1):
        #     mask_element = ET.SubElement(vrt_root, "VRTRasterBand", attrib={
        #         "dataType": "Byte",
        #         "band": str(i)
        #     })
        #     source_element = ET.SubElement(mask_element, "SimpleSource")
        #     ET.SubElement(source_element, "SourceFilename", attrib={"relativeToVRT": "1"}).text = str(mask_path)
        #     ET.SubElement(source_element, "SourceBand").text = "1"
        #
        # # Write the VRT to file
        # tree = ET.ElementTree(vrt_root)
        # with open(rasterfile, "wb") as f:
        #     tree.write(f, encoding="utf-8", xml_declaration=True)
        return rasterfile

    def __wrap(self, input_vrt: Path, roi: Path, uuid: str = "") -> Path:
        """Clip the image to the given ROI.

        Args:
            input_vrt (Path):
                The input VRT to crop
            roi (Path):
                Region of interest defined by a vector data (e.g. GeoJSON) for
                cropping the raster.
            uuid (str):
                Unique identifier when the VRT is created in memory

        Returns:
            Path: The generated VRT
        """
        # convert parameters defined as str to Path
        outdir = utils.to_path(self._vrt_outputdir, "/vsimem/")
        basename = utils.get_basename(self.file)

        # Clip image to the ROI
        _logger.debug("Cropping the raster to fit the region of interest")
        clipped_image = outdir.joinpath(f"{uuid}{basename}-clipped.vrt")
        crop(input_vrt, roi.as_posix(), clipped_image)

        return clipped_image

    def __apply_masks(self, input_vrt: Path, nb_bands: int, nb_masks: int, uuid: str = "") -> Path:
        """Use the masks files to mask the raster data.

        Args:
            input_vrt (Path):
                The input VRT to mask
            nb_bands (int):
                Number of bands in the input vrt
            nb_masks (int):
                Number of masks in the input vrt
            uuid (str):
                Unique identifier when the VRT is created in memory

        Returns:
            Path: The generated VRT
        """
        # convert parameters defined as str to Path
        outdir = utils.to_path(self._vrt_outputdir, "/vsimem/")
        basename = utils.get_basename(self.file)

        # create a tempdir for generated temporary files
        tempdir = Path(tempfile.gettempdir())

        # create a new vrt with only bands_files
        # it must be written to disk so that we can read it and add a maskband
        temp_image = tempdir.joinpath(f"{uuid}{basename}-temp.vrt")
        ds = gdal.BuildVRT(temp_image.as_posix(), input_vrt.as_posix(),
                           bandList=range(1, nb_bands + 1))
        # free resource from GDAL
        del ds

        # Add mask band
        _logger.debug("Adding band masks")
        masks_index = list(range(nb_bands + 1, nb_bands + nb_masks + 1))
        vrt_new_content = add_masks_to_vrt(temp_image, input_vrt, masks_index,
                                           self.rastertype.maskfunc)
        driver = gdal.GetDriverByName('VRT')
        vrt = gdal.Open(vrt_new_content)
        masked_image = outdir.joinpath(f"{uuid}{basename}-mask.vrt")
        copy_ds = driver.CreateCopy(masked_image.as_posix(), vrt, strict=0)
        del copy_ds
        # delete temp image
        temp_image.unlink()
        # free resource from GDAL
        del vrt

        return masked_image

        # # convert parameters defined as str to Path
        # outdir = utils.to_path(self._vrt_outputdir, "/vsimem/")
        # basename = utils.get_basename(self.file)
        #
        # # create a tempdir for generated temporary files
        # tempdir = Path(tempfile.gettempdir())
        # temp_image = tempdir.joinpath(f"{uuid}{basename}-temp.vrt")
        # with rasterio.open(input_vrt) as src:
        #     # Create a new in-memory VRT for the bands
        #     with WarpedVRT(src, crs=src.crs, transform=src.transform, width=src.width, height=src.height,
        #                    count=nb_bands) as vrt:
        #         # Here you would apply any mask band logic. For simplicity, we assume a method that adds the masks.
        #         # For each mask, you could apply it using rasterio to create new bands with the mask applied.
        #         # Add the masks to the VRT using the provided add_masks_to_vrt function
        #         _logger.debug("Adding mask bands to VRT")
        #         masks_index = list(range(nb_bands + 1, nb_bands + nb_masks + 1))
        #         vrt_new_content = add_masks_to_vrt(temp_image, input_vrt, masks_index,
        #                                    self.rastertype.maskfunc)
        #
        #         # Now save this VRT to a file
        #         masked_image = outdir.joinpath(f"{uuid}{basename}-mask.vrt")
        #         with open(masked_image, 'wb') as out_vrt:
        #             out_vrt.write(vrt_new_content)
        #
        # _logger.debug(f"Generated masked VRT saved to {masked_image}")
        # return masked_image


def _extract_bands(inputfile: Path,
                   bands_pattern: str,
                   masks_pattern: str = None,
                   outputdir: Path = None) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Extracts the bands from an archive

    Args:
        inputfile (Path):
            Archive product that contains the raster bands
        bands_pattern (str):
            Pattern to identify the bands files in the product.
        masks_pattern (str), optional, default=None):
            Pattern to identify the masks files in the product if any.
        outputdir (Path, optional, default=None):
            Dir where to extract images if inputfile is an archive that can't be accessed with
            a path like /vsizip or /vsitar.

    Returns:
        (dict, dict): List of the bands and masks files indexed by their identifier
    """
    bands_masks = None
    if inputfile.is_dir():
        _logger.debug("Getting band files from dir resulting from the uncompressed archive")
        bands_masks = _extract_bands_from_dir(inputfile, bands_pattern,
                                              masks_pattern)
    else:
        _logger.debug("Getting band files from archive (zip, gz, tar or targz)")
        bands_masks = _extract_bands_from_archive(inputfile, bands_pattern,
                                                  masks_pattern)

    _logger.debug(f"Identified bands {', '.join(bands_masks[0])}"
                  f" and masks {', '.join(bands_masks[1])}")

    return bands_masks


def _extract_bands_from_archive(inputfile: Path,
                                bands_pattern: str,
                                masks_pattern: str = None) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Extracts the bands from an archive (zip, gz, tar or targz)

    Args:
        inputfile (Path):
            Archive product that contains the raster bands
        bands_pattern (str):
            Pattern to identify the bands files in the product.
        masks_pattern (str):
            Pattern to identify the masks files in the product if any.

    Returns:
        (dict, dict): List of the bands and masks files indexed by their identifier
    """
    bands_files = {}
    masks_files = {}

    band_regexp = re.compile(bands_pattern)
    has_mask = masks_pattern is not None
    mask_regexp = re.compile(masks_pattern) if has_mask else None

    suffix = utils.get_suffixes(inputfile)
    if suffix in [".zip", ".gz"]:
        # zip or gzip
        rootpath = "/vsizip/"
        with zipfile.ZipFile(inputfile.as_posix()) as myzip:
            names = myzip.namelist()

    else:
        # tar or tar.gz
        rootpath = "/vsitar/"
        with tarfile.open(inputfile.as_posix(),
                          mode='r:gz' if inputfile.suffix == "gz" else 'r') as mytar:
            names = [tarinfo.name for tarinfo in mytar.getmembers()]

    for name in names:
        m = band_regexp.match(name)
        if m:
            # if no catching group, store the band files with the key 'all'
            # which means that all bands are in the file.
            key = m.group("bands") if "bands" in band_regexp.groupindex else 'all'
            bands_files[key] = f"{rootpath}{inputfile.joinpath(name).as_posix()}"

        elif has_mask:
            m = mask_regexp.match(name)
            if m:
                key = m.group("bands") if "bands" in mask_regexp.groupindex else 'all'
                masks_files[key] = f"{rootpath}{inputfile.joinpath(name).as_posix()}"

    return bands_files, masks_files


def _extract_bands_from_dir(inputfile: Path,
                            bands_pattern: str,
                            masks_pattern: str = None) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Extracts the bands from an uncompressed archive (i.e. a dir)

    Args:
        inputfile (Path):
            Archive product that contains the raster bands
        bands_pattern (str):
            Pattern to identify the bands files in the product.
        mask_pattern (str):
            Pattern to identify the masks files in the product if any.

    Returns:
        (dict, dict): List of the bands and masks files indexed by their identifier
    """
    bands_files = {}
    masks_files = {}

    band_regexp = re.compile(bands_pattern)
    has_mask = masks_pattern is not None
    mask_regexp = re.compile(masks_pattern) if has_mask else None

    # the archive may have been extracted, find files in it
    for path in inputfile.glob("**/*"):
        if path.is_file():
            m = band_regexp.match(path.name)
            if m:
                key = m.group("bands") if "bands" in band_regexp.groupindex else 'all'
                bands_files[key] = path.as_posix()

            elif has_mask:
                m = mask_regexp.match(path.name)
                if m:
                    key = m.group("bands") if "bands" in band_regexp.groupindex else 'all'
                    masks_files[key] = path.as_posix()

    return bands_files, masks_files
