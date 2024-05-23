#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Model for raster product enabling to extract bands, timestamp, etc.
"""

from typing import List, Dict, Union
import re
from datetime import datetime
from enum import Enum
from pathlib import Path

from eolab.rastertools import utils

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


class BandChannel(Enum):
    """Defines the band channel of a raster product
    """
    blue = "blue"
    green = "green"
    red = "red"
    nir = "nir"
    mir = "mir"
    swir = "swir"

    # specific to S2 products
    red_edge1 = "red_edge1"
    red_edge2 = "red_edge2"
    red_edge3 = "red_edge3"
    red_edge4 = "red_edge4"
    blue_60m = "blue_60m"
    nir_60m = "nir_60m"
    mir_60m = "mir_60m"


class Band:
    """Definition of a band: its identifier in the product's name pattern and its description
    """

    def __init__(self, identifier: str, description: str = None):
        self._identifier = identifier
        self._description = description or identifier

    def __repr__(self):
        return f"Band {self._identifier}"

    @property
    def identifier(self):
        """String that enables to identify the band in a raster product"""
        return self._identifier

    @property
    def description(self):
        """Description of the band"""
        return self._description


class RasterType:
    """Raster type definition
    """

    # initialize rastertypes with the default ones defined in rastertypes.json
    rastertypes = dict()

    @staticmethod
    def get(name: str):
        """Get the raster type by its name"""
        return RasterType.rastertypes[name] if name in RasterType.rastertypes else None

    @staticmethod
    def find(file: Union[Path, str]):
        """Gets the raster type corresponding to the input file

        Args:
            file (Path or str):
                Product name or path to analyse

        Returns:
            :obj:`eolab.rastertools.product.RasterType`: the RasterType corresponding
            to the input file
        """
        return next((t for n, t in RasterType.rastertypes.items() if t.accept(file)), None)

    @staticmethod
    def add(rastertypes):
        """Add new raster types definitions from a json file

        Args:
            rastertypes (str): rastertypes description as JSON string

        Returns:
            [(str, tuple)]: List of rastertype's name and parameters. Parameters are
            provided as a tuple.
        """
        new_rastertypes = dict()
        for rt in rastertypes['rastertypes']:
            name = rt['name']
            product_pattern = rt['product_pattern']
            bands_pattern = rt['bands_pattern'] if "bands_pattern" in rt else None
            date_format = rt['date_format'] if "date_format" in rt else "%Y%m%d-%H%M%S"
            nodata = rt['nodata'] if "nodata" in rt else -10000
            maskfunc = rt['maskfunc'] if "maskfunc" in rt else None
            masknodata = rt['masknodata'] if "masknodata" in rt else 0
            bands = dict()
            for band in rt['bands']:
                channel = band['channel']
                identifier = band['identifier'] if "identifier" in band else None
                description = band['description'] if "description" in band else None
                bands[BandChannel[channel]] = Band(identifier, description)
            masks = list()
            if "masks" in rt:
                for mask in rt['masks']:
                    identifier = mask['identifier'] if "identifier" in mask else None
                    description = mask['description'] if "description" in mask else None
                    masks.append(Band(identifier, description))

            rt_tuple = (name, product_pattern, bands_pattern, bands, masks,
                        date_format, maskfunc, nodata, masknodata)
            new_rastertypes[name] = RasterType(*rt_tuple)

        # update the list of rastertypes with the new ones
        RasterType.rastertypes.update(new_rastertypes)

    def __init__(self, name: str,
                 product_pattern: str,
                 bands_pattern: str,
                 bands: Dict[BandChannel, Band],
                 masks: List[Band],
                 date_format: str = "%Y%m%d-%H%M%S",
                 maskfunc: str = None,
                 nodata: float = -10000,
                 masknodata: int = 1):
        """Constructor

        Args:
            name (str):
                Display name of the rastertype
            product_pattern (str):
                Pattern to identify a file corresponding to this RasterType
                The pattern can contain a capturing group corresponding to
                the product timestamp
            bands_pattern (str):
                Pattern to identify a band file in the product. The pattern can
                contain a capturing group corresponding to the bands' identifiers
                in case bands are separated in different files
            bands (dict(BandChannel, Band)):
                Dictionary associating the channel and the band definition for all available bands
            masks ([Band]):
                List of bands that define the masks of the product type
            date_format (str, optional, default="%Y%m%d-%H%M%S"):
                Date format ot the product timestamp (used to convert a string to datetime)
            maskfunc (str, optional, default=None):
                Name of the function to convert pixels of the band defined as the mask
                (typically the cloud mask) to boolean values.
            nodata (float, optional, default=-10000):
                No data value of the raster product
            masknodata (int, optional, default=1):
                No data value of the mask
        """
        self._name = name
        self._product_pattern = product_pattern
        self._bands_pattern = bands_pattern
        self._raster_bands = bands
        self._masks = masks or list()
        self._date_format = date_format
        self._maskfunc = maskfunc
        self._nodata = nodata
        self._masknodata = masknodata

    def __repr__(self):
        return f"{self.name}"

    @property
    def name(self):
        """Name of the raster type"""
        return self._name

    @property
    def product_pattern(self):
        """Pattern that enables to identify products of this rastertype"""
        return self._product_pattern

    @property
    def bands_pattern(self):
        """Pattern that enables to identify the bands in a product of this rastertype"""
        return self._bands_pattern

    @property
    def date_format(self):
        """Format of the date in the product's name"""
        return self._date_format

    @property
    def maskfunc(self):
        """Function that defines the mask of cloud from the raster band"""
        return self._maskfunc

    @property
    def nodata(self):
        """Nodata value"""
        return self._nodata

    @property
    def masknodata(self):
        """Nodata value of the mask"""
        return self._masknodata

    @property
    def channels(self) -> List[BandChannel]:
        """Gets the list of all available channels

        Returns:
            [:obj:`eolab.rastertools.product.BandChannel`]:
                List of available bands channels for this type of product
        """
        return list(self._raster_bands.keys())

    def accept(self, file: Union[Path, str]) -> bool:
        """Check if the file corresponds to this raster type

        Args:
            file (Path or str):
                Product name or path to analyse

        Returns:
            bool: True if the file matches this RasterType
        """
        accept = False
        if file is not None:
            filename = utils.to_path(file).name
            accept = re.match(self.product_pattern, filename) is not None
        return accept

    def get_date(self, file: Union[Path, str]) -> datetime:
        """Extracts the timestamp of the raster from the input file

        Args:
            file (Path or str):
                Product name or path to analyse

        Returns:
            :obj:`datetime.datetime`: Timestamp of the input file
        """
        datestr = self.get_group(file, 'date')
        return datetime.strptime(datestr, self.date_format) if datestr else None

    def get_group(self, file: Union[Path, str], group: str) -> str:
        """Extracts a group from the input file using the product pattern

        Args:
            file (Path or str):
                Product name or path to analyse
            group (str):
                Name of the group to extract

        Returns:
            str: Group extracted from the raster file
        """
        output = None
        if file is not None:
            regexp = re.compile(self.product_pattern)
            if group in regexp.groupindex:
                m = regexp.match(file.name if isinstance(file, Path) else file)
                if m:
                    output = m.group(group)
        return output

    def has_channel(self, channel: BandChannel) -> bool:
        """Checks if the product type contains the expected channel.

        Args:
            channel (:obj:`eolab.rastertools.product.BandChannel`):
                Band channel

        Returns:
            bool: True if this RasterType contain the channel
        """
        return channel in self._raster_bands

    def has_channels(self, channels: List[BandChannel]) -> bool:
        """Checks if the product type contains all the expected channels.

        Args:
            channels ([:obj:`eolab.rastertools.product.BandChannel`]):
                List of bands channels

        Returns:
            bool: True if this RasterType contains all channels
        """
        has_channels = False
        if channels is not None and len(channels) > 0:
            has_channels = all(channel in self._raster_bands for channel in channels)
        return has_channels

    def get_band_ids(self) -> List[str]:
        """Gets the bands identifiers.

        Returns:
            [str]: The bands ids
        """
        return [self._raster_bands[channel].identifier for channel in self.channels]

    def get_band_id(self, channel: BandChannel) -> str:
        """Gets the band identifier of the specified channel.

        Args:
            channel (:obj:`eolab.rastertools.product.BandChannel`):
                Band channel

        Returns:
            str: The band id if found, None otherwise
        """
        return self._raster_bands[channel].identifier if self.has_channel(channel) else None

    def get_band_descriptions(self) -> List[str]:
        """Gets the descriptions of the bands.

        Returns:
            str: The band description if found, None otherwise
        """
        return [self._raster_bands[channel].description for channel in self.channels]

    def get_band_description(self, channel: BandChannel) -> List[str]:
        """Gets the band description of the given channel.

        Args:
            channel (:obj:`eolab.rastertools.product.BandChannel`):
                Band channel

        Returns:
            str: The band description if found, None otherwise
        """
        return self._raster_bands[channel].description if self.has_channel(channel) else None

    def get_bands_regexp(self, channels: List[BandChannel] = None) -> str:
        """Gets the regexp to identify the bands in the product.

        Args:
            channels ([:obj:`eolab.rastertools.product.BandChannel`]):
                List of bands channels

        Returns:
            str: The regexp to identify the bands in the product
        """
        regexp = None

        if channels is None:
            channels = self.channels

        if self.bands_pattern is not None:
            if not self.has_channels(channels):
                raise ValueError(f"RasterType does not contain all the channels in {channels}")

            ids = [self.get_band_id(channel) for channel in channels]
            str_bands = '|'.join(ids) if len(ids) > 0 and None not in ids else ""
            regexp = self.bands_pattern.format(str_bands)
        return regexp

    def has_mask(self) -> bool:
        """Checks if the product type contains a mask.

        Returns:
            bool: True if this RasterType contains a mask
        """
        return len(self._masks) > 0

    def get_mask(self, mask_id: str) -> Band:
        """Gets the mask corresponding to the given id.

        Args:
            mask_id (str):
                Id of the mask

        Returns:
            Band: the mask corresponding to the given id, or None if no mask corresponds to
                  the id
        """
        selected_mask = None
        for mask in self._masks:
            if mask.identifier == mask_id:
                selected_mask = mask
        return selected_mask

    def get_mask_ids(self) -> List[str]:
        """Gets the identifier of the masks

        Returns:
            [str]: The identifiers of the masks if they are some, empty list otherwise
        """
        return [mask.identifier for mask in self._masks]

    def get_mask_descriptions(self) -> List[str]:
        """Gets the descriptions of the masks

        Returns:
            [str]: The descriptions of the masks if they are some, empty list otherwise
        """
        return [mask.description for mask in self._masks]

    def get_mask_regexp(self) -> str:
        """Gets the regexp to identify the masks

        Returns:
            str: The regexp to identify the masks
        """
        regexp = None
        if self.bands_pattern is not None and self.has_mask():
            ids = self.get_mask_ids()
            str_masks = '|'.join(ids) if len(ids) > 0 and None not in ids else ""
            regexp = self.bands_pattern.format(str_masks)
        return regexp
