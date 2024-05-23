.. svf:

svf
---

``svf`` computes the SVF of a Digital Height Model.

SVF stands for Sky View Factor. It is a geophysical parameter that measures the portion of the sky
visible from a certain point. The portion of the sky visible above the surface is especially relevant
in energy balance studies and computation of diffuse solar insolation.

Sky-view factor is defined as the proportion of visible sky (:math:`\Omega`) above a certain
observation point as seen from a two-dimensional representation.

The light that falls from the sky onto a certain part of the surface is reduced by the obstacles
that form the horizon. These obstacles can be described in all directions by the vertical
elevation angle above the horizontal plane.

A good SVF approximation can therefore be performed with the estimate of this angle
in several directions. After the vertical elevation angle is determined in the chosen
number of directions n, the SVF is determined as a sum of all portions of the sky within
each direction: :math:`\sum \frac {\cos \gamma_i}{n}`, where :math:`\gamma_i` is the
vertical angle of the horizon in the`direction i.

The angle :math:`\gamma` is extracted from the Digital Elevation Model:
:math:`\tan \frac{Height}{Distance}`::

                          _____
                        x|     |  ^
                    x    |     |  | Height (from Digital Elevation Model)
               x   __    |     |  |
      ____p_______|  |___|     |__v____________
          <-------------->
              Distance

Where p is the current pixel where the SVF is computed.

In a direction, the algorithm computes all angles and keeps the largest one. To avoid testing
too many points, the "radius" parameter defines the max distance of the pixel to test.

.. code-block:: console

  $ rastertools svf --help
  usage: rastertools svf [-h] --radius RADIUS --directions DIRECTIONS
                         --resolution RESOLUTION [--altitude ALTITUDE]
                         [-o OUTPUT] [-ws WINDOW_SIZE]
                         [-p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}]
                         inputs [inputs ...]
  
  Compute Sky View Factor of a Digital Height Model.
  
  positional arguments:
    inputs                Input file to process (i.e. geotiff corresponding to a
                          Digital Height Model). You can provide a single file
                          with extension ".lst" (e.g. "filtering.lst") that
                          lists the input files to process (one input file per
                          line in .lst)
  
  optional arguments:
    -h, --help            show this help message and exit
    --radius RADIUS       Max distance (in pixels) around a point to evaluate
                          horizontal elevation angle
    --directions DIRECTIONS
                          Number of directions on which to compute the horizon
                          elevation angle
    --resolution RESOLUTION
                          Pixel resolution in meter
    --altitude ALTITUDE   Reference altitude to use for computing the SVF. If
                          this option is not specified, SVF is computed for
                          every point at the altitude of the point
    -o OUTPUT, --output OUTPUT
                          Output dir where to store results (by default current
                          dir)
    -ws WINDOW_SIZE, --window_size WINDOW_SIZE
                          Size of tiles to distribute processing, default: 1024
    -p {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}, --pad {none,edge,maximum,mean,median,minimum,reflect,symmetric,wrap}
                          Pad to use around the image, default : edge (see https
                          ://numpy.org/doc/stable/reference/generated/numpy.pad.
                          html for more information)

.. warning::
  This command line does not accept all input raster products as other raster tools (radioindice, zonalstats).
  It is mandatory to use a raster file (typically a geotif) in a format that can be read by rasterio: rasterio.open(xxx)).

Example:

Let's take as input a Digital Height Model of Toulouse generated from a PLEIADES stereo (0.5m resolution):

.. image:: ../_static/dsm.jpg

The first command line computes the Sky View Factor using 16 directions and a radius of 50 pixels (25 meters).
The SVF is computed at the altitude of every point of the Digital Height Model, i.e. the SVF is computed on top
of buildings (for the highest building, SVF is thus 1).

.. code-block:: console

  $ rastertools svf --radius 50 --directions 16 --resolution 0.5 tests\tests_data\toulouse-mnh.tif

This command generates the following SVF:

.. image:: ../_static/dsm-svf.jpg

It is also possible to compute the SVF at a specified height, for instance on ground (0m altitude for a Digital Height Model).

.. code-block:: console

  $ rastertools svf --radius 50 --directions 16 --resolution 0.5 tests\tests_data\toulouse-mnh.tif

The SVF is the following:

.. image:: ../_static/dsm-svf0.jpg

As expected, the SVF at altitude 0m are equal to 0 for pixels inside buildings, and are the same as in the previous image
for pixels outside the buildings.