#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from zambeze.log_manager import LogManager
from zambeze.orchestration.plugin_modules.abstract_plugin_template_generator import (
    PluginMessageTemplateGenerator,
)
from ..common_dataclasses import Source
from .git_common import PLUGIN_NAME, SUPPORTED_ACTIONS

# Standard imports
from dataclasses import dataclass, field
from typing import Optional

import logging


@dataclass
class GitCredentialTemplate:
    user_name: str
    access_token: str
    email: str


@dataclass
class GitCommitTemplateInner:
    destination: str
    commit_message: str
    credentials: GitCredentialTemplate
    items: list = field(default_factory=list)


@dataclass
class GitCommitTemplate:
    commit: GitCommitTemplateInner


@dataclass
class GitDownloadTemplateInner:
    destination: str
    credentials: GitCredentialTemplate
    items: list = field(default_factory=list)


@dataclass
class GitDownloadTemplate:
    download: GitDownloadTemplateInner


class GitMessageTemplateGenerator(PluginMessageTemplateGenerator):
    def __init__(self, logger: LogManager) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)
        self._supported_actions = SUPPORTED_ACTIONS

    def generate(self, args=None):
        """Args can be used to generate a more flexible template. Say for
        instance you wanted to transfer several different items.
        """
        if args is None or args == "commit":
            return GitCommitTemplate(
                GitCommitTemplateInner(
                    "", "", GitCredentialTemplate("", "", ""), [Source("")]
                )
            )
        elif args == "download":
            return GitDownloadTemplate(
                GitDownloadTemplateInner(
                    "", GitCredentialTemplate("", "", ""), [Source("")]
                )
            )

        else:
            raise Exception(
                "Unrecognized argument provided, cannot generate " "messageTemplate"
            )
