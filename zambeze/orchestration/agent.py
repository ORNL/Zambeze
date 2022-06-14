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

    def run_activity(self, activity: Activity) -> None:
        """
        Run an activity.

        :param activity: An activity object.
        :type activity: Activity
        """
        # TODO: evaluate activity and generate messages
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
        await nc.publish(type, json.dumps(body).encode())
        await nc.drain()


# def __configure_logging():
#     """ " Configure logging options and format."""
#     logger.setLevel(logging.INFO)
#     ch = logging.StreamHandler()
#     ch.setLevel(logging.INFO)
#     formatter = logging.Formatter(
#         "[Zambeze Agent] [%(levelname)s] %(asctime)s - %(message)s"
#     )
#     ch.setFormatter(formatter)
#     logger.addHandler(ch)


async def main():
    # logging
    # __configure_logging()
    # logger.info("Starting Zambeze Agent")

    nc = await nats.connect("localhost")
    knownmsg = ["z_compute", "z_data"]

    async def handle(msg):
        if msg.subject in knownmsg:
            print(msg)
        else:
            print("Unknown message")

    # sub = await nc.subscribe("execapp", cb=handle)
    # logger.info("Waiting for message")
    sub2 = await nc.subscribe("z_compute")
    while True:
        try:
            msg = await sub2.next_msg()
            print("Message received", msg)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
