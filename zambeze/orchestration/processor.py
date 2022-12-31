#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Standard imports
import asyncio
import logging
import os
import socket
import threading
import time
import uuid

from typing import Optional
from dataclasses import asdict

# Third party imports
import getpass
import json
import pathlib

from urllib.parse import urlparse

# Local imports
from ..settings import ZambezeSettings
from .message.abstract_message import AbstractMessage
from .message.message_factory import MessageFactory
from .queue.queue_factory import QueueFactory
from .queue.queue_exceptions import QueueTimeoutException
from .zambeze_types import ChannelType, QueueType, MessageType, ActivityType


class Processor(threading.Thread):
    """An Agent processor.

    :param settings: Zambeze settings
    :type settings: ZambezeSettings
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        settings: ZambezeSettings,
        logger: Optional[logging.Logger] = None,
        agent_id: Optional[str] = None) -> None:
        """Create an object that represents a distributed agent."""
        threading.Thread.__init__(self)
        self._settings = settings
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self._agent_id = agent_id
        queue_factory = QueueFactory(logger=self._logger)
        args = {
            "ip": self._settings.settings["nats"]["host"],
            "port": self._settings.settings["nats"]["port"],
        }
        self._queue_client = queue_factory.create(QueueType.NATS, args)

        self._msg_factory = MessageFactory(logger=self._logger)

    def run(self):
        """Start the Processor thread."""
        asyncio.run(self.__process())

    async def __process(self):
        """
        Evaluate and process messages if requested activity is supported.
        """
        self._logger.debug(
            f"Connecting to Queue ({self._queue_client.type}) server: "
            f"{self._queue_client.type}"
        )

        await self._queue_client.connect()

        await self._queue_client.subscribe(ChannelType.ACTIVITY)

        default_working_dir = self._settings.settings["plugins"]["All"][
            "default_working_directory"
        ]
        self._logger.debug(f"Moving to working directory {default_working_dir}")
        os.chdir(default_working_dir)

        while True:
            try:
                print("Receiving first message")
                msg = await self._queue_client.nextMsg(ChannelType.ACTIVITY)
                print("Message received")
                print(msg)
                self._logger.debug("Message received:")

                if msg.type != MessageType.ACTIVITY:
                    print("Non activity detected")
                    self._logger.debug(
                        "Non-activity message received on" "ACTIVITY channel"
                    )
                else:
                    print("dump 1")
                    self._logger.debug(json.dumps(asdict(msg.data), indent=4))
                    # Determine what kind of activity it is
                    if msg.data.body.type == "SHELL":
                        # Determine if the shell activity has files that
                        # Need to be moved to be executed
                        if msg.data.body.files:
                            if len(msg.data.body.files) > 0:
                                await self.__process_files(
                                        msg.data.body.files,
                                        msg.data.body.campaign_id,
                                        msg.data.body.activity_id)

                        self._logger.info("Command to be executed.")
                        print("dump 2")
                        # self._logger.info(json.dumps(msg.data["cmd"], indent=4))

                        # Running Checks
                        # Returned results should be double nested dict with a tuple of
                        # the form
                        #
                        # "plugin": { "action": (bool, message) }
                        #
                        # The bool is a true or false which indicates if the action
                        # for the plugin is a problem, the message is an error message
                        # or a success statement
                        checked_result = self._settings.plugins.check(msg)
                        self._logger.debug(checked_result)

                        if checked_result.errorDetected() is False:
                            self._settings.plugins.run(msg)
                        else:
                            self._logger.debug(
                                "Skipping run - error detected when running "
                                "plugin check"
                            )

                    else:
                        raise Exception("Only SHELL currently supported")
                self._logger.debug("Waiting for messages")

            except QueueTimeoutException as e:
                print(e)
            except Exception as e:
                print(e)
                exit(1)

    async def __process_files(
            self,
            files: list[str],
            campaign_id: str,
            activity_id: str) -> None:
        """
        Process a list of files by generating transfer requests when files are
        not available locally.

        :param files: List of files
        :type files: list[str]
        """
        self._logger.debug("Processing files...")
        for file_path in files:
            file_url = urlparse(file_path)
            print(f"File to parse {file_url}")
            if file_url.scheme == "file":
                if not pathlib.Path(file_url.path).exists():
                    raise Exception(f"Unable to find file: {file_url.path}")

            elif file_url.scheme == "globus":
                if "globus" not in self._settings.settings["plugins"]:
                    raise Exception("It doesn't look like Globus is configured locally")

                print("Globus executing")
                print(file_url.path)
                # Check if we have plugin
                source_file_name = os.path.basename(file_url.path)
                print(f"Source file_name {source_file_name}")
                print("Settings")
                print(self._settings.settings["plugins"])
                default_endpoint = self._settings.settings["plugins"]["globus"]["config"]["default_endpoint"]
                print(f"default endpoint {default_endpoint}")
                default_working_dir = self._settings.settings["plugins"]["All"][
                    "default_working_directory"
                ]
                print(f"default working directory {default_working_directory}")

                local_globus_uri = (
                    f"globus://{default_endpoint}{os.sep}" f"source_file_name"
                )

                local_posix_uri = (
                    f"file://{default_working_dir}{os.sep}" f"{source_file_name}"
                )

                msg_template_transfer = self._msg_factory.createTemplate(
                    MessageType.ACTIVITY,
                    ActivityType.PLUGIN,
                    {"plugin": "globus", "action": "transfer"},
                )

                #msg_template_transfer[1].message_id = str(uuid.uuid4())
                msg_template_transfer[1].activity_id = activity_id
                msg_template_transfer[1].agent_id = self._agent_id
                msg_template_transfer[1].campaign_id = campaign_id
                msg_template_transfer[1].credential = {}
                msg_template_transfer[1].submission_time = str(int(time.time()))
                msg_template_transfer[1].body.transfer.type = "synchronous"
                msg_template_transfer[1].body.transfer.items[
                    0
                ].source = file_url.geturl()
                msg_template_transfer[1].body.transfer.items[0].destination = (
                    local_globus_uri,
                )

                print(asdict(msg_template_transfer))
                # Will validate the message fields and then make it immutable
                immutable_msg = self._msg_factory.create(msg_template_transfer)

                checked_result = self._settings.plugins.check(immutable_msg)
                self._logger.debug(checked_result)

                # Move from the Globus collection to the default working
                # directory
                msg_template_move = self._msg_factory.createTemplate(
                    MessageType.ACTIVITY,
                    ActivityType.PLUGIN,
                    {"plugin": "globus", "action": "move_from_globus_collection"},
                )

                #msg_template_move[1].message_id = str(uuid.uuid4())
                msg_template_move[1].activity_id = activity_id
                msg_template_move[1].agent_id = self._agent_id
                msg_template_move[1].campaign_id = campaign_id
                msg_template_move[1].credential = {}
                msg_template_move[1].submission_time = str(int(time.time()))
                msg_template_move[1].body.move_to_globus_collection.items[
                    0
                ].source = local_globus_uri
                msg_template_move[1].body.move_to_globus_collection.items[
                    0
                ].destination = local_posix_uri

                # Will validate the message fields and then make it immutable
                immutable_msg_move = self._msg_factory.create(msg_template_move)
                checked_result = self._settings.plugins.check(immutable_msg_move)
                self._logger.debug(checked_result)

                await self._queue_client.send(ChannelType.ACTIVITY, immutable_msg)
                await self._queue_client.send(ChannelType.ACTIVITY, immutable_msg_move)

            elif file_url.scheme == "rsync":

                msg_template = self._msg_factory.createTemplate(
                    MessageType.ACTIVITY,
                    ActivityType.PLUGIN,
                    {"plugin": "rsync", "action": "transfer"},
                )

                msg_template[1].body.transfer.items[0].source.ip = file_url.netloc
                msg_template[1].body.transfer.items[0].source.path = file_url.path
                msg_template[1].body.transfer.items[
                    0
                ].source.username = file_url.username
                msg_template[1].body.transfer.items[
                    0
                ].destination.ip = socket.gethostbyname(socket.gethostname())
                msg_template[1].body.transfer.items[0].destination.path = str(
                    pathlib.Path().resolve()
                )
                msg_template[1].body.transfer.items[
                    0
                ].destination.username = getpass.getuser()
                # Will validate the message fields and then make it immutable
                msg = self._msg_factory.create(msg_template)
                await self._queue_client.send(ChannelType.ACTIVITY, msg)

    # body needs to be changed to AbstractMessage
    async def send(self, channel_type: ChannelType, msg: AbstractMessage) -> None:
        """
        Publish an activity message to the queue.

        :param type: Message type
        :type type: MessageType
        :param body: Message body
        :type body: dict
        """
        self._logger.debug(
            f"Connecting to Queue ({self._queue_client.type}) "
            f"server: {self._queue_client.uri}"
        )
        self._logger.debug(f"Sending a '{channel_type.value}' message")

        print("Processor sending")
        print(msg)
        await self._queue_client.connect()
        self._logger.debug(json.dumps(asdict(msg.data), indent=4))
        await self._queue_client.send(channel_type, msg)
