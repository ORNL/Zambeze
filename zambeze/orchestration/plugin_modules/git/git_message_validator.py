#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from __future__ import annotations

# Local imports
from ..abstract_plugin_message_validator import PluginMessageValidator
from .git_message_template_generator import GitCommitTemplate, GitDownloadTemplate
from .git_common import PLUGIN_NAME
from zambeze.log_manager import LogManager
from zambeze.orchestration.identity import valid_email

# Standard imports
from dataclasses import asdict
from typing import Optional, overload
import logging


class GitMessageValidator(PluginMessageValidator):
    def __init__(self, logger: LogManager) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)

    def _validateCommit(self, commit_arguments, checks):
        # Start by checking that all the files have been provided
        action = "commit"
        for item in commit_arguments["items"]:
            if not item["source"].startswith("file://"):
                error_msg = "Error detected for commit source. The file to "
                error_msg += "commit must be located on the posix file system"
                error_msg += "and the source URI must begin with file://"
                checks.append({action: (False, error_msg)})

        if not commit_arguments["destination"].startswith("git://"):
            error_msg = "Error detected for commit destination. The git URI "
            error_msg += "must begin with git://"
            checks.append({action: (False, error_msg)})

        print(commit_arguments)
        if len(commit_arguments["credentials"]["user_name"]) == 0:
            error_msg = "Cannot commit without specifying user_name"
            checks.append({action: (False, error_msg)})

        if not valid_email(commit_arguments["credentials"]["email"]):
            error_msg = "Cannot commit without specifying a valid email address"
            checks.append({action: (False, error_msg)})
        return checks

    def _validateDownload(self, download_arguments, checks):
        action = "download"
        for item in download_arguments["items"]:
            if not item["source"].startswith("git://"):
                error_msg = "Error detected for download source. The git URI "
                error_msg += "must begin with git://"
                checks.append({action: (False, error_msg)})

        if not download_arguments["destination"].startswith("file://"):
            error_msg = "Error detected for download destination. The file to "
            error_msg += "download must have a valid posix path to download to"
            error_msg += "and the destination URI must begin with file://"
            checks.append({action: (False, error_msg)})

        # If a source ends with '/' it indicates that the entire folder
        # should be downloaded.
        return checks

    def _validateAction(self, action: str, checks: list, arguments: dict):
        if not isinstance(arguments, dict):
            arguments = asdict(arguments)

        if action == "commit":
            checks = self._validateCommit(arguments["commit"], checks)

        elif action == "download":
            checks = self._validateDownload(arguments["download"], checks)

        else:
            checks.append({action: (False, f"{action} unsupported action\n")})
            return checks

        checks.append({action: (True, "")})
        return checks

    def validateAction(self, arguments: dict, action) -> list:
        """Check the arguments are supported.

        >>> config = {
        >>> }
        >>> # Assumes you are provided with a single dict not a list of dicts
        >>> arguments = {
        >>>
        >>> }
        >>> instance = Git()
        >>> instance.configure(config)
        >>> checked_arguments = instance.check(arguments)
        >>> # If there is no problem will return the following
        >>> # checked_arguments = [
        >>> # {
        >>> #   "transfer": (True, "")
        >>> # }]
        >>> assert checked_arguments[0]["commit"][0]
        """
        checks = []
        return self._validateAction(action, checks, arguments)

    @overload
    def validateMessage(self, arguments: GitCommitTemplate) -> list:
        ...

    @overload
    def validateMessage(self, arguments: GitDownloadTemplate) -> list:
        ...

    @overload
    def validateMessage(self, arguments: list[dict]) -> list:
        ...

    def validateMessage(self, arguments) -> list:
        """Check the arguments are supported.

        :param arguments: arguments needed to run the rsync plugin
        :type arguments: list[dict]


        :Example:

        >>> config = {
        >>> }
        >>> # Assumes you are provided with a list of dicts
        >>> arguments = [
        >>>     {
        >>>
        >>>     }
        >>> ]
        >>> instance = Git()
        >>> instance.configure(config)
        >>> checked_arguments = instance.check(arguments)
        >>> # If there is no problem will return the following
        >>> # checked_arguments = [
        >>> # {
        >>> #   "commit": (True, "")
        >>> # }]
        """

        if isinstance(arguments, list):
            pass
        elif isinstance(arguments, GitCommitTemplate):
            arguments = [arguments]
        elif isinstance(arguments, GitDownloadTemplate):
            arguments = [arguments]
        else:
            error = "Unsupported argument type encountered. arguments = "
            error += f"{type(arguments)} where {type(GitCommitTemplate)} "
            error += f"or {type(GitDownloadTemplate)} is expected."
            raise Exception(error)

        checks = []

        # Here we are cycling a list of dicts
        for index in range(len(arguments)):
            if hasattr(arguments[index], "commit"):
                checks = self._validateAction("commit", checks, arguments[index])
            if hasattr(arguments[index], "download"):
                checks = self._validateAction("download", checks, arguments[index])

        return checks
