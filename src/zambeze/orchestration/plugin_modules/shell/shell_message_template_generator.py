#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin_template_generator import PluginMessageTemplateGenerator
from .shell_common import PLUGIN_NAME

# Standard imports
from dataclasses import dataclass
from typing import Optional

import logging


@dataclass
class Command:
    program: str
    args: list[str]
    env_vars: dict


@dataclass
class Bash:
    bash: Command


class ShellMessageTemplateGenerator(PluginMessageTemplateGenerator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)

    def generate(self, args=None):
        """Args can be used to generate a more flexible template. Say for
        instance you wanted to transfer several different items.
        """
        return Bash(Command("", [], {}))
