#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from typing import Optional


class Output:
    """A Science Campaign Activity Output

    :param name: A dataset name.
    :type name: str
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Create an object that represents an output for a science campaign activity.

        :param logger: The logger where to log information/warning or errors.
        :type logger: Optional[logging.Logger]
        """
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
