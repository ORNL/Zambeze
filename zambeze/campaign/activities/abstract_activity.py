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


class AttributeType(Enum):
    FILE = auto()
    FILES = auto()
    DATA_URI = auto()
    DATA_URIS = auto()
    COMMAND = auto()
    ARGUMENT = auto()
    ARGUMENTS = auto()
    TRANSFER_ITEMS = auto()

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
        supported_attributes: Optional[list[Attribute]] = [],
        logger: Optional[logging.Logger] = None,
        **kwargs
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
        self._supported_attributes = supported_attributes
        self.__dict__.update(kwargs)

    def add(self, attr_type: AttributeType, attribute) -> None:

        if attr_type not in self._supported_attribute_types:
            raise Exception(f"Activity {self.name} does not support the provided type {attr_type}")

        if attr_type == FILES:
            """Add a list of files to the dataset.

            :param files: List of file URIs.
            :type files: list[str]
            """
            self.files.extend(attribute)
        elif attr_type == FILE:
            """Add a file to the dataset.

            :param file: A URI to a single file.
            :type file: str
            """
            self.files.append(attribute)
        elif attr_type == ARGUMENT:
            """Add an argument to the action.

            :param arg: An argument.
            :type arg: str
            """
            self.arguments.append(attribute)
        elif attr_type == ARGUMENTS:
            """Add a list of arguments to the action.

            :param args: List of arguments.
            :type args: list[str]
            """
            self.arguments.extend(attribute)

    def set(self, attr_type: Attribute, attribute) -> None: 
        
        if attr_type not in self._supported_attribute_types:
            raise Exception(f"Activity {self.name} does not support the provided type {attr_type}")

        if attr_type == FILES:
            """Set the list of files.

            :param files: List of file URIs.
            :type files: list[str]
            """
            self.files = attribute
        elif attr_type == FILE:
            """Set files to a single file.

            :param file: A URI to a single file.
            :type file: str
            """
            self.files = attribute
        elif attr_type == ARGUMENT:
            """Set an argument to the action.

            :param arg: An argument.
            :type arg: str
            """
            self.arguments = attribute
        elif attr_type == ARGUMENTS:
            """Set a list of arguments to the action.

            :param args: List of arguments.
            :type args: list[str]
            """
            self.arguments = attribute
        elif attr_type == COMMAND:
            """Set a command to the action.

            :param command: A command.
            :type command: str
            """
            self.command = attribute

    def supported_attributes(self) -> list[Attribute]:
        return self._supported_attribute_types

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
