.. _rasterproduct:

============
Raster types
============

Some of the **rastertools** can only handle input raster files of a recognized raster type.

This concerns ``radioindice``, ``speed`` and also ``zonalstats`` when this latter is asked to plot the statistics. 
In these 3 cases, the tool needs to know the available raster bands (``radioindice``) or to extract the
timestamp of the raster product (``speed``, ``zonalstats``): the tools use the description of the raster type
to retrieve this information.

The other tools are more flexible and also accept input rasters of unknown type provided that the input raster
can be read by rasterio.

.. note::
  Tools like ``radioindice`` and ``zonalstats`` generate output filenames that follow the naming convention defined
  in the rastertype of the input raster products. For instance, an NDVI generated from a Sentinel-2 L1C product
  will be named so that the NDVI output file will be recognized as a Sentinel-2 L1C product. The timestamp of the
  NDVI can thus be extracted by ``speed`` or ``zonalstats`` if they are chained after ``radioindice``.

Built-in raster types
---------------------

**rastertools** has several built-in raster types:

.. list-table:: Built-in raster types
   :widths: 20 20 15 15 15 15
   :header-rows: 1

   * - Name
     - Naming convention
     - Pattern to identify raster bands
     - Date format
     - Mask function
     - Nodata
   * - Sentinel-2 L2A THEIA
     - ^SENTINEL2._(?P<date>[0-9\-]{15}).*_L2A_T(?P<tile>.*)_.*$
     - ^SENTINEL2.*_(?P<bands>{})\.(tif|TIF|vrt|VRT)$
     - %Y%m%d-%H%M%S
     - eolab.rastertools.product.vrt.s2_maja_mask
     - -10000
   * - Sentinel-2 L3A THEIA
     - ^SENTINEL2X_(?P<date>[0-9\-]{15}).*_L3A_T(?P<tile>.*)_.*$
     - ^SENTINEL2.*_(?P<bands>{})\.(tif|TIF|vrt|VRT)$
     - %Y%m%d-%H%M%S
     - No mask
     - -10000
   * - Sentinel-2 L1C PEPS
     - ^S2._MSIL1C_(?P<date>[0-9T]*)_N\d*_R(?P<relorbit>\d*)_T(?P<tile>.*)_.*$
     - ^.*_[0-9T]*_(?P<bands>{})\.jp2$
     - %Y%m%dT%H%M%S
     - No mask
     - 0
   * - Sentinel-2 L2A PEPS
     - ^S2._MSIL2A_(?P<date>[0-9T]*)_N\d*_R(?P<relorbit>\d*)_T(?P<tile>.*)_.*$
     - ^.*_[0-9T]*_(?P<bands>{})\.jp2$
     - %Y%m%dT%H%M%S
     - No mask
     - 0
   * - SPOT6/7
     - ^SPOT._[0-9]{4}_.*_GEOSUD_MS_.*$
     - ^.*IMG_SPOT._MS_.*\.(tif|TIF)$
     - No timestamp in product name
     - No mask
     - -10000

Add custom raster types
-----------------------

**rastertools** CLI has a special argument ``-t`` that allows to define custom raster types. This argument must
be set with the path to a JSON file that contains the new raster types definitions.

The structure of the JSON file is described in :obj:`eolab.rastertools.add_custom_rastertypes`
