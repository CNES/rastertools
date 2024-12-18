.. _usage:

.. currentmodule:: eolab.georastertools

=============
API Reference
=============

georastertools
-----------

georastertools can be activated by calling the API :obj:`eolab.georastertools.run_tool`.

.. autofunction:: run_tool

Example of use in python code::

    from eolab.georastertools import run_tool
    run_tool(args="radioindice --help".split())

Alternatively, every raster tools can be activated with their own API:

.. autosummary::
  :toctree: api/

  Filtering
  Hillshade
  Radioindice
  Speed
  SVF
  Tiling
  Timeseries
  Zonalstats

All these objects provide:

- a fluent API to configure the processing. The methods are all named with the following pattern "with_<something>" and
  return the current instance so that the methods can be chained.
- methods to process a single file or a set of files (see :obj:`eolab.georastertools.Rastertool.process_file`
  and :obj:`eolab.georastertools.Rastertool.process_files`)

Example of use::

    from eolab.georastertools import Radioindice
    proc = Radioindice(Radioindice.ndvi)
    outputs = proc.with_output(".", merge=False)
                  .with_roi("./roi.geojson")
                  .process_file("./SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip")
    print(outputs)

Raster products
---------------

georastertools provides a useful API to open raster products that are provided as an archive or a directory containing
several images.

The API is very simple to use::

   from eolab.georastertools.product import RasterProduct
   import rasterio

   with RasterProduct("tests/tests_data/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip") as rp:
      with rasterio.Env(GDAL_VRT_ENABLE_PYTHON=True):
         with rp.open(roi="tests/tests_data/COMMUNE_32001.shp") as dataset:
            data = dataset.read([1, 2, 3], masked=True)

Adding custom raster types
--------------------------

To add custom raster types, use the method :obj:`eolab.georastertools.add_custom_rastertypes`.

.. autofunction:: add_custom_rastertypes

Example of use::

    from eolab.georastertools import add_custom_rastertypes

    my_rastertypes = {
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

    # now any georastertools can handle products of the two new rastertypes
    ...

Design rules of raster tools
----------------------------

Every raster tool object inherits from base class :obj:`eolab.georastertools.Rastertool`.
If the process supports windowing, the raster tool can also inherit from :obj:`eolab.georastertools.Windowable`.

.. autosummary::
  :toctree: api/

  Rastertool
  Windowable

A rastertool raises a :obj:`eolab.georastertools.RastertoolConfigurationException` when invalid
input parameter is provided.

.. autosummary::
  :toctree: api/

  RastertoolConfigurationException

Moreover, a rastertool can raise any type of Exception during its execution. The best practice is
thus to catch exceptions that can raise as follows::

    from eolab.georastertools import Radioindice, RastertoolConfigurationException

    proc = Radioindice(Radioindice.ndvi)
    try:
        outputs = proc.with_output("unknown_dir", merge=False)
                      .process_file("./SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip")
    except RastertoolConfigurationException as rce:
        # do something
        print(f"Invalid configuration of radioindice processing: {rce}")
    except Exception as err:
        # do something
        print(f"An unexpected error occurs while processing file: {err}")

In this example, a RastertoolConfigurationException is raises because the specified output dir does not
exist.
