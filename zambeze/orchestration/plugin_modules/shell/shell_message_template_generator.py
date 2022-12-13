#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin_template_generator import PluginMessageTemplateGenerator

# Standard imports
from dataclasses import dataclass
from typing import Optional

import logging


class ShellMessageGenerator(PluginMessageTemplateGenerator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("shell", logger=logger)

    def generate(self, args=None) -> dict:
        """Args can be used to generate a more flexible template. Say for
        instance you wanted to transfer several different items.
        """

        @dataclass
        class Bash:
            bash: {}

        @dataclass
        class Command:
            program: str
            args: list[str]

        return Bash(Command("", []))
