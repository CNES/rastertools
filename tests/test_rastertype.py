#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import json
from pathlib import Path
from datetime import datetime
from eolab.rastertools import add_custom_rastertypes
from eolab.rastertools.product import RasterType, BandChannel
from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


def test_rastertype_valid_parameters():
    # S2 L1C
    files = ["S2A_MSIL1C_20170105T013442_N204_R031_T53NMJ_20170105T013443.zip",
             "S2B_MSIL1C_20170105T013442_N204_R031_T53NMJ_20170105T013443.tar",
             Path("../S2A_MSIL1C_20170105T013442_N204_R031_T53NMJ_20170105T013443.SAFE"),
             Path("/home/data/S2B_MSIL1C_20170105T013442_N204_R031_T53NMJ_20170105T013443")]
    results = [RasterType.find(file).name for file in files]
    expected_results = ["S2_L1C"] * 4
    assert results == expected_results

    # S2 L2A SEN2CORE
    files = [Path("S2B_MSIL2A_20190627T104029_N0212_R008_T31TDJ_20190627T135004.zip"),
             Path("S2A_MSIL2A_20190627T104029_N0212_R008_T31TDJ_20190627T135004.tar"),
             "../S2B_MSIL2A_20190627T104029_N0212_R008_T31TDJ_20190627T135004.SAFE",
             "/home/data/S2B_MSIL2A_20190627T104029_N0212_R008_T31TDJ_20190627T135004"]
    results = [RasterType.find(file).name for file in files]
    expected_results = ["S2_L2A_SEN2CORE"] * 4
    assert results == expected_results

    # S2 L2A MAJA
    files = ["SENTINEL2B_20191025-104903-761_L2A_T31TCJ_D.zip",
             "SENTINEL2A_20191025-104903-761_L2A_T31TCJ_D.tar",
             Path("../SENTINEL2B_20191025-104903-761_L2A_T31TCJ_D_V1-9"),
             Path("/home/data/SENTINEL2A_20191025-104903-761_L2A_T31TCJ_D_V1-9")]
    results = [RasterType.find(file).name for file in files]
    expected_results = ["S2_L2A_MAJA"] * 4
    assert results == expected_results

    # S2 L3A THEIA
    files = ["SENTINEL2X_20191025-104903-761_L3A_T31TCJ_D.zip",
             "SENTINEL2X_20191025-104903-761_L3A_T31TCJ_D.tar",
             Path("../SENTINEL2X_20191025-104903-761_L3A_T31TCJ_D_V1-9"),
             Path("/home/data/SENTINEL2X_20191025-104903-761_L3A_T31TCJ_D_V1-9")]
    results = [RasterType.find(file).name for file in files]
    expected_results = ["S2_L3A_THEIA"] * 4
    assert results == expected_results

    # SPOT67 GEOSUD
    files = ["SPOT6_2018_France-Brute_NC_DRS-MS_SPOT6_2018_FRANCE_BRUT_NC_GEOSUD_MS_138.tar.gz",
             "SPOT6_2018_France-Ortho_NC_DRS-MS_SPOT6_2018_FRANCE_ORTHO_NC_GEOSUD_MS_138.tar.gz",
             Path("../SPOT6_2018_FRANCE_ORTHO_NC_GEOSUD_MS_138"),
             Path("/home/data/SPOT6_2018_FRANCE_BRUT_NC_GEOSUD_MS_138")]
    results = [RasterType.find(file).name for file in files]
    expected_results = ["SPOT67_GEOSUD"] * 4
    assert results == expected_results

    # invalid files
    files = ["unexpected_name",
             Path("/home/unexpected_rep/strange_name")]
    results = [RasterType.find(file) for file in files]
    expected_results = [None] * 2
    assert results == expected_results


def test_rastertype_parse_errors():
    file = Path("SENTINEL2B_2019102-5104903-761_L2A_T31TCJ_D.zip")
    prod_type = RasterType.find(file)
    with pytest.raises(ValueError):
        prod_type.get_date(file)

    assert prod_type.get_date("SENTINEL2B_2019104903.zip") is None


def test_rastertype_invalid_parameters():
    assert RasterType.find(None) is None
    assert RasterType.get("S2_L1C").get_date(None) is None
    assert RasterType.get("S2_L1C").has_channel(None) is False
    assert RasterType.get("S2_L1C").has_channels(None) is False
    assert RasterType.get("S2_L1C").has_channels(list()) is False
    assert RasterType.get("S2_L1C").get_band_id(None) is None
    assert RasterType.get("S2_L1C").get_date(None) is None
    assert RasterType.get("S2_L1C").has_channels(None) is False
    with pytest.raises(ValueError):
        RasterType.get("S2_L2A_MAJA").get_bands_regexp([BandChannel.blue, BandChannel.blue_60m])


def test_rastertype_S2_L1C():
    file = "S2A_MSIL1C_20170105T013442_N204_R031_T53NMJ_20170105T013443.zip"

    s2_l1c = RasterType.find(file)
    assert s2_l1c.name == "S2_L1C"

    assert s2_l1c.get_date(file) == datetime(2017, 1, 5, 1, 34, 42)
    assert s2_l1c.get_group(file, "relorbit") == "031"
    assert s2_l1c.get_group(file, "tile") == "53NMJ"
    assert s2_l1c.get_group(file, "satellite") == "S2A"

    bands = [BandChannel.blue, BandChannel.green, BandChannel.red]
    regexp = r"^.*_[0-9T]*_(?P<bands>B02|B03|B04)\.jp2$"
    assert s2_l1c.get_bands_regexp(bands) == regexp
    regexp = r"^.*_[0-9T]*_(?P<bands>B02|B03|B04|B08|B11|B12|B05|B06|B07|B8A|B01|B09|B10)\.jp2$"
    assert s2_l1c.get_bands_regexp(None) == regexp
    assert s2_l1c.get_mask_regexp() is None

    assert s2_l1c.has_channel(BandChannel.blue)
    assert s2_l1c.has_channel(BandChannel.green)
    assert s2_l1c.has_channel(BandChannel.red)
    assert s2_l1c.has_channel(BandChannel.nir)
    assert s2_l1c.has_channel(BandChannel.mir)
    assert s2_l1c.has_channel(BandChannel.swir)
    assert s2_l1c.has_channels([BandChannel.red_edge1,
                                BandChannel.red_edge2,
                                BandChannel.red_edge3,
                                BandChannel.red_edge4])
    assert s2_l1c.has_channels([BandChannel.blue_60m,
                                BandChannel.nir_60m,
                                BandChannel.mir_60m])

    channels = [BandChannel.blue,
                BandChannel.green,
                BandChannel.red,
                BandChannel.nir,
                BandChannel.mir,
                BandChannel.swir,
                BandChannel.red_edge1,
                BandChannel.red_edge2,
                BandChannel.red_edge3,
                BandChannel.red_edge4]
    ids = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12', 'B05', 'B06', 'B07', 'B8A']
    assert [s2_l1c.get_band_id(c) for c in channels] == ids

    channels = [BandChannel.blue_60m,
                BandChannel.nir_60m,
                BandChannel.mir_60m]
    assert [s2_l1c.get_band_id(c) for c in channels] == ['B01', 'B09', 'B10']

    assert s2_l1c.has_mask() is False
    assert len(s2_l1c.get_mask_ids()) == 0


def test_rastertype_S2_L2A_SEN2CORE():
    file = Path("S2B_MSIL2A_20190627T104029_N0212_R008_T31TDJ_20190627T135004.zip")

    s2_l2a = RasterType.find(file)
    assert s2_l2a.name == "S2_L2A_SEN2CORE"

    assert s2_l2a.get_date(file) == datetime(2019, 6, 27, 10, 40, 29)
    assert s2_l2a.get_group(file, "relorbit") == "008"
    assert s2_l2a.get_group(file, "tile") == "31TDJ"
    assert s2_l2a.get_group(file, "satellite") == "S2B"

    bands = [BandChannel.blue, BandChannel.green, BandChannel.red]
    regexp = r"^.*_[0-9T]*_(?P<bands>B02_10m|B03_10m|B04_10m)\.jp2$"
    assert s2_l2a.get_bands_regexp(bands) == regexp
    assert s2_l2a.get_mask_regexp() is None

    assert s2_l2a.has_channel(BandChannel.blue)
    assert s2_l2a.has_channel(BandChannel.green)
    assert s2_l2a.has_channel(BandChannel.red)
    assert s2_l2a.has_channel(BandChannel.nir)
    assert s2_l2a.has_channel(BandChannel.mir)
    assert s2_l2a.has_channel(BandChannel.swir)
    assert s2_l2a.has_channels([BandChannel.red_edge1,
                                BandChannel.red_edge2,
                                BandChannel.red_edge3,
                                BandChannel.red_edge4])
    assert s2_l2a.has_channels([BandChannel.blue_60m,
                                BandChannel.nir_60m])
    assert s2_l2a.has_channel(BandChannel.mir_60m) is False

    channels = [BandChannel.blue,
                BandChannel.green,
                BandChannel.red,
                BandChannel.nir,
                BandChannel.mir,
                BandChannel.swir,
                BandChannel.red_edge1,
                BandChannel.red_edge2,
                BandChannel.red_edge3,
                BandChannel.red_edge4]
    ids = ['B02_10m', 'B03_10m', 'B04_10m', 'B08_10m',
           'B11_20m', 'B12_20m', 'B05_20m', 'B06_20m', 'B07_20m', 'B8A_20m']
    assert [s2_l2a.get_band_id(c) for c in channels] == ids

    channels = [BandChannel.blue_60m,
                BandChannel.nir_60m,
                BandChannel.mir_60m]
    assert [s2_l2a.get_band_id(c) for c in channels] == ['B01_60m', 'B09_60m', None]

    assert s2_l2a.has_mask() is False
    assert len(s2_l2a.get_mask_ids()) == 0


def test_rastertype_S2_L2A_MAJA():
    file = Path("SENTINEL2B_20191025-104903-761_L2A_T31TCJ_D.zip")

    s2_l2a = RasterType.find(file)
    assert s2_l2a.name == "S2_L2A_MAJA"

    assert s2_l2a.maskfunc == "eolab.rastertools.product.s2_maja_mask"
    assert s2_l2a.get_date(file) == datetime(2019, 10, 25, 10, 49, 3)
    assert s2_l2a.get_group(file, "tile") == "31TCJ"
    assert s2_l2a.get_group(file, "satellite") == "SENTINEL2B"

    bands = [BandChannel.blue, BandChannel.green, BandChannel.red]
    regexp = r"^SENTINEL2.*_(?P<bands>FRE_B2|FRE_B3|FRE_B4)\.(tif|TIF|vrt|VRT)$"
    assert s2_l2a.get_bands_regexp(bands) == regexp
    regexp = r"^SENTINEL2.*_(?P<bands>CLM_R1|SAT_R1|EDG_R1)\.(tif|TIF|vrt|VRT)$"
    assert s2_l2a.get_mask_regexp() == regexp

    assert s2_l2a.has_channel(BandChannel.blue)
    assert s2_l2a.has_channel(BandChannel.green)
    assert s2_l2a.has_channel(BandChannel.red)
    assert s2_l2a.has_channel(BandChannel.nir)
    assert s2_l2a.has_channel(BandChannel.mir)
    assert s2_l2a.has_channel(BandChannel.swir)
    assert s2_l2a.has_channels([BandChannel.red_edge1,
                                BandChannel.red_edge2,
                                BandChannel.red_edge3,
                                BandChannel.red_edge4])
    assert s2_l2a.has_channel(BandChannel.blue_60m) is False
    assert s2_l2a.has_channel(BandChannel.nir_60m) is False
    assert s2_l2a.has_channel(BandChannel.mir_60m) is False

    channels = [BandChannel.blue,
                BandChannel.green,
                BandChannel.red,
                BandChannel.nir,
                BandChannel.mir,
                BandChannel.swir,
                BandChannel.red_edge1,
                BandChannel.red_edge2,
                BandChannel.red_edge3,
                BandChannel.red_edge4]
    ids = ['FRE_B2', 'FRE_B3', 'FRE_B4', 'FRE_B8',
           'FRE_B11', 'FRE_B12', 'FRE_B5', 'FRE_B6', 'FRE_B7', 'FRE_B8A']
    assert [s2_l2a.get_band_id(c) for c in channels] == ids

    channels = [BandChannel.blue_60m,
                BandChannel.nir_60m,
                BandChannel.mir_60m]
    assert [s2_l2a.get_band_id(c) for c in channels] == [None, None, None]

    assert s2_l2a.has_mask()
    assert s2_l2a.get_mask_ids() == ["CLM_R1", "SAT_R1", "EDG_R1"]
    assert s2_l2a.get_mask_descriptions() == ["CLM_R1", "SAT_R1", "EDG_R1"]


def test_rastertype_S2_L3A_THEIA():
    file = Path("SENTINEL2X_20191025-104903-761_L3A_T31TCJ_D.zip")

    s2_l3a = RasterType.find(file)
    assert s2_l3a.name == "S2_L3A_THEIA"

    assert s2_l3a.get_date(file) == datetime(2019, 10, 25, 10, 49, 3)
    assert s2_l3a.get_group(file, "tile") == "31TCJ"
    assert s2_l3a.get_group(file, "satellite") == "SENTINEL2X"

    bands = [BandChannel.blue, BandChannel.green, BandChannel.red]
    regexp = r"^SENTINEL2.*_(?P<bands>FRC_B2|FRC_B3|FRC_B4)\.(tif|TIF|vrt|VRT)$"
    assert s2_l3a.get_bands_regexp(bands) == regexp

    assert s2_l3a.has_channel(BandChannel.blue)
    assert s2_l3a.has_channel(BandChannel.green)
    assert s2_l3a.has_channel(BandChannel.red)
    assert s2_l3a.has_channel(BandChannel.nir)
    assert s2_l3a.has_channel(BandChannel.mir)
    assert s2_l3a.has_channel(BandChannel.swir)
    assert s2_l3a.has_channels([BandChannel.red_edge1,
                                BandChannel.red_edge2,
                                BandChannel.red_edge3,
                                BandChannel.red_edge4])
    assert s2_l3a.has_channel(BandChannel.blue_60m) is False
    assert s2_l3a.has_channel(BandChannel.nir_60m) is False
    assert s2_l3a.has_channel(BandChannel.mir_60m) is False

    channels = [BandChannel.blue,
                BandChannel.green,
                BandChannel.red,
                BandChannel.nir,
                BandChannel.mir,
                BandChannel.swir,
                BandChannel.red_edge1,
                BandChannel.red_edge2,
                BandChannel.red_edge3,
                BandChannel.red_edge4]
    ids = ['FRC_B2', 'FRC_B3', 'FRC_B4', 'FRC_B8',
           'FRC_B11', 'FRC_B12', 'FRC_B5', 'FRC_B6', 'FRC_B7', 'FRC_B8A']
    assert [s2_l3a.get_band_id(c) for c in channels] == ids

    channels = [BandChannel.blue_60m,
                BandChannel.nir_60m,
                BandChannel.mir_60m]
    assert [s2_l3a.get_band_id(c) for c in channels] == [None, None, None]

    assert s2_l3a.has_mask() is False
    assert len(s2_l3a.get_mask_ids()) == 0


def test_rastertype_SPOT67():
    file = Path("SPOT6_2018_France-Brute_NC_DRS-MS_SPOT6_2018_FRANCE_BRUT_NC_GEOSUD_MS_138.tar.gz")

    spot67 = RasterType.find(file)
    assert spot67.name == "SPOT67_GEOSUD"

    assert spot67.get_date(file) is None
    assert spot67.get_group(file, "satellite") == "SPOT6"

    bands = [BandChannel.blue, BandChannel.green, BandChannel.red]
    regexp = r"^.*IMG_SPOT._MS_.*\.(tif|TIF)$"
    assert spot67.get_bands_regexp(bands) == regexp
    assert spot67.get_mask_regexp() is None

    assert spot67.has_channel(BandChannel.blue)
    assert spot67.has_channel(BandChannel.green)
    assert spot67.has_channel(BandChannel.red)
    assert spot67.has_channel(BandChannel.nir)
    assert spot67.has_channel(BandChannel.mir) is False
    assert spot67.has_channel(BandChannel.swir) is False
    assert spot67.has_channels([BandChannel.red_edge1,
                                BandChannel.red_edge2,
                                BandChannel.red_edge3,
                                BandChannel.red_edge4,
                                BandChannel.blue_60m,
                                BandChannel.nir_60m,
                                BandChannel.mir_60m]) is False

    channels = [BandChannel.blue,
                BandChannel.green,
                BandChannel.red,
                BandChannel.nir,
                BandChannel.mir,
                BandChannel.swir,
                BandChannel.red_edge1,
                BandChannel.red_edge2,
                BandChannel.red_edge3,
                BandChannel.red_edge4,
                BandChannel.blue_60m,
                BandChannel.nir_60m,
                BandChannel.mir_60m]
    for channel in channels:
        assert spot67.get_band_id(channel) is None

    assert spot67.has_mask() is False
    assert len(spot67.get_mask_ids()) == 0


def test_rastertype_additional():
    file = utils4test.indir + "additional_rastertypes.json"

    with open(file) as json_content:
        RasterType.add(json.load(json_content))

    file = "RGB_TIF_20170105_013442_test.tif"

    rgbtif = RasterType.find(file)
    assert rgbtif.name == "RGB_TIF"

    assert rgbtif.get_date(file) == datetime(2017, 1, 5, 1, 34, 42)

    bands = [BandChannel.blue, BandChannel.green, BandChannel.red]
    assert rgbtif.get_bands_regexp(bands) is None
    assert rgbtif.get_mask_regexp() is None

    assert rgbtif.has_channel(BandChannel.blue)
    assert rgbtif.has_channel(BandChannel.green)
    assert rgbtif.has_channel(BandChannel.red)


def test_rastertype_additional2():
    json = {
        "rastertypes": [
            {
                "name": "RGB_TIF",
                "product_pattern": "^RGB_TIF_(?P<date>[0-9_]*)_test\\.(tif|TIF)$",
                "bands": [
                    {
                        "channel": "red",
                        "description": "red"
                    },
                    {
                        "channel": "green",
                        "description": "green"
                    },
                    {
                        "channel": "blue",
                        "description": "blue"
                    },
                    {
                        "channel": "nir",
                        "description": "nir"
                    }
                ],
                "date_format": "%Y%m%d_%H%M%S",
                "nodata": 0
            },
            {
                "name": "RGB_TIF_ARCHIVE",
                "product_pattern": "^RGB_TIF_(?P<date>[0-9\\_]*).*$",
                "bands_pattern": "^TIF_(?P<bands>{}).*\\.(tif|TIF)$",
                "bands": [
                    {
                        "channel": "red",
                        "identifier": "r",
                        "description": "red"
                    },
                    {
                        "channel": "green",
                        "identifier": "g",
                        "description": "green"
                    },
                    {
                        "channel": "blue",
                        "identifier": "b",
                        "description": "blue"
                    },
                    {
                        "channel": "nir",
                        "identifier": "n",
                        "description": "nir"
                    }
                ],
                "date_format": "%Y%m%d_%H%M%S",
                "nodata": 0
            }
        ]
    }

    add_custom_rastertypes(json)

    file = "RGB_TIF_20170105_013442_test.tif"

    rgbtif = RasterType.find(file)
    assert rgbtif.name == "RGB_TIF"

    assert rgbtif.get_date(file) == datetime(2017, 1, 5, 1, 34, 42)

    bands = [BandChannel.blue, BandChannel.green, BandChannel.red]
    assert rgbtif.get_bands_regexp(bands) is None
    assert rgbtif.get_mask_regexp() is None

    assert rgbtif.has_channel(BandChannel.blue)
    assert rgbtif.has_channel(BandChannel.green)
    assert rgbtif.has_channel(BandChannel.red)

    assert rgbtif.get_band_descriptions() == ['red', 'green', 'blue', 'nir']
