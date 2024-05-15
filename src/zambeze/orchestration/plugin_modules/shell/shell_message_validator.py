#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin_message_validator import PluginMessageValidator
from .shell_message_template_generator import Bash

# Standard imports
from dataclasses import asdict
from typing import Optional, overload

import logging


class ShellMessageValidator(PluginMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("shell", logger=logger)

    def __validateEnvVars(self, action: str, arguments: dict):
        # Make sure all of the values provided in the env_vars dict
        # are of type string
        checks = []
        if arguments[action]["env_vars"]:
            if not isinstance(arguments[action]["env_vars"], dict):
                checks.append(
                    {
                        action: (
                            False,
                            (
                                "Shell env_vars must be provided as a dict but "
                                "they have been provided as "
                                f"{type(arguments[action]['env_vars'])}."
                            ),
                        )
                    }
                )
            else:
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
                    else:
                        # Detect $ in env variable provided by user
                        # only support env variables with ${} syntax
                        # not simply $
                        if value.count("$") != value.count("${"):
                            checks.append(
                                {
                                    action: (
                                        False,
                                        "Shell environment variables can "
                                        + "support shell variable injection."
                                        + " However, zambeze only support the "
                                        + "more explicit${} syntax "
                                        + " value has the following syntax: "
                                        + f"{value}.",
                                    )
                                }
                            )

        return checks

    def _validateAction(self, action: str, checks: list, arguments: dict):
        print("Shell validate action")
        if not isinstance(arguments, dict):
            print("Converting to dict if dataclass")
            arguments = asdict(arguments)

        print("arguments are")
        print(arguments)
        if action == "bash":
            temp_check = []
            if "program" not in arguments[action]:
                temp_check.append(
                    {
                        action: (
                            False,
                            "A program has not been defined to run in the shell,"
                            + " required 'program' field is missing.",
                        )
                    }
                )
            if "env_vars" in arguments[action]:
                print("Validate env_vars")
                result = self.__validateEnvVars(action, arguments)
                temp_check.extend(result)

            if len(temp_check) > 0:
                checks.extend(temp_check)
                return checks
        else:
            checks.append({action: (False, f"{action} unsupported action\n")})
            return checks

        checks.append({action: (True, "")})
        return checks

    def validate_action(self, arguments: dict, action) -> list:
        checks = []
        return self._validateAction(action, checks, arguments)

    @overload
    def validateMessage(self, arguments: Bash) -> list:
        pass

    @overload
    def validateMessage(self, arguments: list[dict]) -> list:
        pass

    def validate_message(self, arguments):
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
            print("Shell validateMessage")
            print(arguments)
            if hasattr(arguments[index], "bash"):
                checks = self._validateAction("bash", checks, arguments[index])
        return checks
