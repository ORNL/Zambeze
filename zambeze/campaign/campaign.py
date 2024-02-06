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
from queue import Queue
import networkx as nx

from typing import Optional
from .activities.abstract_activity import Activity
from .activities.dag import DAG
from zambeze.settings import ZambezeSettings
from zambeze.auth.globus_auth import GlobusAuthenticator


class Campaign:
    """A Scientific Campaign class to manage and dispatch campaign activities.

    Attributes:
        name (str): The name of the campaign.
        campaign_id (str): A unique identifier for the campaign.
        needs_globus_login (bool): A flag indicating if Globus login is needed.
        activities (list[Activity]): A list of activities associated with the campaign.
        _logger (logging.Logger): Logger for logging information, warnings, and errors.
    """

    def __init__(
        self,
        name: str,
        activities: Optional[list[Activity]] = None,
        logger: Optional[logging.Logger] = None,
        force_login: bool = False
    ) -> None:
        """Initializes a Campaign instance.

        Args:
            name (str): The campaign name.
            activities (Optional[list[Activity]]): A list of activities (default is empty list).
            logger (Optional[logging.Logger]): A logger instance (default is module logger).
        """
        self._logger = logging.getLogger(__name__) if logger is None else logger
        self.name = name
        self.campaign_id = str(uuid.uuid4())
        self.needs_globus_login = False
        self.activities = activities if activities is not None else []

        self.force_login = force_login
        self.result_val = "The total wordcount from these books: gatsby, oz is 93944"

        for activity in self.activities:
            activity.campaign_id = self.campaign_id

    def add_activity(self, activity: Activity) -> None:
        """Adds an activity to the campaign.

        Args:
            activity (Activity): The activity to add to the campaign.
        """
        self._logger.debug(f"Adding activity: {activity.name}")
        activity.campaign_id = self.campaign_id

        if any(file_uri.startswith('globus://') for file_uri in activity.files):
            self.needs_globus_login = True

        elif activity.name == "transfer":
            self.needs_globus_login = True

        self.activities.append(activity)

    def dispatch(self) -> None:
        """Dispatches the set of current activities in the campaign."""
        self._logger.info(f"Number of activities to dispatch: {len(self.activities)}")

        # Initialize ZMQ context and socket
        zmq_context = zmq.Context()
        zmq_socket = zmq_context.socket(zmq.REQ)
        settings = ZambezeSettings()
        zmq_host = settings.settings["zmq"]["host"]
        zmq_port = settings.settings["zmq"]["port"]
        zmq_socket.connect(f"tcp://{zmq_host}:{zmq_port}")

        # Create a DAG to organize activities
        dag = DAG()
        last_activity = None
        token_obj = {}

        if self.needs_globus_login or self.force_login:
            authenticator = GlobusAuthenticator()
            access_token = authenticator.check_tokens_and_authenticate(
                force_login=self.force_login)
            token_obj['globus'] = {'access_token': access_token}

        for activity in self.activities:
            if last_activity is None:
                last_activity = "MONITOR"
                dag.add_node("MONITOR",
                             activity="MONITOR",
                             campaign_id=self.campaign_id)

            transfer_params = {}

            if activity.name == "TRANSFER":
                transfer_params = {'source_file': activity.source_file,
                                   'dest_directory': activity.dest_directory,
                                   'override_existing': activity.override_existing}

            dag.add_node(
                activity.activity_id,
                activity=activity,
                campaign_id=self.campaign_id,
                transfer_tokens=token_obj,
                transfer_params=transfer_params
            )

            dag.add_edge(last_activity, activity.activity_id)
            last_activity = activity.activity_id

        # Add the terminator node
        dag.add_node("TERMINATOR", activity="TERMINATOR", campaign_id=self.campaign_id)
        dag.add_edge(last_activity, "TERMINATOR")

        self._logger.debug(f"Shipping activity DAG of {dag.number_of_nodes()} nodes...")
        serial_dag = pickle.dumps(nx.node_link_data(dag))  # Serialize the DAG

        self._logger.debug("Sending activity DAG via ZMQ...")
        zmq_socket.send(serial_dag)
        self._logger.debug("Activity DAG successfully sent!")
        self._logger.info(f"REPLY: {zmq_socket.recv()}")

    def status(self):

        check_queue = Queue()

        # Dump activities into queue.
        for activity in self.activities:
            check_queue.put(activity)

        # Perform check_queue logic for SDK purposes here.
        # if block:
        #     while True:
        #         print("Ping Flowcept DB instead...")
        #         if check_queue.empty():
        #             break
        #         else:
        #             # To save our computers while we're building this out.
        #             time.sleep(1)
        #
        #         activity_to_check = check_queue.get()

        else:
            raise NotImplementedError("Only blocking checks currently supported!")

    def result(self):
        holder = self.result_val
        return holder
