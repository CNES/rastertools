.. _cli:

======================
Command Line Interface
======================

georastertools
-----------

The CLI **georastertools** enable to activate several subcommands, one per raster tool:

.. code-block:: console

  $ georastertools --help
  usage: georastertools [-h] [-t RASTERTYPE] [--version] [--max_workers MAX_WORKERS] [--debug] [-v] [-vv]
                     {filter,fi,hillshade,hs,radioindice,ri,speed,sp,svf,tiling,ti,timeseries,ts,zonalstats,zs} ...

  Collection of tools on raster data
  
  optional arguments:
    -h, --help            show this help message and exit
    -t RASTERTYPE, --rastertype RASTERTYPE
                          JSON file defining additional raster types of input files
    --version             show program's version number and exit
    --max_workers MAX_WORKERS
                          Maximum number of workers for parallel processing. If not given, it will default
                          to the number of processors on the machine. When all processors are not allocated
                          to run georastertools, it is thus recommended to set this option.
    --debug               Store to disk the intermediate VRT images that are generated when handling the 
                          input files which can be complex raster product composed of several band files.
    -v, --verbose         set loglevel to INFO
    -vv, --very-verbose   set loglevel to DEBUG
  
  Commands:
    {filter,fi,hillshade,hs,radioindice,ri,speed,sp,svf,tiling,ti,timeseries,ts,zonalstats,zs}
      filter (fi)         Apply a filter to a set of images
      hillshade (hs)      Compute hillshades of a Digital Elevation / Surface / Height Model (a raster 
                          containing the height of the point as pixel values)
      radioindice (ri)    Compute radiometric indices
      speed (sp)          Compute speed of rasters
      svf                 Compute Sky View Factor of a Digital Height Model
      tiling (ti)         Generate image tiles
      timeseries (ts)     Temporal gap filling of an image time series
      zonalstats (zs)     Compute zonal statistics

The **georastertools** CLI generates the following sys.exit values:

- 0: everything runs fine
- 1: processing error
- 2: wrong configuration of the raster tool (e.g. invalid parameter value given in the command line)

**georastertools** is thus the entry point for all the following tools:

.. toctree::
   :maxdepth: 1
   :glob:

   cli/*

**georastertools** enables to configure additional custom rastertypes (cf. Usage) and to set-up logging
level. Most of the georastertools display their progression using a progress bar. The progress bar is
displayed when the logging level is set to INFO or DEBUG. It can also be disabled / enabled 
independently to the logging level by setting an environment variable named RASTERTOOLS_NOTQDM. For
instance, setting the environment variable to 1 (resp. 0) will disable (resp. enable) the display
of the progress bar:

.. code-block:: console

  $ export RASTERTOOLS_NOTQDM=1
  $ georastertools -v ri [...]

Most of the **georastertools** are designed to split down rasters into small chunks of data so that
the processing can be run in parallel using several processors. The command line of the tools
defines an argument called `window_size` which corresponds to the size of the chunks. It is also
possible to specify the number of workers (i.e. processors) to use for parallel processing. The
number of workers shall not exceed the number of processors of the machine. It is necessary to
specify this option (`--max_workers`) when running georastertools on a machine where all cpus are
not allocated to the job, e.g. if you submit the processing to a job scheduler such as PBSPro.
Alternatively, you can set an environment variable like this and keep the argument 
`--max_workers` unset:

.. code-block:: console

  $ export RASTERTOOLS_MAXWORKERS=12
  $ georastertools -v hillshade [...] # it will use 12 processors


Docker/Singularity
------------------

By default the Docker / Singularity container executes: ``georastertools --help``. To run another command, type a command like:

.. code-block:: console

  $ docker run -it -u 1000 -v $PWD/tests/tests_data:/usr/data georastertools:latest georastertools ri -r /usr/data/COMMUNE_32001.shp --ndvi /usr/data/SENTINEL2A_20180521-105702-711_L2A_T30TYP_D.zip
  
  $ singularity run rastertools_latest.sif georastertools ri -r tests/tests_data/COMMUNE_32001.shp --ndvi tests/tests_data/SENTINEL2A_20180521-105702-711_L2A_T30TYP_D.zip
