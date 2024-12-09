.. tiling:

tiling
------

``tiling`` (or ``ti``) tiles an input raster following the geometries defined in a vector
file.

.. code-block:: console

  $ georastertools tiling --help
  usage: georastertools tiling [-h] -g GRID_FILE [--id_col ID_COLUMN]
                            [--id ID [ID ...]] [-o OUTPUT] [-n OUTPUT_NAME]
                            [-d SUBDIR_NAME]
                            inputs [inputs ...]
  Generate tiles of an input raster image following the geometries defined by
  a given grid.

  The tiling command divides a raster image into smaller tiles based on a grid
  defined in a vector-based spatial data file. Each tile corresponds to a
  specific area within the grid, and tiles can be saved using a customizable
  naming convention and optionally placed in subdirectories based on their
  tile ID.

  Arguments:

      inputs TEXT

      Raster files to process. You can provide a single file with extension
      ".lst" (e.g. "tiling.lst") that lists the input files to process (one
      input file per line in .lst)

  Options:
      -g, --grid TEXT    vector-based spatial data file containing the grid to use
                         to generate the tiles  [required]
      --id_col TEXT      Name of the column in the grid file used to number the
                         tiles. When ids are defined, this argument is requiredto
                         identify which column corresponds to the define ids
      --id INTEGER       Tiles ids of the grid to export as new tile, default all
      -o, --output TEXT  Output directory to store results (by default current
                         directory)
      -n, --name TEXT    Basename for the output raster tiles,
                         default:"{}_tile{}". The basename must be defined as a
                         formatted string where tile index is at position 1 and
                         original filename is at position 0. For instance,
                         tile{1}.tif will generate the filename tile75.tif for the
                         tile id = 75
      -d, --dir TEXT     When each tile must be generated in a
                         different subdirectory, it defines the naming convention
                         for the subdirectory. It is a formatted string with one
                         positional parameter corresponding to the tile index. For
                         instance, tile{} will generate the subdirectory name
                         tile75/for the tile id = 75. By default, subdirectory is
                         not defined and output files will be generated directly
                         in the output directory
      -h, --help         Show this message and exit.

In the next examples, we will be working on a grid of 4 cells (ids 1, 2, 3 and 4): *grid.geojson* and the image: *image.tif*.
The grid and the image only overlap on the cells 1 and 2.

* example 1::

    georastertools -v ti -g grid.geojson image.tif

This command will return 2 files in the current directory named *image_tile1.tif* et *image_tile2.tif*
corresponding to the cells 1 and 2. The command will return an error for cells 3 and 4 because they do not overlap the raster image.

* exemple 2::

    georastertools -v ti -g grid.geojson image.tif --id 2 4 --name output_{1}.tif

This command will return 1 file in the current directory named *output_2.tif* and will return an error for cell 4 because this cell
does not overlap the raster image.
