#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin_message_validator import PluginMessageValidator
from .shell_message_template_generator import (
    Bash,
)

# Standard imports
from dataclasses import asdict
from typing import Optional, overload

import logging


class ShellMessageValidator(PluginMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("shell", logger=logger)


    def __validateEnvVars(
            self,
            action: str,
            arguments: dict,
            checks: list):

        # Make sure all of the values provided in the env_vars dict
        # are of type string
        if arguments[action]["env_vars"]:
            for key in arguments[action]["env_vars"].keys():
                value = arguments[action]["env_vars"][key]
                if not isinstance(value, str):
                    checks.append(
                           {
                               action: (
                                   False,
                                   "All env_vars key value pairs must be strings "
                                   + f" {key} value is not: {value}.",
                               )
                           }
                       )
        return checks


    def _validateAction(self, action: str, checks: list, arguments: dict):
        if not isinstance(arguments, dict):
            arguments = asdict(arguments)

        if action == "bash":
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
            if "env_vars" in arguments[action]:
                checks = self.__validateEnvVars(action, arguments, checks)

        else:
            checks.append({action: (False, f"{action} unsupported action\n")})
            return checks

        checks.append({action: (True, "")})
        return checks

    def validateAction(self, arguments: dict, action) -> list:
        checks = []
        return self._validateAction(action, checks, arguments)

    @overload
    def validateMessage(self, arguments: Bash) -> list:
        ...

    @overload
    def validateMessage(self, arguments: list[dict]) -> list:
        ...

    def validateMessage(self, arguments):
        """Checks to see if the message contains the right fields


        :Example"

        >>> arguments = [ {
        >>>   "bash": { }
        >>> }]

        """
        if isinstance(arguments, list):
            pass
        elif isinstance(arguments, Bash):
            arguments = [arguments]
        else:
            error = (
                f"Unsupported argument type encountered. arguments = {type(arguments)}"
            )
            error += f" where {type(Bash)} is expected"
            raise Exception(error)

        checks = []
        for index in range(len(arguments)):
            if hasattr(arguments[index], "bash"):
                checks = self._validateAction("bash", checks, arguments[index])
        return checks
