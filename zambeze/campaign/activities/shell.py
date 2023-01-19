# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import time
import uuid

from typing import Optional
from .abstract_activity import Activity

from zambeze.orchestration.message.abstract_message import AbstractMessage
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType


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
        campaign_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        message_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Create an object of a unix shell activity."""
        super().__init__(
            name,
            files,
            command,
            arguments,
            logger,
            campaign_id,
            agent_id,
            message_id,
            activity_id=str(uuid.uuid4()),
        )
        self.logger: Optional[logging.Logger] = (
            logger if logger else logging.getLogger(__name__)
        )
        # Pull out environment variables, IF users submitted them.
        if "env_vars" in kwargs:
            if not isinstance(kwargs.get("env_vars"), dict):
                raise Exception("env_vars provided via kwargs mubst be a dict.")
            self.env_vars = kwargs.get("env_vars")
        else:
            self.env_vars = {}

        self.logger.info("[activities/shell.py] Printing files after init in SHELL")
        self.logger.info(self.files)

    def generate_message(self) -> AbstractMessage:

        factory = MessageFactory(logger=self.logger)
        template = factory.createTemplate(
            MessageType.ACTIVITY, ActivityType.SHELL, {"shell": "bash"}
        )

        try:
            template[1].activity_id = self.activity_id
            template[1].message_id = self.message_id
            template[1].agent_id = self.agent_id
            template[1].campaign_id = self.campaign_id
            template[1].credential = {}
            template[1].submission_time = str(int(time.time()))
            template[1].body.type = "SHELL"
            template[1].body.shell = "bash"
            template[1].body.files = self.files
            template[1].body.parameters.program = self.command
            template[1].body.parameters.args = self.arguments
            template[1].body.parameters.env_vars = self.env_vars
        except Exception as e:
            self.logger.info(f"Error is here: {e}")

        return factory.create(template)
