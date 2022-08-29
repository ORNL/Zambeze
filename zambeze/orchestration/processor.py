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
import os
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

    async def __disconnected():
        self._logger.info(f"Disconnected from nats... {self._settings.get_nats_connection_uri()}")
        print(f"Disconnected from nats... {self._settings.get_nats_connection_uri()}")

    async def __reconnected():
        self._logger.info(f"Reconnected to nats... {self._settings.get_nats_connection_uri()}")
        print(f"Reconnected to nats... {self._settings.get_nats_connection_uri()}")

    async def __process(self):
        """
        Evaluate and process messages if requested activity is supported.
        """
        self._logger.debug(
            f"Connecting to NATS server: {self._settings.get_nats_connection_uri()}"
        )
        print(f"Connecting to {self._settings.get_nats_connection_uri()}")

        nc = await nats.connect(self._settings.get_nats_connection_uri(),
                                reconnected_cb=self.__reconnected,
                                disconnected_cb=self.__disconnected,
                                connect_timeout=1)

        print("subscribing")
        sub = await nc.subscribe(MessageType.COMPUTE.value)
        self._logger.debug("Waiting for messages")

        print("processor settings")
        print(self._settings.settings)
        print("Changing directory to")
        print(self._settings.settings["plugins"]["All"]["default_working_directory"])
        os.chdir(self._settings.settings["plugins"]["All"]["default_working_directory"])

        while True:
            try:
                print("Grab next msg")
                msg = await sub.next_msg()
                print("message is ")
                print(msg)
                print("message data is ")
                print(msg.data)
                data = json.loads(msg.data)
                print("Unloaded")
                self._logger.debug(f"Message received: {msg.data}")

                if self._settings.is_plugin_configured(data["plugin"].lower()):

                    print("Plugin is configured") 
                    # look for files
                    if "files" in data and data["files"]:
                        await self.__process_files(data["files"])
                        

                    print("Printing content to be executed")
                    self._logger.info("Command to be executed.")
                    self._logger.info(data["cmd"])
                    print(data["cmd"])
                    # perform compute action
                    checked_result = self._settings.plugins.check(
                        plugin_name=data["plugin"].lower(), arguments=data["cmd"]
                    )
                    print(checked_result)
                    for action in checked_result[data["plugin"].lower()]:
                      print(action)
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
        print("Processing files")
        for file in files:
            file_url = urlparse(file)
            print("File_url is")
            print(file_url.geturl())
            if file_url.scheme == "file":
                if not pathlib.Path(file_url.path).exists():
                    raise Exception(f"Unable to find file: {file_url.path}")

            elif file_url.scheme == "globus":

                # Check if we have plugin
                print("Running scheme globus")
                if self._settings.is_plugin_configured("globus"):
                    print("Getting url basename")
                    source_file_name = os.path.basename(file_url.path)
                    print(f"Source file name: {source_file_name}")
                    default_endpoint = self._settings.settings["plugins"]["globus"]["config"]["default_endpoint"]
                    print(f"default endpoint: {default_endpoint}")
                    default_working_dir = self._settings.settings["plugins"]["All"]["default_working_directory"]
                    print(f"default working directory: {default_working_dir}")

                    local_globus_uri = "globus://"
                    local_globus_uri = local_globus_uri + default_endpoint + os.sep
                    local_globus_uri = local_globus_uri + source_file_name
                    print(f"local_globus_uri: {local_globus_uri}")

                    local_posix_uri = "file://"
                    local_posix_uri = local_posix_uri + default_working_dir + os.sep
                    local_posix_uri = local_posix_uri + source_file_name 
                    print(f"local_posix_uri: {local_posix_uri}")
                    print("file url after calling geturl")
                    print(file_url.geturl())
                    message1 =  {
                                "transfer": {
                                    "type": "synchronous",
                                    "items": [
                                      { "source": file_url.geturl(),
                                        "destination": local_globus_uri 
                                      }
                                    ],
                                }
                            }

                    print("Sending message")
                    print(message1)
                    # perform compute action
                    checked_result = self._settings.plugins.check( plugin_name="globus",arguments=message1)
                    print(checked_result)
                    for action in checked_result["globus"]:
                      print(action)
                    
                    self._settings.plugins.run(plugin_name="globus",arguments=message1)

                    message2 ={ 
                              "move_from_globus_collection": {
                                  "items": 
                                  [{
                                    "source": local_globus_uri,
                                    "destination": local_posix_uri
                                  }]
                              }
                            }
                    print("Sending message")
                    print(message2)
                    self._settings.plugins.run(plugin_name="globus",arguments=message2)
                else:
#                    await self.send(
#                        MessageType.COMPUTE.value,
#                        {
#                            "plugin": "globus",
#                            "cmd": [
#                                {
#                                    "transfer": {
#                                        "type": "synchronous",
#                                        "items": [file_url],
#                                    }
#                                },
#                            ],
#                        },
#                    )
                    raise Exception("Needs to be implemented.")
               

                

            elif file_url.scheme == "rsync":
                await self.send(
                    MessageType.COMPUTE.value,
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

    async def send(self, type: MessageType, body: dict) -> None:
        """
        Publish an activity message to the queue.

        :param type: Message type
        :type type: MessageType
        :param body: Message body
        :type body: dict
        """
        self._logger.debug(
            f"Connecting to NATS server: {self._settings.get_nats_connection_uri()}"
        )
        self._logger.debug(f"Sending a '{type}' message")
        nc = await nats.connect(self._settings.get_nats_connection_uri())
        await nc.publish(type, json.dumps(body).encode())
        await nc.drain()
