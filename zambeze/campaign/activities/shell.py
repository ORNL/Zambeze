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
from .abstract_activity import Activity, AttributeType

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
    files: list[str]
    command: Optional[str]
    arguments: list[str]

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
        activity_id: Optional[str] = str(uuid.uuid4()),
        **kwargs
    ) -> None:
        """Create an object of a unix shell activity."""
        super().__init__(
            name,
            supported_attributes=[
                AttributeType.FILES,
                AttributeType.FILE,
                AttributeType.ARGUMENT,
                AttributeType.ARGUMENTS,
                AttributeType.COMMAND,
            ],
            logger=logger,
            campaign_id=campaign_id,
            agent_id=agent_id,
            message_id=message_id,
            activity_id=activity_id,
        )

        self.arguments = arguments
        self.command = command
        self.files = files

        # Pull out environment variables, IF users submitted them.
        if "env_vars" in kwargs:
            if not isinstance(kwargs.get("env_vars"), dict):
                raise Exception("env_vars provided via kwargs mubst be a dict.")
            self.env_vars = kwargs.get("env_vars")
        else:
            self.env_vars = {}

    def add(self, attr_type: AttributeType, attribute) -> None:

        if attr_type not in self._supported_attributes:
            error_msg = f"Activity {self.name} does not support "
            error_msg += f"the provided type {attr_type}"
            raise Exception(error_msg)

        if attr_type == AttributeType.FILES:
            """Add a list of files to the dataset.

            :param files: List of file URIs.
            :type files: list[str]
            """
            self.files.extend(attribute)
        elif attr_type == AttributeType.FILE:
            """Add a file to the dataset.

            :param file: A URI to a single file.
            :type file: str
            """
            self.files.append(attribute)
        elif attr_type == AttributeType.ARGUMENT:
            """Add an argument to the action.

            :param arg: An argument.
            :type arg: str
            """
            self.arguments.append(attribute)
        elif attr_type == AttributeType.ARGUMENTS:
            """Add a list of arguments to the action.

            :param args: List of arguments.
            :type args: list[str]
            """
            self.arguments.extend(attribute)

    def set(self, attr_type: AttributeType, attribute) -> None:
        if attr_type not in self._supported_attributes:
            error_msg = f"Activity {self.name} does not support the "
            error_msg += f"provided type {attr_type}"
            raise Exception(error_msg)

        if attr_type == AttributeType.FILES:
            """Set the list of files.

            :param files: List of file URIs.
            :type files: list[str]
            """
            self.files = attribute
        elif attr_type == AttributeType.FILE:
            """Set files to a single file.

            :param file: A URI to a single file.
            :type file: str
            """
            self.files = [attribute]
        elif attr_type == AttributeType.ARGUMENT:
            """Set an argument to the action.

            :param arg: An argument.
            :type arg: str
            """
            self.arguments = attribute
        elif attr_type == AttributeType.ARGUMENTS:
            """Set a list of arguments to the action.

            :param args: List of arguments.
            :type args: list[str]
            """
            self.arguments = attribute
        elif attr_type == AttributeType.COMMAND:
            """Set a command to the action.

            :param command: A command.
            :type command: str
            """
            self.command = attribute

    def generate_message(self) -> AbstractMessage:

        factory = MessageFactory()
        template = factory.createTemplate(
            MessageType.ACTIVITY, ActivityType.SHELL, {"shell": "bash"}
        )

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

        return factory.create(template)
