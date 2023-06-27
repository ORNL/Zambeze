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
import time
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

        # add incoming control queue for making predecessor decisions.
        self.incoming_control_q = Queue()

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

        # Initially we don't have a monitor. This can become a Monitor Thread object. It can revert to None.
        self.monitor = None
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

            self._logger.info("[EXECUTOR] Retrieving a message! ")
            dag_msg = self.to_process_q.get()
            self._logger.info(f"QUEUE OF SIZE: {self.to_process_q.qsize()}")

            # Check 1. If MONITOR, then we want to STICK the process.
            monitor_launched = False
            terminator_stopped = False

            self._logger.info(f"EXECUTOR!!! {dag_msg}")
            if dag_msg[0] == "MONITOR":

                self._logger.info("[EXECUTOR] ENTERING MONITOR TASK THREAD!")
                monitor_thread = Monitor(dag_msg, self._logger)
                monitor_thread.start()

                self._logger.info("[EXECUTOR] Creating MONITOR reader thread!")
                monitor_reader = threading.Thread(target=self.monitor_check, args=())
                monitor_reader.start()

                self._logger.info(
                    "Successfully launched MONITOR thread... continuing..."
                )

                # Save the monitor thread so we can scan it.
                self.monitor = monitor_thread
                monitor_launched = True

            elif dag_msg[0] == "TERMINATOR":
                # TERMINATOR ALWAYS SUCCEEDS.
                status_msg = {
                    "status": "SUCCEEDED",
                    "activity_id": dag_msg[0],
                    "msg": "TERMINATION CONDITION ACTIVATED.",
                }

                self._logger.debug("Putting TERMINATOR success on to_status_q...")
                self.to_status_q.put(status_msg)
                terminator_stopped = True

            self._logger.info(
                f"Monitor launched: {monitor_launched} | "
                f"Terminator stopped: {terminator_stopped}"
            )

            # If we were just launching monitor, go to top of loop; start over.
            if monitor_launched or terminator_stopped:
                self._logger.debug("CONTINUE CONDITION!")
                continue

            self._logger.info("[cccc]")
            activity_msg = dag_msg[1]["activity"]

            predecessors = dag_msg[1]["predecessors"]

            self._logger.info("[Executor] Message received:")
            self._logger.info(f"[ddd] ACTUAL SHELL MESSAGE RECEIVED")
            self._logger.info(json.dumps(asdict(activity_msg.data), indent=4))

            # *** HERE WE DO PREDECESSOR CHECKING (to unlock actual activity task) ***
            self._logger.info(f"GET PREDECESSORS from DAG message: {predecessors}")

            # STEP 1. Confirm the monitor is MONITORING.
            if "MONITOR" in predecessors:  # TODO: allow MONITOR *AND OTHER* predecessors.

                self._logger.debug("UUU")
                campaign_id = activity_msg.data.campaign_id
                self._logger.info(f"Checking monitor message for campaign ID: {campaign_id}")

                # Wait until we receive a monitoring heartbeat.
                while True:
                    self._logger.debug("VVV")
                    status_msg = self.incoming_control_q.get()
                    self._logger.debug(f"RECEIVED CONTROL MSG IN EXECUTOR: {status_msg}")

                    self._logger.debug(f"V1: {status_msg['campaign_id']}")
                    self._logger.debug(f"V1: {status_msg['status']}")

                    if status_msg["campaign_id"] == campaign_id and status_msg["status"] == "MONITORING":
                        self._logger.info("[executor] Eligible MONITOR heartbeat. Continuing!")
                        break
            # Step 2. If not waiting on monitor... make sure all other predecessors are met.
            else:
                # TODO.
                self._logger.info("TODO: WAIT LOOP FOR OTHER PREDECESSORS. ")
                pass

            self._logger.info(f"[aaa1] {activity_msg.data.body.type}")
            self._logger.info(f"[aaa2] {activity_msg.data}")
            if activity_msg.data.body.type == "SHELL":
                self._logger.info("[Executor] SHELL message received:")
                self._logger.info(json.dumps(asdict(activity_msg.data), indent=4))

                # Determine if the shell activity has files that
                # Need to be moved to be executed
                if activity_msg.data.body.files:
                    if len(activity_msg.data.body.files) > 0:

                        try:
                            self.__process_files(
                                activity_msg.data.body.files,
                                activity_msg.data.campaign_id,
                                activity_msg.data.activity_id,
                            )
                        except Exception as e:
                            status_msg = {
                                "status": "FAILED",
                                "activity_id": dag_msg[0],
                                "msg": "UNABLE TO ACQUIRE FILES.",
                            }
                            self.to_status_q.put(status_msg)
                            self._logger.error("[executor.py] Unable to acquire files. Quitting...")
                            continue

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

                # if psij_flag:
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
                "status": "SUCCEEDED",
                "activity_id": dag_msg[0],
                "msg": "SUCCESSFULLY COMPLETED TASK.",
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

    def monitor_check(self):
        # TODO: whenever we want to query status, get info from MONITOR here.
        self._logger.info("[executor] Monitor check initializing...")

        while True:
            self._logger.info("[executor] IN HURR.")
            self._logger.info(f"Monitor completed?: {self.monitor.completed}")

            if self.monitor.completed:
                self.monitor.to_monitor_q.put("KILL")
                self.monitor = None  # reset to None for now.
                self._logger.info("[executor] MONITOR check sending kill signal...")
                break
            else:
                self._logger.info("MONITOR NOT COMPLETED YET!!!")
                time.sleep(2)
