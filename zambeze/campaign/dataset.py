#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from typing import List, Optional


class Dataset:
    """A Science Campaign Dataset

    :param name: A dataset name.
    :type name: str
    :param files: List of file URIs.
    :type files: List[str]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        files: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object that represents a dataset for a science campaign."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name: str = name
        self.files: List[str] = files

    def add_files(self, files: List[str]) -> None:
        """Add a list of files to the dataset.

        :param files: List of file URIs.
        :type files: List[str]
        """
        self.files.extend(files)

    def add_file(self, file: str) -> None:
        """Add a file to the dataset.

        :param file: A URI to a single file.
        :type file: str
        """
        self.files.append(file)
