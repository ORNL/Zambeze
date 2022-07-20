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
import nats
import socket
import threading

from enum import Enum
from nats.errors import TimeoutError
from typing import Optional
from urllib.parse import urlparse
from ..settings import ZambezeSettings


class MessageType(Enum):
    COMPUTE = "z_compute"
    DATA = "z_data"
    STATUS = "z_status"


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

    def run(self):
        """Start the Processor thread."""
        self._logger.debug("Starting Agent Processor")
        asyncio.run(self.__process())

    async def __process(self):
        """
        Evaluate and process messages if requested activity is supported.
        """
        self._logger.debug(
            f"Connecting to NATS server: {self._settings.get_nats_connection_uri()}"
        )
        nc = await nats.connect(self._settings.get_nats_connection_uri())
        sub = await nc.subscribe(MessageType.COMPUTE.value)
        self._logger.debug("Waiting for messages")

        while True:
            try:
                msg = await sub.next_msg()
                data = json.loads(msg.data)
                self._logger.debug(f"Message received: {msg.data}")
                if self._settings.is_plugin_configured(data["plugin"].lower()):
                    # look for files
                    if "files" in data and data["files"]:
                        await self.__process_files(data["files"])

                    # perform compute action
                    self._settings.plugins.run(
                        plugin_name=data["plugin"].lower(), arguments=data["cmd"]
                    )
                self._logger.debug("Waiting for messages")

            except TimeoutError:
                pass
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

        for file in files:
            file_url = urlparse(file)

            if file_url.scheme == "file":
                if not pathlib.Path(file_url.path).exists():
                    raise Exception(f"Unable to find file: {file_url.path}")

            elif file_url.scheme == "rsync":
                await self.send(
                    MessageType.COMPUTE.value,
                    {
                        "plugin": "rsync",
                        "cmd": {
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
                        },
                    },
                )

    async def send(self, type: MessageType, body: dict) -> None:
        """
        Publish an activity message to the queue.

        :param type: Message type
        :type type: MessageType
        :param body: Message body
        :type body: dict
        """
        self._logger.debug(f"hi 1")
        self._logger.debug(
            f"Connecting to NATS server: {self._settings.get_nats_connection_uri()}"
        )
        self._logger.debug(f"Sending a '{type}' message")
        nc = await nats.connect(self._settings.get_nats_connection_uri())
        await nc.publish(type, json.dumps(body).encode())
        await nc.drain()
