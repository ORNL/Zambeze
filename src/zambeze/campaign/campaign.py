# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import zmq
import uuid

from typing import Optional
from .activity import Activity
from .dag import DAG
from zambeze.settings import ZambezeSettings
from zambeze.auth import GlobusAuthenticator


class Campaign:
    """A Scientific Campaign class to manage and dispatch campaign activities."""

    def __init__(
        self,
        name: str,
        activities: list[Activity],
        logger: Optional[logging.Logger] = None,
        force_login: bool = False,
    ) -> None:
        """Initializes a Campaign instance.

        Parameters
        ----------
        name : str
            The name of the campaign.
        activities : list
            List of science activities for processing by Zambeze.
        logger : logging.Logger, optional
            Logger object to flush stderr and stdout.
        force_login : bool
            Boolean whether to force a Globus Auth flow.
        """
        self._logger = logging.getLogger(__name__) if logger is None else logger
        self.name = name
        self.campaign_id = str(uuid.uuid4())
        self.needs_globus_login = False
        self.activities = activities

        self.force_login = force_login
        self.result_val = "The total wordcount from these books: gatsby, oz is 93944"

        for activity in self.activities:
            activity.campaign_id = self.campaign_id

    def add_activity(self, activity: Activity) -> None:
        """Adds an activity to the campaign.

        Parameters
        ----------
        activity : Activity
            The activity to add to the campaign.
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
        """Package the graph in a way that is amenable to send to the
        Zambeze activity queues.
        """
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
        """Dispatches the serialized Directed Acyclic Graph (DAG) of activities via ZeroMQ to the Zambeze service.

        This method prepares a ZeroMQ context and socket, connects to the specified Zambeze
        service host and port (from user's settings), and sends the serialized DAG.

        It handles sending and receiving acknowledgments to ensure
        the DAG is received by the Zambeze service. The method logs all critical steps, errors, and exceptions during the
        dispatch process.

        Notes
        -----
            - This method uses ZeroMQ for communication. Ensure that the network settings are correctly configured.
            - The Zambeze agent must be running and accessible at the specified host and port.
            - The method will log detailed error messages if it fails to send the DAG or does not receive a response within
              the expected time frame. It suggests possible actions to resolve such issues.
        """
        self._logger.info(f"Number of activities to dispatch: {len(self.activities)}")
        zmq_context = zmq.Context()
        zmq_socket = zmq_context.socket(zmq.REQ)
        zmq_socket.setsockopt(zmq.SNDTIMEO, 5000)
        zmq_socket.setsockopt(zmq.RCVTIMEO, 5000)
        zmq_socket.setsockopt(zmq.LINGER, 0)  # Do not linger on close
        settings = ZambezeSettings()
        zmq_socket.connect(
            f"tcp://{settings.settings['zmq']['host']}:{settings.settings['zmq']['port']}"
        )

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
                    self._logger.error(
                        "No response received within timeout period. Please try either: "
                        "\n1. Check your network settings and dispatch again. "
                        "\n2. After installing Zambeze, you may start your agent"
                        ' with "zambeze agent start" and dispatch again.'
                    )
            else:
                self._logger.error(
                    "Unable to send: message queue not ready. "
                    "Please check your network settings and restart your Zambeze agent."
                )
        except zmq.Again:
            self._logger.error(
                "Operation timed out: Zambeze agent might be unreachable."
                " \nAfter installing Zambeze, you may start your agent"
                ' with "zambeze agent start" and dispatch again.'
            )
        finally:
            try:
                self._logger.debug(
                    "Cleaning up message queues and closing connections."
                )
                zmq_socket.close()
                zmq_context.term()
                self._logger.debug("Cleanup completed.")

            except Exception as e:
                self._logger.error(f"Error during cleanup: {str(e)}")
