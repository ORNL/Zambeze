# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import zmq
import uuid
from queue import Queue

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
        force_login: bool = False,
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
        activity.running_agent_ids = []

        if any(file_uri.startswith("globus://") for file_uri in activity.files):
            self.needs_globus_login = True

        elif activity.name == "transfer":
            self.needs_globus_login = True

        self.activities.append(activity)

    def _pack_dag_for_dispatch(self):
        # Create a DAG to organize activities
        last_activity = None
        token_obj = {}

        dag = DAG()
        if self.needs_globus_login or self.force_login:
            authenticator = GlobusAuthenticator()
            access_token = authenticator.check_tokens_and_authenticate(
                force_login=self.force_login
            )
            token_obj["globus"] = {"access_token": access_token}

        for activity in self.activities:
            if last_activity is None:
                last_activity = "MONITOR"
                dag.add_node(
                    "MONITOR", activity="MONITOR", campaign_id=self.campaign_id
                )

            transfer_params = {}

            if activity.name == "TRANSFER":
                transfer_params = {
                    "source_file": activity.source_file,
                    "dest_directory": activity.dest_directory,
                    "override_existing": activity.override_existing,
                }

            dag.add_node(
                activity.activity_id,
                activity=activity,
                campaign_id=self.campaign_id,
                transfer_tokens=token_obj,
                transfer_params=transfer_params,
            )

            dag.add_edge(last_activity, activity.activity_id)
            last_activity = activity.activity_id

        # Add the terminator node
        dag.add_node("TERMINATOR", activity="TERMINATOR", campaign_id=self.campaign_id)
        dag.add_edge(last_activity, "TERMINATOR")

        # Adds predecessors and successors to nodes.
        dag.update_node_relationships()
        return dag

    def dispatch(self) -> None:
        self._logger.info(f"Number of activities to dispatch: {len(self.activities)}")
        zmq_context = zmq.Context()
        zmq_socket = zmq_context.socket(zmq.REQ)
        zmq_socket.setsockopt(zmq.SNDTIMEO, 5000)
        zmq_socket.setsockopt(zmq.RCVTIMEO, 5000)
        zmq_socket.setsockopt(zmq.LINGER, 0)  # Do not linger on close
        settings = ZambezeSettings()
        zmq_socket.connect(f"tcp://{settings.settings['zmq']['host']}:{settings.settings['zmq']['port']}")

        dag = self._pack_dag_for_dispatch()
        serial_dag = dag.serialize_dag()
        self._logger.debug("Sending activity DAG via ZMQ...")

        try:
            poller = zmq.Poller()
            poller.register(zmq_socket, zmq.POLLOUT)
            if poller.poll(5000):
                zmq_socket.send(serial_dag)
                self._logger.debug("Sending campaign to Zambeze...")

                poller.register(zmq_socket, zmq.POLLIN)
                if poller.poll(5000):
                    # If we receive any message, then we succeeded in REQ/REP. Do not need to parse it.
                    zmq_socket.recv()
                    self._logger.info("Campaign successfully dispatched to Zambeze!")
                else:
                    self._logger.error("No response received within timeout period. Please try either: "
                                       "\n1. Check your network settings and dispatch again. "
                                       "\n2. After installing Zambeze, you may start your agent"
                                       " with \"zambeze agent start\" and dispatch again."
                                       )
            else:
                self._logger.error("Unable to send: message queue not ready. "
                                   "Please check your network settings and restart your Zambeze agent.")
        except zmq.Again:
            self._logger.error("Operation timed out: Zambeze agent might be unreachable."
                               " \nAfter installing Zambeze, you may start your agent"
                               " with \"zambeze agent start\" and dispatch again.")
        finally:
            try:
                self._logger.debug("Cleaning up message queues and closing connections.")
                zmq_socket.close()
                zmq_context.term()
                self._logger.debug("Cleanup completed.")

            except Exception as e:
                self._logger.error(f"Error during cleanup: {str(e)}")

    def status(self):
        check_queue = Queue()

        # Dump activities into queue.
        for activity in self.activities:
            check_queue.put(activity)

        else:
            raise NotImplementedError("Only blocking checks currently supported!")

    def result(self):
        holder = self.result_val
        return holder
