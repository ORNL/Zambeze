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
from .processor import Processor
from ..campaign.activity import Activity, ActivityStatus
from ..campaign.actions.abstract_action import ActionType


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
        self.processor = Processor(logger=self.logger)
        self.processor.start()

    def run_activity(self, activity: Activity) -> None:
        """
        Run an activity.
        """
        asyncio.run(self.__send(activity.action.type))
        activity.status = ActivityStatus.QUEUED

    async def __send(self, action_type: ActionType) -> None:
        """

        :param action_type: Action type.
        :type action_type: ActionType
        """
        self.logger.debug("Connecting to NATS server")
        self.logger.debug(f"Sending a '{action_type.value}' message")
        nc = await nats.connect("nats://localhost:4222")
        await nc.publish(action_type.value, b"/bin/echo hello world.")
        await nc.publish(
            action_type.value,
            json.dumps(
                {"task": "hello", "cmd": "/bin/echo", "args": "Hello World!"}
            ).encode(),
        )
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
