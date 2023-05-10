#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from zambeze.log_manager import LogManager

# Standard imports
import logging

from abc import ABC, abstractmethod


class PluginMessageTemplateGenerator(ABC):
    """
    Abstract base class for ensuring that all registered plugins have a
    valid message helper

    :param logger: The logger where to log information/warning or errors.
    :type logger: LogManager
    """

    def __init__(self, name: str, logger: LogManager) -> None:
        self._logger: LogManager = logger
        self._name = name

    @property
    def name(self) -> str:
        """Returns the name of the plugin.

        The name of the plugin, should be lower case

        :return: Name of the plugin
        :rtype: string
        """
        return self._name

    @abstractmethod
    def generate(self, args) -> dict:
        """Returns the message Template that can be attached to an activity"""
        raise NotImplementedError("messageTemplate method has not been created.")
