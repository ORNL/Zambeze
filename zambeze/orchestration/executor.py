#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import json
import logging
import os
import pathlib
import threading

from queue import Queue
from typing import Optional
from dataclasses import asdict
from urllib.parse import urlparse

from ..settings import ZambezeSettings
from .message.message_factory import MessageFactory
from .queue.queue_exceptions import QueueTimeoutException
from zambeze.orchestration.message.transfer_hippo import TransferHippo


class Executor(threading.Thread):
    """An Agent executor (formerly the PROCESSOR).

    :param settings: Zambeze settings
    :type settings: ZambezeSettings
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        settings: ZambezeSettings,
        logger: Optional[logging.Logger] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        """Create an object that represents a distributed agent."""
        threading.Thread.__init__(self)
        self._settings = settings
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )

        self.to_process_q = Queue()
        self.to_status_q = Queue()
        self.to_new_activity_q = Queue()
        self.to_monitor_q = Queue()

        self._logger.info("[EXECUTOR] Created executor! ")
        self._agent_id = agent_id

        self._msg_factory = MessageFactory(logger=self._logger)
        self._transfer_hippo = TransferHippo(
            agent_id=self._agent_id, logger=self._logger, settings=self._settings
        )

        self._logger.info("[EXECUTOR] Successfully initialized Executor!")

    def run(self):
        """Override the Thread 'run' method to instead run our
        process when Thread.start() is called!"""
        # Create persisent "__process()"
        self.__process()

    def __process(self):
        """
        Evaluate and process messages if requested activity is supported.
        """

        self._logger.info("[EXECUTOR] In __process! ")

        # Change to the agent's desired working directory.
        default_working_dir = self._settings.settings["plugins"]["All"][
            "default_working_directory"
        ]
        self._logger.info(
            f"[EXECUTOR] Moving to working directory {default_working_dir}"
        )
        os.chdir(default_working_dir)

        while True:
            try:

                self._logger.info("[EXECUTOR] Retrieving a message! ")
                dag_msg = self.to_process_q.get()

                # Check 1. If MONITOR, then we want to STICK the process.
                monitor_term = False

                self._logger.info(f"EXECUTOR!!! {dag_msg}")
                if dag_msg[0] == "MONITOR":

                    # Now we want to hold (and periodically log) until all subtasks are complete.
                    dag_dict = dict()

                    # Add all activities (besides the monitor) to our dict.
                    for activity_id in dag_msg[1]["all_activity_ids"]:
                        if activity_id == "MONITOR":
                            continue
                        dag_dict[activity_id] = "PROCESSING"

                    while True:
                        # Quick check to see if all values are NOT "PROCESSING"
                        proc_count = sum(x == 'PROCESSING' for x in dag_dict.values())

                        if proc_count == 0:
                            monitor_term = True
                            break

                        status_msg = self.to_monitor_q.get()
                        if status_msg.activity_id in dag_dict:
                            status = status_msg.status
                            dag_dict[status_msg.activity_id] = status

                elif dag_msg[0] == "TERMINATOR":
                    # TODO: TERMINATE AND SEND BACK!
                    pass

                # If we were just monitoring, go to top of loop; start over.
                if monitor_term:
                    continue

                activity_msg = dag_msg[1]['activity']
                # if we need files, check if present (and if not, go get them).
                self._logger.info("[Executor] Message received:")
                self._logger.info(json.dumps(asdict(activity_msg.data), indent=4))
                if activity_msg.data.body.type == "SHELL":
                    self._logger.info("[Executor] Message received:")
                    self._logger.info(json.dumps(asdict(activity_msg.data), indent=4))

                    # Determine if the shell activity has files that
                    # Need to be moved to be executed
                    if activity_msg.data.body.files:
                        if len(activity_msg.data.body.files) > 0:
                            self.__process_files(
                                activity_msg.data.body.files,
                                activity_msg.data.campaign_id,
                                activity_msg.data.activity_id,
                            )

                    # Running Checks
                    # Returned results should be double nested dict with a tuple of
                    # the form
                    #
                    # "plugin": { "action": (bool, message) }
                    #
                    # The bool is a true or false which indicates if the action
                    # for the plugin is a problem, the message is an error message
                    # or a success statement

                    # TODO -- bring these back.
                    # self._logger.info("[EXECUTOR] Command to be executed.")
                    # self._logger.info(json.dumps(data["cmd"], indent=4))

                    # TODO: TYLER -- WAIT until we have the eligible resources.

                    checked_result = self._settings.plugins.check(dag_msg)
                    self._logger.debug(f"[EXECUTOR] Checked result: {checked_result}")

                    if checked_result.error_detected() is False:
                        self._settings.plugins.run(activity_msg)
                    else:
                        self._logger.debug(
                            "Skipping run - error detected when running " "plugin check"
                        )
                else:
                    raise Exception("Only SHELL currently supported")

                self._logger.info("[EXECUTOR] Waiting for messages")

            except QueueTimeoutException as e:
                print(e)
            except Exception as e:
                self._logger.error(e)
                # TODO: exit(1) makes me nervous???
                exit(1)

    def __process_files(
        self, files: list[str], campaign_id: str, activity_id: str
    ) -> None:
        """
        Process a list of files by generating transfer requests when files are
        not available locally.

        :param files: List of files
        :type files: list[str]
        """

        self._logger.debug("Processing files...")

        # TODO: we raise exceptions and handle them in __process with an agent
        # shutdown?!
        transfer_type = None
        for file_path in files:
            file_url = urlparse(file_path)
            self._logger.debug(f"File to parse {file_url}")

            # If file scheme local, then do not upgrade to transfer!
            if file_url.scheme == "file":
                if not pathlib.Path(file_url.path).exists():
                    raise Exception(f"Unable to find file: {file_url.path}")

            # If globus, then upgrade to transfer
            elif file_url.scheme == "globus":
                transfer_type = "globus"
                if "globus" not in self._settings.settings["plugins"]:
                    raise Exception("Globus may not be configured locally")

            elif file_url.scheme == "rsync":
                transfer_type = "rsync"
                if "rsync" not in self._settings.settings["plugins"]:
                    raise Exception("Rsync may not be configured locally")

            # Create activity messages (if no transfer, will do be empty).
            activity_messages = self._transfer_hippo.pack(
                activity_id=activity_id,
                campaign_id=campaign_id,
                file_url=file_url,
                transfer_type=transfer_type,
            )
            for msg in activity_messages:
                self.to_new_activity_q.put(msg)
