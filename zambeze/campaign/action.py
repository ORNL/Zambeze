#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from typing import Optional


class Action:
    """An action to be executed as part of an activity.

    :param name: Activity name.
    :type name: str
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        """Create an object that represents an action."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name = name
