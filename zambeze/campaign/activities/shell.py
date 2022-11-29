# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from typing import Optional
from .abstract_activity import Activity


class ShellActivity(Activity):
    """A Unix Shell script activity.

    :param name: Campaign activity name.
    :type name: str

    :param files: List of file URIs.
    :type files: Optional[list[str]]

    :param command: Action's command.
    :type command: Optional[str]

    :param arguments: List of arguments.
    :type arguments: Optional[list[str]]

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        files: list[str] = [],
        command: Optional[str] = None,
        arguments: list[str] = [],
        logger: Optional[logging.Logger] = None,
        **kwargs
    ) -> None:
        """Create an object of a unix shell activity."""
        super().__init__(name, files, command, arguments, logger)
        self.logger: Optional[logging.Logger] = (
            logger if logger else logging.getLogger(__name__)
        )

        # Pull out environment variables, IF users submitted them.
        if "env_vars" in kwargs:
            self.env_vars = kwargs.get("env_vars")
        else:
            self.env_vars = []

    def generate_message(self) -> dict:
        return {
            "plugin": "shell",
            "files": self.files,
            "cmd": {
                "bash": {
                    "program": self.command,
                    "args": self.arguments,
                    "env_vars": self.env_vars,
                }
            },
        }
