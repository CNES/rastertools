.. radioindice:

radioindice
-----------

``radioindice`` (or ``ri``) subcommand computes radiometric indices such as ndvi or ndwi.

.. code-block:: console

  $ rastertools radioindice --help
  usage: rastertools radioindice [-h] [-o OUTPUT] [-m] [-r ROI]
                                 [-i INDICES [INDICES ...]] [--ndvi] [--tndvi]
                                 [--rvi] [--pvi] [--savi] [--tsavi] [--msavi]
                                 [--msavi2] [--ipvi] [--evi] [--ndwi] [--ndwi2]
                                 [--mndwi] [--ndpi] [--ndti] [--ndbi] [--ri]
                                 [--bi] [--bi2] [-nd band1 band2]
                                 [-ws WINDOW_SIZE]
                                 inputs [inputs ...]
  
  Compute a list of radiometric indices (NDVI, NDWI, etc.) on a raster image
  
  positional arguments:
    inputs                Input file to process (e.g. Sentinel2 L2A MAJA from
                          THEIA). You can provide a single file with extension
                          ".lst" (e.g. "radioindice.lst") that lists the input
                          files to process (one input file per line in .lst)
  
  optional arguments:
    -h, --help            show this help message and exit
    -o OUTPUT, --output OUTPUT
                          Output dir where to store results (by default current
                          dir)
    -m, --merge           Merge all indices in the same image (i.e. one band per
                          indice).
    -r ROI, --roi ROI     Region of interest in the input image (vector)
    -ws WINDOW_SIZE, --window_size WINDOW_SIZE
                          Size of tiles to distribute processing, default: 1024
  
  Options to select the indices to compute:
    -i INDICES [INDICES ...], --indices INDICES [INDICES ...]
                          List of indices to computePossible indices are: bi,
                          bi2, evi, ipvi, mndwi, msavi, msavi2, ndbi, ndpi,
                          ndti, ndvi, ndwi, ndwi2, pvi, ri, rvi, savi, tndvi,
                          tsavi
    --ndvi                Compute ndvi indice
    --tndvi               Compute tndvi indice
    --rvi                 Compute rvi indice
    --pvi                 Compute pvi indice
    --savi                Compute savi indice
    --tsavi               Compute tsavi indice
    --msavi               Compute msavi indice
    --msavi2              Compute msavi2 indice
    --ipvi                Compute ipvi indice
    --evi                 Compute evi indice
    --ndwi                Compute ndwi indice
    --ndwi2               Compute ndwi2 indice
    --mndwi               Compute mndwi indice
    --ndpi                Compute ndpi indice
    --ndti                Compute ndti indice
    --ndbi                Compute ndbi indice
    --ri                  Compute ri indice
    --bi                  Compute bi indice
    --bi2                 Compute bi2 indice
    -nd band1 band2, -normalized_difference band1 band2
                          Compute the normalized difference of two bands defined
                          as parameter of this option, e.g. "-nd red nir" will
                          compute (red-nir)/(red+nir). See
                          eolab.rastertools.product.rastertype.BandChannel for
                          the list of bands names. Several nd options can be set
                          to compute several normalized differences.
  
  If no indice option is explicitly set, NDVI, NDWI and NDWI2 are computed.

.. warning::
  ``radioindice`` only accepts input files that match one of the configured raster types, either a built-in raster type
  or a custom raster type defined with option -t of ``rastertools``. See section "Raster types".

Examples :

The first command computes the NDVI of a Sentinel-2 L2A product. The computation is performed on a region of interest defined
by a shapefile. The NDVI is then computed on a subset of the input product.

Let's have a look of the Sentinel-2 L2A product in false color (Green, Red, NIR). The region of interest is highlighted with
a black line.

.. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-grn.jpg

.. code-block:: console

  $ rastertools radioindice -r "./COMMUNE_32001.shp" --ndvi ./SENTINEL2A_20180521-105702-711_L2A_T30TYP_D.zip

The generated NDVI image is:

.. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi_cropped.jpg

The second command computes two indices (NDVI and NDWI) of the same input image. No region of interest is configured.

.. code-block:: console
  
  $ rastertools radioindice -i ndvi ndwi -m ./SENTINEL2A_20180521-105702-711_L2A_T30TYP_D.zip

The generated image has two bands (because option -m is activated): first one is the ndvi, second one is the ndwi. If -m option
is not activated, two images would be generated, one image per indice.

Here is a capture of the first band (ndvi):

.. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.jpg
