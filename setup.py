#!/usr/bin/env python
import os

from distutils.core import setup

from djsonapi import __version__


rel = lambda *x: os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

with open(rel("./README.txt")) as readme:
    long_description = readme.read()

VERSION = (0, 1, 0)

setup(name="djsonapi",
      version=".".join(map(str, __version__)),
      description="Non-prohibitive, JSON API library for Django.",
      long_description=long_description,
      author="Evan Leis",
      author_email="evan.explodes@gmail.com",
      url="https://github.com/explodes/djsonapi",
      download_url="https://pypi.python.org/pypi/djsonapi/",
      package_data={},
      packages=("djsonapi",),
      license="MIT",
      requires=[
          "django (>=1.5)",
      ]
)