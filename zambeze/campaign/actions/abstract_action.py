# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.


import logging

from abc import ABC
from enum import Enum
from typing import List, Optional


class ActionType(Enum):
    COMPUTE = "z_compute"
    DATA = "z_data"
    STATUS = "z_status"


class Action(ABC):
    """An abstract class of an activity action.

    :param name: Action name.
    :type name: str
    :param type: Type of action.
    :type type: ActionType
    :param command: Action's command.
    :type command: Optional[str]
    :param params: List of parameters.
    :type params: Optional[List[str]]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        type: ActionType,
        command: Optional[str] = None,
        params: Optional[List[str]] = [],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object of an abstract action."""
        self.logger: Optional[logging.Logger] = (
            logger if logger else logging.getLogger(__name__)
        )
        self.name: str = name
        self.type: ActionType = type
        self.params: List[str] = params
        self.command: str = command

    def add_parameters(self, params: List[str]) -> None:
        """Add a list of parameters to the action.

        :param params: List of parameters.
        :type params: List[str]
        """
        self.params.extend(params)

    def add_parameter(self, param: str) -> None:
        """Add a parameter to the action.

        :param param: A parameter.
        :type param: str
        """
        self.params.append(param)

    def set_command(self, command: str) -> None:
        """Set the action's command.

        :param command: A command.
        :type command: str
        """
        self.command = command
