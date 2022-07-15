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
import pathlib
import pickle
import zmq

from typing import Optional
from uuid import uuid4
from zambeze.orchestration.processor import Processor, MessageType
from zambeze.campaign.activities.abstract_activity import Activity, ActivityStatus
from zambeze.settings import ZambezeSettings


class Agent:
    """A distributed Agent.

    :param conf_file: Path to configuration file
    :type conf_file: Optional[pathlib.Path]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        conf_file: Optional[pathlib.Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object that represents a distributed agent."""
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )

        self.agent_id = uuid4()

        self._settings = ZambezeSettings(conf_file=conf_file, logger=self._logger)
        self._processor = Processor(settings=self._settings, logger=self._logger)
        self._processor.start()

        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.REP)
        self.zmq_socket.bind("tcp://*:5555")

        self.receive_activity_from_campaign()

    def receive_activity_from_campaign(self):

        # Receive and unwrap the activity message from ZMQ.
        activity_message = pickle.loads((self.zmq_socket.recv()))
        self.dispatch_activity(activity_message)

        # Receive confirmation of message sent.
        # TODO: TYLER.
        resp_object = {'send_status': 'SUCCESS', 'agent_id': self.agent_id}

    @property
    def processor(self) -> Processor:
        return self._processor

    def dispatch_activity(self, activity: Activity) -> None:
        """
        Dispatch an activity.

        :param activity: An activity object.
        :type activity: Activity
        """
        asyncio.run(
            self.processor.send(MessageType.COMPUTE.value, activity.generate_message())
        )
        activity.status = ActivityStatus.QUEUED
