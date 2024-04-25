# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="zambeze",
    version="0.2",
    license="MIT",
    author="Oak Ridge National Laboratory",
    author_email="support@zambeze.org",
    description="Zambeze is a task orchestration system for scientific workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ORNL/zambeze",
    packages=find_packages(),
    install_requires=[
        "pyzmq",
        "dill",
        "networkx",
        "pyyaml",
        "SQLAlchemy",
        "globus_sdk",
        "pika",
        "requests",
    ],
    extras_require={"dev": ["pytest", "setuptools"]},
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Topic :: Documentation :: Sphinx",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "zambeze = zambeze.cli:main",
            "zambeze-agent = zambeze.cli_agent:main",
        ]
    },
)
