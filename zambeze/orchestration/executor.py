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
from .monitor import Monitor


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

        self._logger.info("[EXECUTOR] Creating executor...")
        self._agent_id = agent_id

        try:
            self._msg_factory = MessageFactory(logger=self._logger)
            self._transfer_hippo = TransferHippo(
                agent_id=self._agent_id, logger=self._logger, settings=self._settings
            )
        except Exception as e:
            self._logger.info("WHAT IS WRONG???")
            self._logger.info(str(e))

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
            # try:

            self._logger.info("[EXECUTOR] Retrieving a message! ")
            dag_msg = self.to_process_q.get()

            # Check 1. If MONITOR, then we want to STICK the process.
            monitor_launched = False
            terminator_stopped = False

            self._logger.info(f"EXECUTOR!!! {dag_msg}")
            if dag_msg[0] == "MONITOR":

                self._logger.info(f"[EXECUTOR] ENTERING MONITOR TASK THREAD!")
                monitor_thread = Monitor(dag_msg, self._logger)
                self._logger.info(f"bbb1")
                monitor_thread.start()
                self._logger.info(f"bbb2")

                self._logger.info(f"Successfully launched MONITOR thread... continuing...")

                monitor_launched = True

            # elif dag_msg[0] == "TERMINATOR":
            #     status_msg = {
            #         'status': 'COMPLETED',
            #         'activity_id': dag_msg[0],
            #         'msg': 'TERMINATION CONDITION ACTIVATED.'
            #     }
            #     self.to_status_q.put(status_msg)
            #     terminator_stopped = True

            self._logger.info(f"Monitor launched: {monitor_launched} | "
                              f"Terminator stopped: {terminator_stopped}")

            # If we were just launching monitor, go to top of loop; start over.
            if monitor_launched or terminator_stopped:
                self._logger.debug("CONTINUE CONDITION!")
                continue

            self._logger.info("[cccc]")
            activity_msg = dag_msg[1]['activity']

            self._logger.info("[Executor] Message received:")
            # if type(activity_msg) is str and activity_msg in ["MONITOR", "TERMINATOR"]:
            #     self._logger.info(f"Message of type {activity_msg} (with NO payload) received! Continuing...")
            #     continue
            # else:
            self._logger.info(f"[ddd] ACTUAL SHELL MESSAGE RECEIVED")
            self._logger.info(json.dumps(asdict(activity_msg.data), indent=4))

            # NOW WE CREATE A WAIT-LOOP TO DETERMINE WHEN WE CAN PROCESS.

            # if we need files, check if present (and if not, go get them).

            # TODO: BRING THIS BACK TO BE SMART!!
            # any_upstream_failures = False
            # marked_predecessors = []
            # while True:
            #     control_msg = self.to_monitor_q.get()
            #     if control_msg["activity_id"] in dag_msg[1]['predecessors']:
            #         marked_predecessors.append(control_msg["activity_id"])
            #f
            #         # Something upstream failed :(
            #         if control_msg['status'] == "FAILED":
            #             any_upstream_failures = True
            #
            #         # If we have all of the predecessors, break loop!
            #         if len(dag_msg[1]['predecessors']) == len(marked_predecessors):
            #             break
            #
            # # Now we decide if we give up before we start OR keep going
            # if any_upstream_failures:
            #     # If there is a failure, mark this as failed and move on.
            #     status_msg = {
            #         'status': 'FAILED',
            #         'activity_id': dag_msg[0],
            #         'msg': 'UPSTREAM FAILURE ACKNOWLEDGED.'
            #     }
            #     self.to_status_q.put(status_msg)
            #     continue
            self._logger.info(f"[aaa1] {activity_msg.data.body.type}")
            self._logger.info(f"[aaa2] {activity_msg.data}")
            if activity_msg.data.body.type == "SHELL":
                self._logger.info("[Executor] SHELL message received:")
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

                self._logger.debug(f"EXECUTOR CHECKING RESULT...")
                self._logger.debug(f"activity_msg.data.body.type...")
                # checked_result = self._settings.plugins.check(activity_msg.data.body)
                # self._logger.debug(f"[EXECUTOR] Checked result: {checked_result}")
                self._logger.debug("SKIPPING FAULTY CHECK...")

                # TODO: have psij instead run the plugins.

                #if psij_flag:
                #    Run through psi_j

                # elif.

                self._settings.plugins.run(activity_msg)
                # if checked_result.error_detected() is False:
                #     self._settings.plugins.run(activity_msg)
                # else:
                #     self._logger.debug(
                #         "Skipping run - error detected when running " "plugin check"
                #     )

            else:
                raise Exception("Only SHELL currently supported")

            # If we get here, it should be because nothing failed # TODO: confirm (unit-test somehow)
            status_msg = {
                'status': 'COMPLETED',
                'activity_id': dag_msg[0],
                'msg': 'SUCCESSFULLY COMPLETED TASK.'
            }
            self.to_status_q.put(status_msg)

            self._logger.info("[EXECUTOR] Waiting for messages")

            # TODO: bring both of these back!
            # except QueueTimeoutException as e:
            #     print(e)
            # except Exception as e:
            #     self._logger.error(e)
            #     # TODO: exit(1) makes me nervous???
            #     exit(1)

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
