#!/usr/bin/env python
import os

from distutils.core import setup

from djsonapi import __version__


rel = lambda *x: os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

with open(rel("./README.txt")) as readme:
    long_description = readme.read()

setup(
    name="django-jsonapi",
    version=".".join(map(str, __version__)),
    description="Non-prohibitive, JSON API library for Django.",
    long_description=long_description,
    author="Evan Leis",
    author_email="evan.explodes@gmail.com",
    url="https://github.com/explodes/djsonapi",
    download_url="https://pypi.python.org/pypi/djsonapi/",
    package_data={},
    license="MIT",
    classifiers=(
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ),
    packages=(
        "djsonapi",
    ),
)