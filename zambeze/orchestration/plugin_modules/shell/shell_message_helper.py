#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin_message_helper import PluginMessageHelper

# Standard imports
from typing import Optional

import logging


class ShellMessageHelper(PluginMessageHelper):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("shell", logger=logger)

    def messageTemplate(self, args=None) -> dict:
        """Args can be used to generate a more flexible template. Say for
        instance you wanted to transfer several different items.
        """
        return {"bash": {"program": "", "args": [""]}}

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
                    continue

                checks.append({action, (True, "")})
        return checks
