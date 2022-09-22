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
    RESPONSE = "z_response"


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
        self._logger.debug("[processor] Starting Agent Processor")
        asyncio.run(self.__process())

    async def __disconnected(self):
        self._logger.info(
            f"[processor] Disconnected from nats... {self._settings.get_nats_connection_uri()}"
        )

    async def __reconnected(self):
        self._logger.info(
            f"[processor] Reconnected to nats... {self._settings.get_nats_connection_uri()}"
        )

    async def __process(self):
        """
        Evaluate and process messages if requested activity is supported.
        """
        self._logger.debug(
            f"[processor] Connecting to NATS server: {self._settings.get_nats_connection_uri()}"
        )
        print(f"[processor] Connecting to {self._settings.get_nats_connection_uri()}")

        nc = await nats.connect(
            self._settings.get_nats_connection_uri(),
            reconnected_cb=self.__reconnected,
            disconnected_cb=self.__disconnected,
            connect_timeout=1,
        )

        sub = await nc.subscribe(MessageType.COMPUTE.value)
        self._logger.debug("[processor] Waiting for messages B")

        self._logger.debug("[processor] About to get default working dir")
        self._logger.debug(self._settings.settings)
        default_working_dir = self._settings.settings["plugins"]["All"][
            "default_working_directory"
        ]
        self._logger.debug(f"Moving to working directory {default_working_dir}")
        os.chdir(default_working_dir)

        while True:
            try:
                msg = await sub.next_msg()
                data = json.loads(msg.data)
                self._logger.debug("[processor] Message received:")
                self._logger.debug(json.dumps(data, indent=4))

                if self._settings.is_plugin_configured(data["plugin"].lower()):

                    # look for files
                    if "files" in data and data["files"]:
                        await self.__process_files(data["files"])

                    self._logger.info("[processor] Command to be executed.")
                    self._logger.info(json.dumps(data["cmd"], indent=4))

                    self._logger.info("[processor] ARE WE STUCK???.")
                    # Running Checks
                    # checked_result = self._settings.plugins.check(
                    #     plugin_name=data["plugin"].lower(), arguments=data["cmd"]
                    # )

                    self._logger.info("[processor] I DELETED CHECKED RESULT!")
                    # self._logger.debug(f"[processor] checked result {checked_result}")

                    self._logger.debug("[processor] PRE PLUGIN RUN")
                    # perform compute action
                    self._settings.plugins.run(
                        plugin_name=data["plugin"].lower(), arguments=data["cmd"]
                    )

                    # self.return_response_to_nats({'hi': 'bye', 'activity_id': 'hello1'})

                    # TODO: Tyler -- BRING BACK THIS RESULT RETURN.
                    await self.send(type=MessageType.RESPONSE.value, body={'status': 'completed'})

                    self._logger.debug("[processor] POST PLUGIN RUN")

                self._logger.debug("[processor] Waiting for messages A")

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

    # def return_response_to_nats(self, resp_data):
    #     """Send response back upstream to all relevant NATS servers.
    #
    #     :param resp_data: (dict) response object created by generate_response_dict().
    #
    #     :return None
    #     """
    #
    #     self._logger.info("A1")
    #
    #     channels = []
    #
    #     # Step 1. Select the proper NATS channels.
    #     # --- First NATS channel is the 'status' for the origin_agent.
    #     origin_channel = f"update.origin.{resp_data['activity_id']}"
    #     channels.append(origin_channel)
    #
    #     self._logger.info("A2")
    #
    #     # --- Second NATS channel is one awaiting the 'activity_id'.
    #     if resp_data['next_activity_id'] is not None:
    #         next_in_wf_channel = f"update.workflow.{resp_data['activity_id']}"
    #         channels.append(next_in_wf_channel)
    #         self._logger.info("A3")
    #
    #     # Step 2. Send to the proper NATS channels.
    #     self._logger.info(
    #         f"Connecting to NATS server: {self._settings.get_nats_connection_uri()}"
    #     )
    #
    #     self._logger.info("A4")
    #
    #     self._logger.info(f"Sending a 'magoo' message on channels: {channels}")
    #     nc = await nats.connect(self._settings.get_nats_connection_uri())
    #
    #     for channel in channels:
    #         await nc.publish(channel, json.dumps(resp_data).encode())
    #         await nc.drain()
    #     self._logger.info(f"Sent all messageseses")



