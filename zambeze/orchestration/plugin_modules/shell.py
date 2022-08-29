#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import os
import subprocess

# Local imports
from .abstract_plugin import Plugin
from shutil import which

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
        """Checks to see if the provided shell is supported

        
        :Example" 

        >>> arguments = [ {
        >>>   "bash": { }
        >>> }]

        """
        print("Arguments are")
        print(arguments)
        checks = {}
        for item in arguments:
          for shell in item.keys():
            if which(shell) is None:
              return { shell: ( False, "Unrecognized shell" ) }

            if "program" in item:
              if which(shell["program"]) is None:
                return { shell: ( False, f"Unable to locate program: {shell['program']}" ) }

            checks[shell] = ("True", "")

        print("Checking shell plugin")
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

            # Take an image of the parent environment
            # -- then add the environment variables to it.
            parent_env = os.environ.copy()

            try:
                # env_tup : (key, value)
                for env_tup in data["bash"]["env_vars"]:
                    parent_env[env_tup[0]] = env_tup[1]
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
            shell_exec = subprocess.Popen(shell_cmd, shell=True)
            shell_exec.wait()
