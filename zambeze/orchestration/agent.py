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

from typing import Optional
from .processor import Processor, MessageType
from ..campaign.activities.abstract_activity import Activity, ActivityStatus
from ..settings import ZambezeSettings


class Agent:
    """A distributed Agent.

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Create an object that represents a distributed agent."""
        self.logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.settings = ZambezeSettings()
        self.processor = Processor(settings=self.settings, logger=self.logger)
        self.processor.start()

    def dispatch_activity(self, activity: Activity) -> None:
        """
        Dispatch an activity.

        :param activity: An activity object.
        :type activity: Activity
        """
        asyncio.run(self.__send(MessageType.COMPUTE.value, activity.generate_message()))
        activity.status = ActivityStatus.QUEUED

    async def __send(self, type: MessageType, body: dict) -> None:
        """
        Publish an activity message to the queue.

        :param type: Message type
        :type type: MessageType
        :param body: Message body
        :type body: dict
        """
        self.logger.debug(
            f"Connecting to NATS server: {self.settings.get_nats_connection_uri()}"
        )
        self.logger.debug(f"Sending a '{type}' message")
        nc = await nats.connect(self.settings.get_nats_connection_uri())
        await nc.publish(
            type,
            json.dumps(body).encode(),
        )
        await nc.drain()
