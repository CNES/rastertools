# -*- coding: utf-8 -*-
"""
    Setup file for rastertools.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 4.0.2.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
from setuptools import setup, find_packages

if __name__ == "__main__":
    try:
        setup(name='rastertools',
              version="0.1.0",
              description=u"Collection of tools for raster data",
              long_description="",
              classifiers=[],
              keywords='',
              author=u"Olivier Queyrut",
              author_email="",
              url="https://github.com/CNES/rastertools",
              packages=find_packages(exclude=['tests']),
              include_package_data=True,
              zip_safe=False,
              setup_requires = ["setuptools_scm"],
              install_requires=[
                  'click',
                  'rasterio',
                  'pytest>=3.6',
                  'pytest-cov',
                  'geopandas==0.13',
                  'kiwisolver==1.4.5',
                  'matplotlib==3.7.3',
                  'packaging==24.1',
                  'fiona==1.8.21',
                  'sphinx_rtd_theme==3.0.1',
                  'pip==24.2',
                  'sphinx==7.1.2',
                  'scipy==1.8',
                  'pyscaffold',
                  'gdal==3.5.0',
                  'tqdm==4.66'
              ],
              entry_points="""
                [rasterio.rio_plugins]
                rastertools=eolab.rastertools.main:rastertools
                """,
              python_requires='==3.8.13',
              use_scm_version={"version_scheme": "no-guess-dev"})
    except:
        print(
            "\n\nAn error occurred while building the project, "
            "please ensure you have the most updated version of setuptools, "
            "setuptools_scm and wheel with:\n"
            "   pip install -U setuptools setuptools_scm wheel\n\n"
        )
        raise
