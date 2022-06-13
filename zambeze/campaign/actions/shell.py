# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from .abstract_action import Action, ActionType

from typing import List, Optional


class ShellAction(Action):
    """A Unix Shell script action.

    :param name: Action name.
    :type name: str
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
        command: Optional[str] = None,
        params: Optional[List[str]] = [],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object of a unix shell action."""
        super().__init__(name, ActionType.COMPUTE, command, params, logger)
        self.logger: Optional[logging.Logger] = (
            logger if logger else logging.getLogger(__name__)
        )
