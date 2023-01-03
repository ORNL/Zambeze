#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin import Plugin
from .shell_message_validator import ShellMessageValidator
from .shell_common import PLUGIN_NAME, SUPPORTED_ACTIONS
from ...system_utils import isExecutable

# Standard imports
from shutil import which
from typing import Optional

import logging
import os
import subprocess


def checkInputs(variable, left_pattern, right_pattern):
    # find returns -1 if no match was found
    if len(variable) == 0:
        return "", -1, -1

    if len(left_pattern) == 0:
        raise Exception("Must specify a left pattern")

    if len(right_pattern) == 0:
        raise Exception("Must specify a right pattern")

    if variable.count(left_pattern) != variable.count(right_pattern):
        raise Exception("Cannot identify inner pattern ambiguous patterns used")


def getInnerPattern(variable: str, left_pattern: str, right_pattern: str):
    """Finds the value between two patterns

    :Example:

    variable = "My${Long}string${Containing${Nested}Patterns}"
                012345678901234567890123456789012345678901234
    match, start, end = getInnerPattern(variable, "${", "}")
    print(f"match: {match}, start: {start}, end: {end})

    Will return

    match: Nested, start: 27, end: 36
    """
    checkInputs(variable, left_pattern, right_pattern)

    left_index = variable.find(left_pattern, 0, len(variable))
    right_index = variable.rfind(right_pattern, 0, len(variable))

    inner_match_left_index = -1
    inner_match_right_index = -1

    while True:

        if inner_match_left_index < right_index and right_index > -1:
            inner_match_right_index = right_index

        if left_index < inner_match_right_index and left_index > -1:
            inner_match_left_index = left_index

        match = ""
        if inner_match_right_index > -1 and inner_match_left_index > -1:
            match = variable[
                inner_match_left_index + len(left_pattern): inner_match_right_index
            ]

        if (left_index > inner_match_right_index or left_index <= -1) and (
            right_index <= inner_match_left_index or right_index <= -1
        ):
            if inner_match_right_index > -1 and inner_match_left_index > -1:
                return (
                    match,
                    inner_match_left_index,
                    inner_match_right_index + len(right_pattern),
                )
            return "", -1, -1

        left_index = variable.find(left_pattern, left_index + 1, len(variable))
        if right_index >= -1:
            right_index = variable.rfind(right_pattern, 0, right_index)


def mergeEnvVariables(current_vars: dict, new_vars: dict) -> dict:
    """Function supports merging env variables

    This function also supports ${} notation, where ${var} where
    var is a variable in the current env.
    """
    for key in new_vars.keys():
        value = new_vars[key]
        match, index_left, index_right = getInnerPattern(value, "${", "}")
        while len(match) > 0:
            if match in current_vars.keys():
                value = value[:index_left] + current_vars[match] + value[index_right:]
                new_vars[key] = value
            match, index_left, index_right = getInnerPattern(value, "${", "}")

    # If new vars have the same named key it will overwrite current vars
    return {**current_vars, **new_vars}


class Shell(Plugin):
    """Implementation of a Shell plugin."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)
        self._configured = False
        self._supported_actions = SUPPORTED_ACTIONS
        self._message_validator = ShellMessageValidator(logger)

    def configure(self, config: dict) -> None:
        """Configure shell."""
        self._logger.debug(f"Configuring {self._name} plugin")
        for action in self._supported_actions.keys():
            if isExecutable(action):
                self._supported_actions[action] = True
            else:
                self._supported_actions[action] = False
            self._logger.debug(
                f"  - action {action} supported {self._supported_actions[action]}"
            )
        self._configured = True
        self._logger.debug(f"Configured {self._name} = {self._configured}")

    @property
    def configured(self) -> bool:
        return self._configured

    @property
    def help(self) -> str:
        return "Shell does not require any configuration."

    @property
    def supportedActions(self) -> list[str]:
        supported_actions = []
        for action in self._supported_actions:
            if self._supported_actions[action]:
                supported_actions.append(action)
        return supported_actions

    @property
    def info(self) -> dict:
        """Provides information about the instance of the plugin"""
        supported_actions = []
        for action in self._supported_actions:
            if self._supported_actions[action]:
                supported_actions.append(action)

        return {"configured": self._configured, "supported_actions": supported_actions}

    def check(self, arguments: list[dict]) -> list[dict]:
        """Checks to see if the provided shell is supported

        :Example:

        >>> arguments = [ {
        >>>   "bash": { }
        >>> }]

        """

        self._logger.debug("[shell.py] In SHELL check function!")

        checks = []

        for index in range(len(arguments)):
            for action in arguments[index]:
                print(f"shell action {action} index is {index}")
                schema_checks = self._message_validator.validateAction(
                    arguments[index], action
                )
                print("Schema checks")
                print(schema_checks)
                if len(schema_checks) > 0:
                    if schema_checks[0][action][0] is False:
                        checks.extend(schema_checks)
                        continue

                # Check if the action is supported
                if which(action) is None:
                    checks.append({action: (False, f"Unrecognized shell: {action}")})
                    continue

                if "program" not in arguments[index][action]:
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

                if which(arguments[index][action]["program"]) is None:
                    checks.append(
                        {
                            action: (
                                False,
                                "Unable to locate program: "
                                + f"{arguments[action]['program']}",
                            )
                        }
                    )
                checks.append({action: (True, "")})
        return checks

    def process(self, arguments: list[dict]):
        """
        Run the shell plugin.

        :param arguments: arguments needed to run the shell plugin
        :type arguments: list[dict]

        Example

        config = {}
        arguments = [
            {
                "bash": {
                    "program": "/bin/echo",
                    "args": ["Hello! $NAME"],
                    "env_vars": { "NAME": "John" }
                }
            }
        ]

        instance = ShellPlugin()
        instance.configure(config)
        if instance.check(arguments):
            instance.process(arguments)
        """
        if not self._configured:
            raise Exception("Cannot run shell plugin, must first be configured.")

        print("Arguments passed to shell process are")
        print(arguments)
        for data in arguments:
            cmd = data["bash"]["args"]
            cmd.insert(0, data["bash"]["program"])

            # Take an image of the parent environment
            # -- then add the environment variables to it.
            parent_env = os.environ.copy()
            merged_env = parent_env
            try:
                # env_tup : (key, value)
                # Check if dict is empty
                if data["bash"]["env_vars"]:
                    merged_env = mergeEnvVariables(parent_env, data["bash"]["env_vars"])
            #                for env_tup in data["bash"]["env_vars"]:
            #                    parent_env[env_tup[0]] = env_tup[1]
            except ValueError as e:
                self._logger.error(f"Caught ValueError: {e}")

            shell_cmd = " ".join(cmd)

            self._logger.debug(f"Running SHELL command: {shell_cmd}")

            # converting to use actual SHELL so subprocess can inherit parent env
            #   (dev note 1: needed for Tyler's ORNL M1 Mac)
            #   (dev note 2: shell=False can lead to shell injection attacks
            #       if cmd coming from untrusted source. See:
            # https://stackoverflow.com/questions/21009416/python-subprocess-security)
            # shell_exec = subprocess.Popen(shell_cmd, shell=True, env=parent_env)
            print(shell_cmd)
            print(parent_env)
            print(merged_env)
            shell_exec = subprocess.Popen(shell_cmd, shell=True, env=merged_env)
            shell_exec.wait()
