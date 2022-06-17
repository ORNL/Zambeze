#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional


class ActivityStatus(Enum):
    CREATED = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class Activity(ABC):
    """An abstract class of a scientific campaign activity.

    :param name: Campaign activity name.
    :type name: str
    :param files: List of file URIs.
    :type files: Optional[list[str]]
    :param command: Action's command.
    :type command: Optional[str]
    :param arguments: List of arguments.
    :type arguments: Optional[list[str]]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        files: Optional[list[str]] = [],
        command: Optional[str] = None,
        arguments: Optional[list[str]] = [],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object that represents a science campaign activity."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name: str = name
        self.files: list[str] = files
        self.command: str = command
        self.arguments: list[str] = arguments
        self.status: ActivityStatus = ActivityStatus.CREATED

    def add_files(self, files: list[str]) -> None:
        """Add a list of files to the dataset.

        :param files: List of file URIs.
        :type files: list[str]
        """
        self.files.extend(files)

    def add_file(self, file: str) -> None:
        """Add a file to the dataset.

        :param file: A URI to a single file.
        :type file: str
        """
        self.files.append(file)

    def add_arguments(self, args: list[str]) -> None:
        """Add a list of arguments to the action.

        :param args: List of arguments.
        :type args: list[str]
        """
        self.arguments.extend(args)

    def add_argument(self, arg: str) -> None:
        """Add an argument to the action.

        :param arg: An argument.
        :type arg: str
        """
        self.arguments.append(arg)

    def set_command(self, command: str) -> None:
        """Set the action's command.

        :param command: A command.
        :type command: str
        """
        self.command = command

    def get_status(self) -> ActivityStatus:
        """Get current activity status.

        :return: Current activity status
        :rtype: ActivityStatus
        """
        return self.status

    @abstractmethod
    def generate_message(self) -> dict:
        raise NotImplementedError(
            "Method to generate message has not been instantiated."
        )
