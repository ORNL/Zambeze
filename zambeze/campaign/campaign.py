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
import networkx as nx  # TODO: move to dag object.

from .activities.abstract_activity import Activity
from .activities.dag import DAG

from zambeze.orchestration.agent.commands import agent_start
from typing import Optional

from zambeze.config import HOST, ZMQ_PORT


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

        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.REQ)

        # TODO: this needs to be REFACTORED AND UNHARDCODED
        #  (use the get_zmq_connection_uri) after we move it somewhere nice.
        self._zmq_socket.connect(f"tcp://{HOST}:{ZMQ_PORT}")

        self._logger.info("[CAMPAIGN] Starting agent...")
        agent_start(self._logger)

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

        # Create and pack a sequential DAG (TODO: relax sequential requirement).
        dag = DAG()
        last_activity = None
        for activity in self.activities:
            if last_activity is None:
                last_activity = "MONITOR"
                # Add one node explicitly
                dag.add_node("MONITOR", activity="MONITOR", campaign_id=self.campaign_id)

            dag.add_node(activity.activity_id, activity=activity, campaign_id=self.campaign_id)

            # Rest of nodes added implicitly via edge.
            dag.add_edge(last_activity, activity.activity_id)
            last_activity = activity.activity_id

        dag.add_node("TERMINATOR", activity="TERMINATOR", campaign_id=self.campaign_id)
        dag.add_edge(last_activity, "TERMINATOR")

        self._logger.debug(f"Shipping activity DAG of {dag.number_of_nodes()} nodes...")

        # Dump dict into bytestring. NetworkX prefers breaking up into nodes and edges (and pickling)
        serial_dag = pickle.dumps(nx.node_link_data(dag))

        self._logger.debug("Activity DAG sending via ZMQ...")
        self._zmq_socket.send(serial_dag)
        self._logger.debug("Activity DAG successfully sent!")
        self._logger.info(f"REPLY: {self._zmq_socket.recv()}")
