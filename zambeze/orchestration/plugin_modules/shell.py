#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

# Local imports
from .abstract_plugin import Plugin

# Standard imports
from typing import Optional


class Shell(Plugin):
    """Implementation of a Shell plugin."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(logger=logger)
        self.__name = "shell"
        self.__configured = False

    def configure(self, config: dict) -> None:
        """Configure shell."""
        self.logger.debug(f"Configuring {self.__name} plugin.")
        self.__configured = True

    @property
    def configured(self) -> bool:
        return self.__configured

    @property
    def name(self) -> str:
        return self.__name

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
        if not self.__configured:
            raise Exception("Cannot run shell plugin, must first be configured.")
        print("Running shell plugin")
