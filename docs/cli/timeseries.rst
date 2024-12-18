.. timeseries:

timeseries
----------

``timeseries`` (or ``ts``) generates a series of rasters at given dates from a set of input rasters
of the same type. When input rasters contain gaps (due for instance to clouds), gaps are filled in 
the generated rasters.

To generate the timeseries, this tool uses linear interpolation of every pixels in the input rasters.

If some of the requested dates are before (resp. after) the dates of the input rasters, the
corresponding generated raster will contain the raster values of the first (resp. last) input raster
and may thus contain the same gaps as the input raster.

.. code-block:: console

  $ georastertools timeseries --help

  usage: georastertools timeseries [-h] [-b BANDS [BANDS ...]] [-a] [-o OUTPUT]
                                [-s START_DATE] [-e END_DATE] [-p TIME_PERIOD]
                                [-ws WINDOW_SIZE]
                                inputs [inputs ...]

  Generate a timeseries of images (without gaps) from a set of input images.
  Data not present in the input images (e.g., missing images for specific
  dates or masked data) are interpolated (with linear interpolation) so that
  all gaps in the timeseries are filled.

  This command is useful for generating continuous timeseries data, even when
  some input images are missing or contain masked values.

  Arguments:

      inputs TEXT

          Input file to process (e.g. Sentinel2 L2A MAJA from THEIA). You can
          provide a single file with extension ".lst" (e.g. "speed.lst") that
          lists the input files to process (one input file per line in .lst).

  Options:
      -b, --bands LIST            List of bands to process
      -a, --all                   Process all bands
      -o, --output TEXT           Output directory to store results (by default
                                  current directory)
      -s, --start_date TEXT       Start date of the timeseries to generate in the
                                  following format: yyyy-MM-dd
      -e, --end_date TEXT         End date of the timeseries to generate in the
                                  following format: yyyy-MM-dd
      -p, --time_period INTEGER   Time period (number of days) between two
                                  consecutive images in the timeseries to generate
                                  e.g. 10 = generate one image every 10 days
      -ws, --window_size INTEGER  Size of tiles to distribute processing, default:
                                  1024
      -h, --help                  Show this message and exit.


.. warning::
  At least two input rasters must be given. The rasters must match one of the configured raster types,
  either a built-in raster type or a custom raster type defined with option -t of ``georastertools``.
  See section "Raster types". The raster type must define where to get the date of the product
  in the filename.

Example:

.. code-block:: console

  $ georastertools timeseries ./SENTINEL2A_20180521-105702-711_L2A_T30TYP_D-ndvi.zip ./SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif -s 2018-05-21 -e 2018-10-25 -p 10 -ws 512

This command generates rasters from 2018-05-21 until 2018-10-25 with a timeperiod between
two consecutive images of 10 days (2018-05-21, 2018-05-31, 2018-06-10, ...).
