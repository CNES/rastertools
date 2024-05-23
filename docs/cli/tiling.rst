.. tiling:

tiling
------

``tiling`` (or ``ti``) tiles an input raster following the geometries defined in a vector
file.

.. code-block:: console

  $ rastertools tiling --help
  usage: rastertools tiling [-h] -g GRID_FILE [--id_col ID_COLUMN]
                            [--id ID [ID ...]] [-o OUTPUT] [-n OUTPUT_NAME]
                            [-d SUBDIR_NAME]
                            inputs [inputs ...]
  
  Generate tiles of an input raster image following the geometries defined by a
  given grid
  
  positional arguments:
    inputs                Raster files to process. You can provide a single file
                          with extension ".lst" (e.g. "tiling.lst") that lists
                          the input files to process (one input file per line in
                          .lst)
  
  optional arguments:
    -h, --help            show this help message and exit
    -g GRID_FILE, --grid GRID_FILE
                          vector-based spatial data file containing the grid to
                          use to generate the tiles
    --id_col ID_COLUMN    Name of the column in the grid file used to number the
                          tiles. When ids are defined, this argument is required
                          to identify which column corresponds to the defined
                          ids
    --id ID [ID ...]      Tiles ids of the grid to export as new tile, default
                          all
    -o OUTPUT, --output OUTPUT
                          Output dir where to store results (by default current
                          dir)
    -n OUTPUT_NAME, --name OUTPUT_NAME
                          Basename for the output raster tiles, default:
                          "{}_tile{}". The basename must be defined as a
                          formatted string where tile index is at position 1 and
                          original filename is at position 0. For instance,
                          tile{1}.tif will generate the filename tile75.tif for
                          the tile id = 75.
    -d SUBDIR_NAME, --dir SUBDIR_NAME
                          When each tile must be generated in a different
                          subdir, it defines the naming convention for the
                          subdir. It is a formatted string with one positional
                          parameter corresponding to the tile index. For
                          instance, tile{} will generate the subdir name tile75/
                          for the tile id = 75. By default, subdir is not
                          defined and output files will be generated directly in
                          the outputdir.

In the next examples, we will be working on a grid of 4 cells (ids 1, 2, 3 and 4): *grid.geojson* and the image: *image.tif*.
The grid and the image only overlap on the cells 1 and 2.

* example 1::

    rastertools -v ti -g grid.geojson image.tif

This command will return 2 files in the current directory named *image_tile1.tif* et *image_tile2.tif*
corresponding to the cells 1 and 2. The command will return an error for cells 3 and 4 because they do not overlap the raster image.

* exemple 2::

    rastertools -v ti -g grid.geojson image.tif --id 2 4 --name output_{1}.tif 

This command will return 1 file in the current directory named *output_2.tif* and will return an error for cell 4 because this cell
does not overlap the raster image.
