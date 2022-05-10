#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from .action import Action
from .dataset import Dataset

from enum import Enum, auto
from typing import Optional


class ActivityStatus(Enum):
    CREATED = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class Activity:
    """A Science Campaign Activity

    :param name: Science campaign activity name.
    :type name: str
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        """Create an object that represents a science campaign activity."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name = name
        self.datasets = []
        self.actions = []
        self.parents = []

    def add_dataset(self, dataset: Dataset) -> None:
        """Add a dataset to the activity.

        :param dataset: a Dataset object.
        :type dataset: Dataset
        """
        self.datasets.append(dataset)

    def add_action(self, action: Action) -> None:
        """Add an action to the activity.

        :param action: an Action object.
        :type action: Action
        """
        self.actions.append(action)

    def depends(self, activity: "Activity") -> None:
        """Add dependency between activities.

        :param activity: A parent activity.
        :type activity: Activity
        """
        self.parents.append(activity)
