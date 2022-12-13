#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from abc import ABC, abstractmethod
from typing import Optional


class PluginMessageTemplateGenerator(ABC):
    """
    Abstract base class for ensuring that all registered plugins have a
    valid message helper

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
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
