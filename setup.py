#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

# Fetch the version
exec(open("zambeze/version.py").read())

setup(
    name="zambeze",
    version=str(__version__),
    license="MIT",
    author="Oak Ridge National Laboratory",
    author_email="support@zambeze.org",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zambeze/zambeze",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["setuptools"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Documentation :: Sphinx",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.7",
)
