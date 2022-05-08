#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from .activity import Activity
from typing import Optional


class Campaign:
    """A Science Campaign

    :param name: Science campaign name.
    :type name: str
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        """Create an object that represents a science campaign."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name = name
        self.activities = []

    def add_activity(self, activity: Activity) -> None:
        """Add an activity to the campaign.

        :param activity: An activity object.
        :type activity: Activity
        """
        self.debug(f"Adding activity: {activity.name}")
        self.activities.append(activity)
