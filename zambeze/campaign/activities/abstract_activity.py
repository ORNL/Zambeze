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

from zambeze.orchestration.message.abstract_message import AbstractMessage


class ActivityStatus(Enum):
    CREATED = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class AttributeType(Enum):
    FILE = auto()
    FILES = auto()
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

    logger: Optional[logging.Logger]
    campaign_id: Optional[str]
    agent_id: Optional[str]
    message_id: Optional[str]
    activity_id: Optional[str]
    _status: ActivityStatus

    def __init__(
        self,
        name: str,
        supported_attributes: Optional[list[AttributeType]] = [],
        logger: Optional[logging.Logger] = None,
        campaign_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        message_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Create an object that represents a science campaign activity."""
        self.logger = logging.getLogger(__name__) if logger is None else logger
        self.name: str = name
        self.campaign_id = campaign_id
        self.agent_id = agent_id
        self.message_id = message_id
        self.activity_id = activity_id
        self._status = ActivityStatus.CREATED
        self._supported_attributes = supported_attributes
        self.__dict__.update(kwargs)

    @abstractmethod
    def add(self, attr_type: AttributeType, attribute) -> None:
        raise NotImplementedError(
            "Method to generate message has not been instantiated."
        )

    @abstractmethod
    def set(self, attr_type: AttributeType, attribute) -> None:
        raise NotImplementedError(
            "Method to generate message has not been instantiated."
        )

    def supported_attributes(self) -> list[AttributeType]:
        return self._supported_attribute_types

    @property
    def status(self) -> ActivityStatus:
        """Get current activity status.

        :return: Current activity status
        :rtype: ActivityStatus
        """
        return self._status

    @abstractmethod
    def generate_message(self) -> AbstractMessage:
        raise NotImplementedError(
            "Method to generate message has not been instantiated."
        )
