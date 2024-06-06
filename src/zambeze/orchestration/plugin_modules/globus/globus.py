#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin import Plugin
from .globus_common import PLUGIN_NAME, SUPPORTED_ACTIONS
from ...system_utils import isExecutable

# Standard imports
from typing import Optional

import logging
import os
import subprocess


def check_inputs(variable, left_pattern, right_pattern):
    # find returns -1 if no match was found
    if len(variable) == 0:
        return "", -1, -1

    if len(left_pattern) == 0:
        raise Exception("Must specify a left pattern")

    if len(right_pattern) == 0:
        raise Exception("Must specify a right pattern")

    if variable.count(left_pattern) != variable.count(right_pattern):
        raise Exception("Cannot identify inner pattern ambiguous patterns used")


def get_inner_pattern(variable: str, left_pattern: str, right_pattern: str):
    """Finds the value between two patterns

    :Example:

    variable = "My${Long}string${Containing${Nested}Patterns}"
                012345678901234567890123456789012345678901234
    match, start, end = getInnerPattern(variable, "${", "}")
    print(f"match: {match}, start: {start}, end: {end})

    Will return

    match: Nested, start: 27, end: 36
    """
    check_inputs(variable, left_pattern, right_pattern)

    left_index = variable.find(left_pattern, 0, len(variable))
    right_index = variable.rfind(right_pattern, 0, len(variable))

    inner_match_left_index = -1
    inner_match_right_index = -1

    while True:
        if inner_match_left_index < right_index and right_index > -1:
            inner_match_right_index = right_index

        if inner_match_right_index > left_index > -1:
            inner_match_left_index = left_index

        match = ""
        if inner_match_right_index > -1 and inner_match_left_index > -1:
            match = variable[
                inner_match_left_index + len(left_pattern) : inner_match_right_index
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


def merge_env_variables(current_vars: dict, new_vars: dict) -> dict:
    """Function supports merging env variables

    This function also supports ${} notation, where ${var} where
    var is a variable in the current env.
    """
    for key in new_vars.keys():
        value = new_vars[key]
        match, index_left, index_right = get_inner_pattern(value, "${", "}")
        while len(match) > 0:
            if match in current_vars.keys():
                value = value[:index_left] + current_vars[match] + value[index_right:]
                new_vars[key] = value
            match, index_left, index_right = get_inner_pattern(value, "${", "}")

    # If new vars have the same named key it will overwrite current vars
    return {**current_vars, **new_vars}


class Globus(Plugin):
    """Implementation of a Shell plugin."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)
        self._configured = False
        self._supported_actions = SUPPORTED_ACTIONS
        self._message_validator = None

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

    def check(self, arguments: dict):
        """Checks to see if the provided shell is supported

        :Example: TODO.
        """

        self._logger.debug("[shell.py] In SHELL check function!")
        print("[globus.py] In GLOBUS check function!")
        checks = []
        checks.append({"arguments": True})
        return checks

    def process(self, arguments: list[dict]):
        """
        Run the shell plugin.

        :param arguments: arguments needed to run the globus plugin
        :type arguments: list[dict]

        """
        raise NotImplementedError("This should not be touched as 'process' logic intercepted in executor")