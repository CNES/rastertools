============
Raster tools
============

This project provides a command line named **rastertools** that enables various calculation tools:


- the calculation of radiometric indices on satellite images
- the calculation of the speed of evolution of radiometry from images between two dates
- the calculation of zonal statistics of the bands of a raster, that is to say statistics such as min, max, average, etc.
  on subareas (defined by a vector file) of the area of interest.
  
The **rastertools** project also aims to make the handling of the following image products transparent:

- Sentinel-2 L1C PEPS (https://peps.cnes.fr/rocket/#/search)
- Sentinel-2 L2A PEPS (https://peps.cnes.fr/rocket/#/search)
- Sentinel-2 L2A THEIA (https://theia.cnes.fr/atdistrib/rocket/#/search?collection=SENTINEL2)
- Sentinel-2 L3A THEIA (https://theia.cnes.fr/atdistrib/rocket/#/search?collection=SENTINEL2)
- SPOT 6/7 Ortho de GEOSUD (http://ids.equipex-geosud.fr/web/guest/catalog)

It is thus possible to input files in the command line in any of the formats above. 
It is also possible to specify your own product types by providing a JSON file as a parameter of the command line (cf. docs/usage.rst)

Finally, **rastertools** offers an API for calling these different tools in Python and for extending its capabilities, for example by defining new radiometric indices.

Installation
============

Create a conda environment by typing the following:

.. code-block:: bash

  conda env create -f environment.yml
  conda env update -f env_update.yml

The following dependencies will be installed in the ``rastertools`` environment:

- pyscaffold
- geopandas
- scipy
- gdal
- rasterio
- tqdm

Install ``rastertools`` in the conda environment by typing the following:

.. code-block:: bash

  conda activate rastertools
  pip install -e .

.. note::

  Note: Installing in a *virtualenv* does not work properly for this project. For unexplained reasons, 
  the VRTs that are created in memory by rastertools to handle image products are not properly managed 
  with an installation in a virtualenv.

For more details, including installation as a Docker or Singularity image, please refer to the documentation. : `Installation <docs/install.rst>`_


Usage
=====

rastertools
^^^^^^^^^^^
The rastertools command line is the high-level command for activating the various tools.

.. code-block:: console

  $ rastertools --help
  usage: rastertools [-h] [-t RASTERTYPE] [--version] [-v] [-vv]
                     {filter,fi,radioindice,ri,speed,sp,svf,hillshade,hs,zonalstats,zs,tiling,ti}
                     ...
  
  Collection of tools on raster data
  
  optional arguments:
    -h, --help            show this help message and exit
    -t RASTERTYPE, --rastertype RASTERTYPE
                          JSON file defining additional raster types of input
                          files
    --version             show program's version number and exit
    -v, --verbose         set loglevel to INFO
    -vv, --very-verbose   set loglevel to DEBUG
  
  Commands:
    {filter,fi,radioindice,ri,speed,sp,svf,hillshade,hs,zonalstats,zs,tiling,ti}
      filter (fi)         Apply a filter to a set of images
      radioindice (ri)    Compute radiometric indices
      speed (sp)          Compute speed of rasters
      svf                 Compute Sky View Factor of a Digital Height Model
      hillshade (hs)      Compute hillshades of a Digital Height Model
      zonalstats (zs)     Compute zonal statistics
      tiling (ti)         Generate image tiles

Calling rastertools returns the following exit codes:

.. code-block:: console

    0: everything went well
    1: processing error
    2: incorrect invocation parameters

Details of the various subcommands are presented in the documentation : `Usage <docs/cli.rst>`_


Tests & documentation
=====================

To run tests and generate documentation, the following dependencies must be installed in the conda environment. :

- py.test et pytest-cov (tests execution)
- sphinx (documentation generation)

Pour cela, exécuter la commande suivante :

.. code-block:: console

  conda env update -f env_test.yml


Tests
^^^^^

The project comes with a suite of unit and functional tests. To run them, 
launch the command ``pytest tests``. To run specific tests, execute ``pytest tests -k "<nom_du_test>"``.

The tests may perform comparisons between generated files and reference files. 
In this case, the tests depend on the numerical precision of the platforms. 
To enable these comparisons, you need to add the option. "--compare" for instance ``pytest tests --compare``.

The execution of the tests includes a coverage analysis via pycov.

Documentation generation
^^^^^^^^^^^^^^^^^^^^^^^^

To generate the documentation, run: 

.. code-block:: console

  cd docs
  sphinx-quickstart
  make html

The documentation is generated using the theme "readthedocs".

Note
====

This project has been set up using PyScaffold. For details and usage
information on PyScaffold see https://pyscaffold.org/.
