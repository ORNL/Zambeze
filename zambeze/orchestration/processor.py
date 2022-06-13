#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import asyncio
import logging
import nats
import threading

from nats.errors import TimeoutError
from typing import Optional
from ..campaign.actions.abstract_action import ActionType


class Processor(threading.Thread):
    """An Agent processor.

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Create an object that represents a distributed agent."""
        threading.Thread.__init__(self)
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )

    def run(self):
        """ """
        self.logger.debug("Starting Agent Processor")
        asyncio.run(self.__process())

    async def __process(self):
        """ """
        self.logger.debug("Waiting for messages")
        nc = await nats.connect("nats://localhost:4222")
        sub = await nc.subscribe(ActionType.COMPUTE.value)
        self.logger.debug("Waiting for messages")

        while True:
            try:
                msg = await sub.next_msg()
                self.logger.debug(f"Message received: {msg}")
            except TimeoutError:
                pass
            except Exception as e:
                print(e)
                exit(1)
