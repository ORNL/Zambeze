# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from typing import List, Optional
from .abstract_activity import Activity


class ShellActivity(Activity):
    """A Unix Shell script activity.

    :param name: Campaign activity name.
    :type name: str
    :param files: List of file URIs.
    :type files: Optional[List[str]]
    :param command: Action's command.
    :type command: Optional[str]
    :param arguments: List of arguments.
    :type arguments: Optional[List[str]]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        files: Optional[List[str]] = [],
        command: Optional[str] = None,
        arguments: Optional[List[str]] = [],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object of a unix shell activity."""
        super().__init__(name, files, command, arguments, logger)
        self.logger: Optional[logging.Logger] = (
            logger if logger else logging.getLogger(__name__)
        )

    def generate_message(self) -> dict:
        return {
            "service": "shell",
            "command": self.command,
            "arguments": self.arguments,
            "files": self.files,
        }
