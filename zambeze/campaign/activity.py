#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from .actions import Action

from enum import Enum, auto
from typing import List, Optional


class ActivityStatus(Enum):
    CREATED = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class Activity:
    """A Scientific Campaign Activity.

    :param name: Campaign activity name.
    :type name: str
    :param files: List of file URIs.
    :type files: Optional[List[str]]
    :param action: An action.
    :type action: Optional[Action]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        files: Optional[List[str]] = [],
        action: Optional[Action] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object that represents a science campaign activity."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name: str = name
        self.files: List[str] = files
        self.action: Action = action
        self.status: ActivityStatus = ActivityStatus.CREATED

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

    def set_action(self, action: Action) -> None:
        """Set an action to the activity.

        :param action: an Action object.
        :type action: Action
        """
        self.action = action

    def get_status(self) -> ActivityStatus:
        """Get current activity status.

        :return: Current activity status
        :rtype: ActivityStatus
        """
        return self.status
