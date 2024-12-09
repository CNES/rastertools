Conda
-----

First, create a conda environment via:

.. code-block:: console

  $ conda env create -f environment.yml
  $ conda env update -f env_update.yml

The following libraries will be installed in the conda environment named ``georastertools`` :

- pyscaffold
- geopandas
- scipy
- gdal
- rasterio
- matplotlib
- tqdm

Secondly, run commands:

.. code-block:: console

  $ conda activate georastertools
  $ pip install -e .

``georastertools`` will be installed in the conda environment. Then, the CLI ``georastertools`` can be used and the API :obj:`eolab.georastertools`
can be called in a python script.

Docker et Singularity
---------------------

``georastertools`` can be used in a Docker container that is built from the Dockerfile available in the root directory of the project.
To create the docker image, run:

.. code-block:: console

  $ docker build -t georastertools:latest .

To create the singularity image from the docker image, run:

.. code-block:: console

  $ singularity build rastertools_latest.sif docker://georastertools:latest
