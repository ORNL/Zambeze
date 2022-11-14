#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import asyncio
import getpass
import json
import logging
import pathlib

import os
import socket
import threading

from typing import Optional
from urllib.parse import urlparse
from ..settings import ZambezeSettings
from .zambeze_types import ChannelType, QueueType
from .queue.queue_factory import QueueFactory
from .queue.queue_exceptions import QueueTimeoutException


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

        factory = QueueFactory(logger=self._logger)
        args = {
            "ip": self._settings.settings["nats"]["host"],
            "port": self._settings.settings["nats"]["port"],
        }
        self._queue_client = factory.create(QueueType.NATS, args)

    def start(self):
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
                data = msg  # json.loads(msg)
                self._logger.debug("Message received:")
                self._logger.debug(json.dumps(data, indent=4))

                if self._settings.is_plugin_configured(data["plugin"].lower()):

                    # look for files
                    if "files" in data and data["files"]:
                        await self.__process_files(data["files"])

                    self._logger.info("Command to be executed.")
                    self._logger.info(json.dumps(data["cmd"], indent=4))

                    # Running Checks
                    # Returned results should be double nested dict with a tuple of
                    # the form
                    #
                    # "plugin": { "action": (bool, message) }
                    #
                    # The bool is a true or false which indicates if the action
                    # for the plugin is a problem, the message is an error message
                    # or a success statement
                    checked_result = self._settings.plugins.check(
                        plugin_name=data["plugin"].lower(), arguments=data["cmd"]
                    )
                    self._logger.debug(checked_result)

                    if checked_result.errorDetected() is False:
                        self._settings.plugins.run(
                            plugin_name=data["plugin"].lower(), arguments=data["cmd"]
                        )
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
                if self._settings.is_plugin_configured("globus"):
                    source_file_name = os.path.basename(file_url.path)
                    default_endpoint = self._settings.settings["plugins"]["globus"][
                        "config"
                    ]["default_endpoint"]
                    default_working_dir = self._settings.settings["plugins"]["All"][
                        "default_working_directory"
                    ]

                    local_globus_uri = "globus://"
                    local_globus_uri = local_globus_uri + default_endpoint + os.sep
                    local_globus_uri = local_globus_uri + source_file_name

                    local_posix_uri = "file://"
                    local_posix_uri = local_posix_uri + default_working_dir + os.sep
                    local_posix_uri = local_posix_uri + source_file_name

                    # Schedule the Globus transfer
                    transfer_args = {
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

                    checked_result = self._settings.plugins.check(
                        plugin_name="globus", arguments=transfer_args
                    )
                    self._logger.debug(checked_result)
                    self._settings.plugins.run(
                        plugin_name="globus", arguments=transfer_args
                    )

                    # Move from the Globus collection to the default working
                    # directory
                    move_to_file_path_args = {
                        "move_from_globus_collection": {
                            "items": [
                                {
                                    "source": local_globus_uri,
                                    "destination": local_posix_uri,
                                }
                            ]
                        }
                    }
                    checked_result = self._settings.plugins.check(
                        plugin_name="globus", arguments=move_to_file_path_args
                    )
                    self._logger.debug(checked_result)
                    self._settings.plugins.run(
                        plugin_name="globus", arguments=move_to_file_path_args
                    )
                else:
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
                    raise Exception("Needs to be implemented.")

            elif file_url.scheme == "rsync":
                await self._queue_client.send(
                    ChannelType.ACTIVITY,
                    {
                        "plugin": "rsync",
                        "cmd": [
                            {
                                "transfer": {
                                    "source": {
                                        "ip": file_url.netloc,
                                        "path": file_url.path,
                                        "user": file_url.username,
                                    },
                                    "destination": {
                                        "ip": socket.gethostbyname(
                                            socket.gethostname()
                                        ),
                                        "path": str(pathlib.Path().resolve()),
                                        "user": getpass.getuser(),
                                    },
                                }
                            }
                        ],
                    },
                )

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

        await self._queue_client.connect()
        await self._queue_client.send(channel_type, body)
