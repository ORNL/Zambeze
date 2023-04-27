#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import zmq
import pickle
import uuid

from .activities.abstract_activity import Activity

from typing import Optional

from zambeze.settings import ZambezeSettings


class Campaign:
    """A Scientific Campaign.

    :param name: The campaign name.
    :type name: str
    :param activities: List of activities.
    :type activities: Optional[list[Activity]]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        activities: list[Activity] = [],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object that represents a science campaign."""
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self.name: str = name

        self.campaign_id = str(uuid.uuid4())

        self.activities: list[Activity] = activities
        for index in range(0, len(self.activities)):
            self.activities[index].campaign_id = self.campaign_id

    def add_activity(self, activity: Activity) -> None:
        """Add an activity to the campaign.

        :param activity: An activity object.
        :type activity: Activity
        """
        self._logger.debug(f"Adding activity: {activity.name}")
        activity.campaign_id = self.campaign_id
        self.activities.append(activity)

    def dispatch(self) -> None:
        """Dispatch the set of current activities in the campaign."""
        self._logger.info(f"Number of activities to dispatch: {len(self.activities)}")

        # Connecting to ZMQ
        _zmq_context = zmq.Context()
        _zmq_socket = _zmq_context.socket(zmq.REQ)

        _settings = ZambezeSettings()

        zmq_host = _settings.settings["zmq"]["host"]
        zmq_port = _settings.settings["zmq"]["port"]

        _zmq_socket.connect(f"tcp://{zmq_host}:{zmq_port}")

        for activity in self.activities:
            self._logger.debug(f"Running activity: {activity.name}")

            # Dump dict into bytestring (.dumps)
            serial_activity = pickle.dumps(activity)
            self._logger.debug("Sending serial activity")
            _zmq_socket.send(serial_activity)
            self._logger.debug("Serial activity sent.")
            self._logger.info(f"REPLY: {_zmq_socket.recv()}")
