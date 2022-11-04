#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import asyncio
import logging
import pathlib
import pickle
import zmq

from time import time
from typing import Optional
from uuid import uuid4

from zambeze.orchestration.db.dao.activity_dao import ActivityDAO
from zambeze.orchestration.db.model.activity_model import ActivityModel

from ..processor import Processor
from ..zambeze_types import ChannelType
from ...campaign.activities.abstract_activity import Activity, ActivityStatus
from ...settings import ZambezeSettings


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
        self._agent_id = uuid4()

        self._settings = ZambezeSettings(conf_file=conf_file, logger=self._logger)
        self._processor = Processor(settings=self._settings, logger=self._logger)
        self._processor.start()

        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.REP)
        self._logger.info(f"Binding to: {self._settings.get_zmq_connection_uri()}")
        self._zmq_socket.bind(self._settings.get_zmq_connection_uri())
        self._activity_dao = ActivityDAO(self._logger)

        while True:
            self._logger.info("Waiting for new activities from campaign(s)...")
            self._receive_activity_from_campaign()

    def _receive_activity_from_campaign(self) -> None:
        """
        Receive activity messages via ZMQ
        """
        # Receive and unwrap the activity message from ZMQ.
        activity_message = pickle.loads((self._zmq_socket.recv()))
        self._logger.info(f"Received message from campaign: {activity_message}")

        activity = ActivityModel(agent_id=str(self._agent_id),
                                 created_at=int(time()*1000))
        self._logger.info(f"Creating activity in the DB: {activity}")
        self._activity_dao.insert(activity)
        self._logger.info("Saved in the DB!")
        # Dispatch the activity!
        self.dispatch_activity(activity_message)
        self._zmq_socket.send(b"Agent successfully dispatched task!")

    @property
    def processor(self) -> Processor:
        return self._processor

    def dispatch_activity(self, activity: Activity) -> None:
        """
        Dispatch an activity.

        :param activity: An activity object.
        :type activity: Activity
        """
        self._logger.error("Received activity for dispatch...")
        asyncio.run(
            self.processor.send(ChannelType.ACTIVITY, activity.generate_message())
        )
        activity.status = ActivityStatus.QUEUED
