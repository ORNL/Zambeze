#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import asyncio
import json
import logging
import nats
import subprocess
import threading

from enum import Enum
from nats.errors import TimeoutError
from typing import Optional
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
        self.settings = settings
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )

    def run(self):
        """ """
        self.logger.debug("Starting Agent Processor")
        asyncio.run(self.__process())

    async def __process(self):
        """
        Evaluate messages and process them if requested activity is supported.
        """
        self.logger.debug(
            f"Connecting to NATS server: {self.settings.get_nats_connection_uri()}"
        )
        nc = await nats.connect(self.settings.get_nats_connection_uri())
        sub = await nc.subscribe(MessageType.COMPUTE.value)
        self.logger.debug("Waiting for messages")

        while True:
            try:
                msg = await sub.next_msg()
                data = json.loads(msg.data)
                self.logger.debug(f"Message received: {msg.data}")

                if data["service"].lower() == "shell":
                    cmd = data["arguments"]
                    cmd.insert(0, data["command"])
                    self.logger.debug(f"Running SHELL command: {' '.join(cmd)}")
                    shell_exec = subprocess.Popen(cmd)
                    shell_exec.wait()

            except TimeoutError:
                pass
            except Exception as e:
                print(e)
                exit(1)
