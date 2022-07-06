#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import subprocess

# Local imports
from .abstract_plugin import Plugin

# Standard imports
from typing import Optional


class Shell(Plugin):
    """Implementation of a Shell plugin."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("shell", logger=logger)
        self._configured = False

    def configure(self, config: dict) -> None:
        """Configure shell."""
        self._logger.debug(f"Configuring {self._name} plugin")
        self._configured = True

    @property
    def configured(self) -> bool:
        return self._configured

    @property
    def help(self) -> str:
        return "Shell does not require any configuration."

    @property
    def supportedActions(self) -> list[str]:
        return []

    @property
    def info(self) -> dict:
        return {}

    def check(self, arguments: list[dict]) -> dict:
        print("Checking shell plugin")
        return {"run": False}

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
                    "args": ["Hello!"]
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

        for data in arguments:
            cmd = data["bash"]["args"]
            cmd.insert(0, data["bash"]["program"])
            self._logger.debug(f"Running SHELL command: {' '.join(cmd)}")
            shell_exec = subprocess.Popen(cmd)
            shell_exec.wait()
