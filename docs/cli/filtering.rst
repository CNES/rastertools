filter
------

``filter`` (or ``fi``) subcommand applies a convolutive filter on a a raster image.

.. code-block:: console

  $ rastertools filter --help
  usage: rastertools filter [-h] {median,sum,mean,adaptive_gaussian} ...
  
  Apply a filter to a set of images.
  
  optional arguments:
    -h, --help            show this help message and exit
  
  Filters:
    {median,sum,mean,adaptive_gaussian}
      median              Apply median filter
      sum                 Apply local sum filter
      mean                Apply local mean filter
      adaptive_gaussian   Apply adaptive gaussian filter

The available filters are Adaptive Gaussian, Local Sum, and Local Mean.
Each filter is used as a sub-command and has specific arguments for filtering.
To see the definitions of these arguments, type the option --help.

- **Median**

<<<<<<< HEAD
    .. code-block:: console
=======
  $ rastertools filter adaptive_gaussian --help
  usage: rastertools filter adaptive_gaussian [-h] --kernel_size KERNEL_SIZE
                                              --sigma SIGMA [-o OUTPUT]
                                              [-ws WINDOW_SIZE]
                                              [-p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}]
                                              [-b BANDS [BANDS ...]] [-a]
                                              inputs [inputs ...]

  Execute the requested filter on the input files with the specified
  parameters. The `inputs` argument can either be a single file or a `.lst`
  file containing a list of input files.

  Arguments:

      inputs TEXT

      Input file to process (e.g. Sentinel2 L2A MAJA from THEIA). You can
      provide a single file with extension ".lst" (e.g. "filtering.lst") that
      lists the input files to process (one input file per line in .lst).

  Options:
      --sigma INTEGER                 Standard deviation of the Gaussian
                                      distribution  [required]
      -a, --all                       Process all bands
      -b, --bands INTEGER             List of bands to process
      -p, --pad [none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap]
                                      Pad to use around the image, default : edge(see
                                      https://numpy.org/doc/stable/reference/generated/numpy.pad.html
                                      for more information)
      -ws, --window_size INTEGER      Size of tiles to distribute processing,
                                      default: 1024
      -o, --output TEXT               Output directory to store results (by
                                      default current directory)
      --kernel_size INTEGER           Kernel size of the filter function, e.g. 3
                                      means a square of 3x3 pixels on which the
                                      filter function is computed (default: 8)
      -h, --help                      Show this message and exit.

  Apply an adaptive (Local gaussian of 3x3) recursive filter on the input image

  positional arguments:
    inputs                Input file to process (e.g. Sentinel2 L2A MAJA from
                          THEIA). You can provide a single file with extension
                          ".lst" (e.g. "filtering.lst") that lists the input
                          files to process (one input file per line in .lst)

  optional arguments:
    -h, --help            show this help message and exit
    --kernel_size KERNEL_SIZE
                          Kernel size of the filter function, e.g. 3 means a
                          square of 3x3 pixels on which the filter function is
                          computed (default: 8)
    --sigma SIGMA         Standard deviation of the Gaussian distribution
                          (sigma)
    -o OUTPUT, --output OUTPUT
                          Output dir where to store results (by default current
                          dir)
    -ws WINDOW_SIZE, --window_size WINDOW_SIZE
                          Size of tiles to distribute processing, default: 1024
    -p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}, --pad {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}
                          Pad to use around the image, default : edge (see https
                          ://numpy.org/doc/stable/reference/generated/numpy.pad.
                          html for more information)
    -b BANDS [BANDS ...], --bands BANDS [BANDS ...]
                          List of bands to compute
    -a, --all             Compute all bands

  By default only first band is computed.
>>>>>>> rasterio_plugin_vsimem

      $ rastertools filter median --help
        usage: rastertools filter median [-h] --kernel_size KERNEL_SIZE [-o OUTPUT]
                                         [-ws WINDOW_SIZE]
                                         [-p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}]
                                         [-b BANDS [BANDS ...]] [-a]
                                         inputs [inputs ...]

        Apply a median filter (see scipy median_filter for more information)

        positional arguments:
          inputs                Input file to process (e.g. Sentinel2 L2A MAJA from
                                THEIA). You can provide a single file with extension
                                ".lst" (e.g. "filtering.lst") that lists the input
                                files to process (one input file per line in .lst)

        optional arguments:
          -h, --help            show this help message and exit
          --kernel_size KERNEL_SIZE
                                Kernel size of the filter function, e.g. 3 means a
                                square of 3x3 pixels on which the filter function is
                                computed (default: 8)
          -o OUTPUT, --output OUTPUT
                                Output dir where to store results (by default current
                                dir)
          -ws WINDOW_SIZE, --window_size WINDOW_SIZE
                                Size of tiles to distribute processing, default: 1024
          -p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}, --pad {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}
                                Pad to use around the image, default : edge (see https
                                ://numpy.org/doc/stable/reference/generated/numpy.pad.
                                html for more information)
          -b BANDS [BANDS ...], --bands BANDS [BANDS ...]
                                List of bands to compute
          -a, --all             Compute all bands

        By default only first band is computed.

    The corresponding API functions that is called by the command line interface is the following :

    .. autofunction:: eolab.rastertools.processing.algo.median


    Here is an example of a median filter applied to the NDVI of a SENTINEL2 L2A THEIA image cropped to a region of interest.
    This raster was previously computed using :ref:`radioindice` on the original SENTINEL2 L2A THEIA image.

    .. code-block:: console

     $ rastertools filter median --kernel_size 16 "./SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"

    .. list-table::
       :widths: 20 20
       :header-rows: 0

       * - .. centered:: Original
         - .. centered:: Filtered by Median

       * - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.jpg
            :align: center
         - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-median.jpg
            :align: center

- **Local sum**

    .. code-block:: console

      $ rastertools filter sum --help
        usage: rastertools filter sum [-h] --kernel_size KERNEL_SIZE [-o OUTPUT]
                                      [-ws WINDOW_SIZE]
                                      [-p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}]
                                      [-b BANDS [BANDS ...]] [-a]
                                      inputs [inputs ...]

        Apply a local sum filter using integral image method

        positional arguments:
          inputs                Input file to process (e.g. Sentinel2 L2A MAJA from
                                THEIA). You can provide a single file with extension
                                ".lst" (e.g. "filtering.lst") that lists the input
                                files to process (one input file per line in .lst)

        optional arguments:
          -h, --help            show this help message and exit
          --kernel_size KERNEL_SIZE
                                Kernel size of the filter function, e.g. 3 means a
                                square of 3x3 pixels on which the filter function is
                                computed (default: 8)
          -o OUTPUT, --output OUTPUT
                                Output dir where to store results (by default current
                                dir)
          -ws WINDOW_SIZE, --window_size WINDOW_SIZE
                                Size of tiles to distribute processing, default: 1024
          -p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}, --pad {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}
                                Pad to use around the image, default : edge (see https
                                ://numpy.org/doc/stable/reference/generated/numpy.pad.
                                html for more information)
          -b BANDS [BANDS ...], --bands BANDS [BANDS ...]
                                List of bands to compute
          -a, --all             Compute all bands

        By default only first band is computed.

    The corresponding API functions that is called by the command line interface is the following :

    .. autofunction:: eolab.rastertools.processing.algo.local_sum

    Here is an example of the local mean applied to the NDVI of a SENTINEL2 L2A THEIA image cropped to a region of interest.
    This raster was previously computed using :ref:`radioindice` on the original SENTINEL2 L2A THEIA image.

    .. code-block:: console

     $ rastertools filter sum --kernel_size 16 "./SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"

    .. list-table::
       :widths: 20 20
       :header-rows: 0

       * - .. centered:: Original
         - .. centered:: Filtered by Local sum

       * - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.jpg
            :align: center
         - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-sum.jpg
            :align: center

- **Local mean**

    .. code-block:: console

      $ rastertools filter mean --help
        usage: rastertools filter mean [-h] --kernel_size KERNEL_SIZE [-o OUTPUT]
                               [-ws WINDOW_SIZE]
                               [-p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}]
                               [-b BANDS [BANDS ...]] [-a]
                               inputs [inputs ...]

        Apply a local mean filter using integral image method

        positional arguments:
          inputs                Input file to process (e.g. Sentinel2 L2A MAJA from
                                THEIA). You can provide a single file with extension
                                ".lst" (e.g. "filtering.lst") that lists the input
                                files to process (one input file per line in .lst)

        optional arguments:
          -h, --help            show this help message and exit
          --kernel_size KERNEL_SIZE
                                Kernel size of the filter function, e.g. 3 means a
                                square of 3x3 pixels on which the filter function is
                                computed (default: 8)
          -o OUTPUT, --output OUTPUT
                                Output dir where to store results (by default current
                                dir)
          -ws WINDOW_SIZE, --window_size WINDOW_SIZE
                                Size of tiles to distribute processing, default: 1024
          -p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}, --pad {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}
                                Pad to use around the image, default : edge (see https
                                ://numpy.org/doc/stable/reference/generated/numpy.pad.
                                html for more information)
          -b BANDS [BANDS ...], --bands BANDS [BANDS ...]
                                List of bands to compute
          -a, --all             Compute all bands

        By default only first band is computed.


    The corresponding API functions that is called by the command line interface is the following :

    .. autofunction:: eolab.rastertools.processing.algo.local_mean


    Here is an example of the local mean applied to the NDVI of a SENTINEL2 L2A THEIA image cropped to a region of interest.
    This raster was previously computed using :ref:`radioindice` on the original SENTINEL2 L2A THEIA image.

    .. code-block:: console

     $ rastertools filter mean --kernel_size 16 "./SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"

    .. list-table::
       :widths: 20 20
       :header-rows: 0

       * - .. centered:: Original
         - .. centered:: Filtered by Local mean

       * - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.jpg
            :align: center
         - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-mean.jpg
            :align: center

- **Adaptative gaussian**

    .. code-block:: console

      $ rastertools filter adaptive_gaussian --help
      usage: rastertools filter adaptive_gaussian [-h] --kernel_size KERNEL_SIZE
                                                  --sigma SIGMA [-o OUTPUT]
                                                  [-ws WINDOW_SIZE]
                                                  [-p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}]
                                                  [-b BANDS [BANDS ...]] [-a]
                                                  inputs [inputs ...]

      Apply an adaptive (Local gaussian of 3x3) recursive filter on the input image

      positional arguments:
        inputs                Input file to process (e.g. Sentinel2 L2A MAJA from
                              THEIA). You can provide a single file with extension
                              ".lst" (e.g. "filtering.lst") that lists the input
                              files to process (one input file per line in .lst)

      optional arguments:
        -h, --help            show this help message and exit
        --kernel_size KERNEL_SIZE
                              Kernel size of the filter function, e.g. 3 means a
                              square of 3x3 pixels on which the filter function is
                              computed (default: 8)
        --sigma SIGMA         Standard deviation of the Gaussian distribution
                              (sigma)
        -o OUTPUT, --output OUTPUT
                              Output dir where to store results (by default current
                              dir)
        -ws WINDOW_SIZE, --window_size WINDOW_SIZE
                              Size of tiles to distribute processing, default: 1024
        -p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}, --pad {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}
                              Pad to use around the image, default : edge (see https
                              ://numpy.org/doc/stable/reference/generated/numpy.pad.
                              html for more information)
        -b BANDS [BANDS ...], --bands BANDS [BANDS ...]
                              List of bands to compute
        -a, --all             Compute all bands

      By default only first band is computed.

    The corresponding API functions that is called by the command line interface is the following :

    .. autofunction:: eolab.rastertools.processing.algo.adaptive_gaussian

    Here is an example of the local mean applied to the NDVI of a SENTINEL2 L2A THEIA image cropped to a region of interest.
    This raster was previously computed using :ref:`radioindice` on the original SENTINEL2 L2A THEIA image.

    .. code-block:: console

     $ rastertools filter adaptive_gaussian --kernel_size 16 --sigma 1 "./SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"

    .. list-table::
       :widths: 20 20
       :header-rows: 0

       * - .. centered:: Original
         - .. centered:: Filtered by Adaptive gaussian

       * - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.jpg
            :align: center
         - .. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-adaptive_gaussian.jpg
            :align: center

<<<<<<< HEAD
=======
.. image:: ../_static/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi-adaptive_gaussian.jpg
>>>>>>> rasterio_plugin_vsimem
