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


class Plugin(ABC):
    """
    Abstract base class for ensuring that all registered plugins have the
    same interface

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
    def configure(self, config: dict) -> None:
        """Configure this set up the plugin."""
        raise NotImplementedError("for configuring plugin.")

    @property
    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError(
            "Method for indicating if plugin has been configured has not been "
            "instantiated."
        )

    @property
    @abstractmethod
    def supportedActions(self) -> list[str]:
        raise NotImplementedError(
            "Method indicating supported actions of the plugin is not " "implemented"
        )

    @property
    @abstractmethod
    def help(self) -> str:
        raise NotImplementedError("Missing help message that explains plugin")

    @property
    @abstractmethod
    def info(self) -> dict:
        """This method is to be used after configuration step and will return
        information about the plugin such as configuration settings and
        defaults."""
        raise NotImplementedError("returns information about the plugin.")

    @abstractmethod
    def check(self, arguments: list[dict]) -> list[dict]:
        """Determine if the proposed arguments can be executed by this instance.

        :param arguments: The arguments are checked to ensure their types and
        formats are valid
        :type arguments: list[dict]
        :return: Returns the list of actions that are vaid
        :rtype: list[dict] with the actions valid actions listed with bool set to
        True and invalid ones False, along with a message.

        :Example:

        >>> arguments =
        >>> [
        >>>     { "action1": { "dothis": ...} },
        >>>     { "action2": { "dothat": ...} },
        >>> ]
        >>> checked_actions = plugin.check(arguments)
        >>> for action in checked_actions:
        >>>     print(f"{action}: {checked_actions[action]}")
        >>> # Should print
        >>> # action1 True, ""
        >>> # action2 False, "This was the problem"
        """

    @abstractmethod
    def process(self, arguments: list[dict]) -> dict:
        """Will run the plugin with the provided arguments"""
        raise NotImplementedError(
            "process method of derived plugin must be implemented."
        )
