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

from typing import Optional

# Third party imports
import getpass
import json
import pathlib

from urllib.parse import urlparse

# Local imports
from ..settings import ZambezeSettings
from .message.message_factory import MessageFactory
from .queue.queue_factory import QueueFactory
from .queue.queue_exceptions import QueueTimeoutException
from .zambeze_types import ChannelType, QueueType, MessageType


class Processor(threading.Thread):
    """An Agent processor.

    :param settings: Zambeze settings
    :type settings: ZambezeSettings
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self, settings: ZambezeSettings, logger: Optional[logging.Logger] = None
    ) -> None:
        """Create an object that represents a distributed agent."""
        threading.Thread.__init__(self)
        self._settings = settings
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )

        queue_factory = QueueFactory(logger=self._logger)
        args = {
            "ip": self._settings.settings["nats"]["host"],
            "port": self._settings.settings["nats"]["port"],
        }
        self._queue_client = queue_factory.create(QueueType.NATS, args)

        self._msg_factory = MessageFactory(self._settings.plugins, logger=self._logger)

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

                msg = await self._queue_client.nextMsg(ChannelType.ACTIVITY)
                self._logger.debug("Message received:")
                self._logger.debug(json.dumps(msg.data, indent=4))

                if self._settings.is_plugin_configured(msg.data["plugin"].lower()):

                    # look for files
                    if "files" in msg.data and msg.data["files"]:
                        await self.__process_files(msg.data["files"])

                    self._logger.info("Command to be executed.")
                    self._logger.info(json.dumps(msg.data["cmd"], indent=4))

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
                    #                        self._settings.plugins.run(
                    #                            plugin_name=msg.data["plugin"].lower(),
                    #                            arguments=msg.data["cmd"]
                    #                        )
                    else:
                        self._logger.debug(
                            "Skipping run - error detected when running plugin check"
                        )

                self._logger.debug("Waiting for messages")

            except QueueTimeoutException as e:
                print(e)
            except Exception as e:
                print(e)
                exit(1)

    async def __process_files(self, files: list[str]) -> None:
        """
        Process a list of files by generating transfer requests when files are
        not available locally.

        :param files: List of files
        :type files: list[str]
        """
        self._logger.debug("Processing files...")
        for file_path in files:
            file_url = urlparse(file_path)
            if file_url.scheme == "file":
                if not pathlib.Path(file_url.path).exists():
                    raise Exception(f"Unable to find file: {file_url.path}")

            elif file_url.scheme == "globus":

                # Check if we have plugin
                source_file_name = os.path.basename(file_url.path)
                default_endpoint = self._settings.settings["plugins"]["globus"][
                    "config"
                ]["default_endpoint"]
                default_working_dir = self._settings.settings["plugins"]["All"][
                    "default_working_directory"
                ]

                local_globus_uri = (
                    f"globus://{default_endpoint}{os.sep}" f"source_file_name"
                )

                local_posix_uri = (
                    f"file://{default_working_dir}{os.sep}" f"{source_file_name}"
                )

                msg_template = self._msg_factory.createTemplate(
                    MessageType.ACTIVITY, "globus", "transfer"
                )

                msg_template[1]["body"]["cmd"] = [
                    {
                        "transfer": {
                            "type": "synchronous",
                            "items": [
                                {
                                    "source": file_url.geturl(),
                                    "destination": local_globus_uri,
                                }
                            ],
                        }
                    }
                ]
                # Will validate the message fields and then make it immutable
                immutable_msg = self._msg_factory.create(msg_template)

                checked_result = self._settings.plugins.check(immutable_msg)
                self._logger.debug(checked_result)

                # Move from the Globus collection to the default working
                # directory
                msg_template_move = self._msg_factory.createTemplate(
                    MessageType.ACTIVITY, "globus", "move_from_globus_collection"
                )

                # Dependency on transfer needs to be defined
                msg_template_move[1]["body"]["cmd"] = [
                    {
                        "move_from_globus_collection": {
                            "items": [
                                {
                                    "source": local_globus_uri,
                                    "destination": local_posix_uri,
                                }
                            ]
                        }
                    }
                ]
                # Will validate the message fields and then make it immutable
                immutable_msg_move = self._msg_factory.create(msg_template_move)
                checked_result = self._settings.plugins.check(immutable_msg_move)
                self._logger.debug(checked_result)

                await self._queue_client.send(ChannelType.ACTIVITY, immutable_msg)
                await self._queue_client.send(ChannelType.ACTIVITY, immutable_msg_move)

                # If the local agent does not support Globus we will need to
                # send a request to to nats for someone else to handle the
                # transfer
                # await self.send(
                #     MessageType.COMPUTE.value,
                #     {
                #         "plugin": "globus",
                #         "cmd": [
                #             {
                #                 "transfer": {
                #                     "type": "synchronous",
                #                     "items": [file_url],
                #                 }
                #             },
                #         ],
                #     },
                # )
                # raise Exception("Needs to be implemented.")

            elif file_url.scheme == "rsync":

                msg_template = self._msg_factory.createTemplate(
                    MessageType.ACTIVITY, "rsync", "transfer"
                )

                msg_template[1]["body"]["cmd"] = [
                    {
                        "transfer": {
                            "source": {
                                "ip": file_url.netloc,
                                "path": file_url.path,
                                "user": file_url.username,
                            },
                            "destination": {
                                "ip": socket.gethostbyname(socket.gethostname()),
                                "path": str(pathlib.Path().resolve()),
                                "user": getpass.getuser(),
                            },
                        }
                    }
                ]
                # Will validate the message fields and then make it immutable
                msg = self._msg_factory.create(msg_template)
                await self._queue_client.send(ChannelType.ACTIVITY, msg)

    # body needs to be changed to AbstractMessage
    async def send(self, channel_type: ChannelType, body: dict) -> None:
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

        msg = self._msg_factory.create(body)
        await self._queue_client.connect()
        await self._queue_client.send(channel_type, msg)
