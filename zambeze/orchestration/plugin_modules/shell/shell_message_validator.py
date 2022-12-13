#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin_message_validator import PluginMessageValidator

# Standard imports
from typing import Optional

import logging


class ShellMessageValidator(PluginMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("shell", logger=logger)

    def _validateAction(self, action: str, checks: list, arguments: dict):
        if "program" not in arguments[action]:
            checks.append(
                {
                    action: (
                        False,
                        "A program has not been defined to run in the shell,"
                        + " required 'program' field is missing.",
                    )
                }
            )

        else:
            checks.append({action: (True, "")})

        return checks

    def validateAction(self, arguments: dict, action) -> list:
        checks = []
        return self._validateAction(action, checks, arguments)

    def validateMessage(self, arguments: list[dict]) -> list:
        """Checks to see if the message contains the right fields


        :Example"

        >>> arguments = [ {
        >>>   "bash": { }
        >>> }]

        """
        checks = []
        for index in range(len(arguments)):
            for action in arguments[index]:
                checks = self._validateAction(action, checks, arguments[index])
        return checks
