#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import json
import logging
import nats
import uuid

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional
# from ...settings import ZambezeSettings



class ActivityStatus(Enum):
    CREATED = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class Activity(ABC):
    """An abstract class of a scientific campaign activity.

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
        files: Optional[list[str]] = [],
        command: Optional[str] = None,
        arguments: Optional[list[str]] = [],
        logger: Optional[logging.Logger] = None,
        **kwargs
    ) -> None:
        """Create an object that represents a science campaign activity."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name: str = name
        self.files: list[str] = files
        self.command: str = command
        self.arguments: list[str] = arguments
        self.status: ActivityStatus = ActivityStatus.CREATED
        self.__dict__.update(kwargs)
        # self.activity_id = uuid.uuid4()

    def add_files(self, files: list[str]) -> None:
        """Add a list of files to the dataset.

        :param files: List of file URIs.
        :type files: list[str]
        """
        self.files.extend(files)

    def add_file(self, file: str) -> None:
        """Add a file to the dataset.

        :param file: A URI to a single file.
        :type file: str
        """
        self.files.append(file)

    def add_arguments(self, args: list[str]) -> None:
        """Add a list of arguments to the action.

        :param args: List of arguments.
        :type args: list[str]
        """
        self.arguments.extend(args)

    def add_argument(self, arg: str) -> None:
        """Add an argument to the action.

        :param arg: An argument.
        :type arg: str
        """
        self.arguments.append(arg)

    def set_command(self, command: str) -> None:
        """Set the action's command.

        :param command: A command.
        :type command: str
        """
        self.command = command

    def get_status(self) -> ActivityStatus:
        """Get current activity status.

        :return: Current activity status
        :rtype: ActivityStatus
        """
        return self.status

    def generate_response_dict(self, origin_agent_id, last_agent_id, activity_id, data=None, next_activity_id=None):
        """ Create a response to send back to NATS after processing. Should include the following information:

        :param origin_agent_id: (str) the agent that launched the campaign containing this activity.
        :param last_agent_id: (str) the agent that completed the activity of ID... (next line)
        :param activity_id: (str) the ID of the activity created by the origin_agent
        :param data: (str) any data that needs to be sent back to host
        :param next_activity_id: (str) ID of next activity in workflow.
        """

        # Check if we are JSON serializable.  # TODO: Remove JSON requirement.
        try:
            response_data = {'data': data, 'serialize_error': False}
            json.dumps(response_data)
        except (TypeError, OverflowError):  # If we are not
            response_data = {'data': None, 'serialize_error': True}

        # Grab the status
        exec_status = self.get_status()

        response = {'origin_agent_id': origin_agent_id,
                    'last_agent_id': last_agent_id,
                    'activity_id': activity_id,
                    'data': response_data,
                    'exit_status': exec_status,
                    'next_activity_id': next_activity_id}

        return response

    @abstractmethod
    def generate_message(self) -> dict:
        raise NotImplementedError(
            "Method to generate message has not been instantiated."
        )
