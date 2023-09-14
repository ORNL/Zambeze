#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import json
import logging
import globus_sdk
import os
import re
import time
import pathlib
import threading
import requests

from queue import Queue
from typing import Optional
from dataclasses import asdict
from urllib.parse import urlparse
from .monitor import Monitor


from ..settings import ZambezeSettings
from .message.message_factory import MessageFactory
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

        self.control_dict = dict()

        try:
            self._msg_factory = MessageFactory(logger=self._logger)
            self._transfer_hippo = TransferHippo(
                agent_id=self._agent_id, logger=self._logger, settings=self._settings
            )
        except Exception as e:
            self._logger.error(str(e))

        # Initially we don't have a monitor. This can become a Monitor Thread object.
        # It can revert to None.
        self.monitor = None
        self._logger.info("[executor] Successfully initialized Executor!")

    def run(self):
        """Override the Thread 'run' method to instead run our
        process when Thread.start() is called!"""
        # Create persisent "__process()"
        self.__process()

    def __process(self):
        """
        Evaluate and process messages if requested activity is supported.
        """

        self._logger.info("[executor] In __process! ")

        # Change to the agent's desired working directory.
        default_working_dir = self._settings.settings["plugins"]["All"][
            "default_working_directory"
        ]
        self._logger.info(
            f"[executor] Moving to working directory {default_working_dir}"
        )
        os.chdir(default_working_dir)

        monitor_launched = False
        terminator_stopped = False

        while True:

            self._logger.info("[executor] Retrieving a message! ")
            self._logger.info(f" SIZE OF QUEUE: {self.to_process_q.qsize()}")
            dag_msg = self.to_process_q.get()

            # Check 1. If MONITOR, then we want to STICK the process
            if dag_msg[0] == "MONITOR":

                self._logger.info("[executor] ENTERING MONITOR TASK THREAD!")
                monitor_thread = Monitor(dag_msg, self._logger)
                monitor_thread.start()

                self._logger.info("[executor] Creating MONITOR reader thread!")
                monitor_reader = threading.Thread(target=self.monitor_check, args=())
                monitor_reader.start()

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

                self._logger.debug(
                    "[executor] Putting TERMINATOR success on to_status_q..."
                )
                self.to_status_q.put(status_msg)
                terminator_stopped = True

            self._logger.info(
                f"[executor] Monitor launched: {monitor_launched} | "
                f"Terminator stopped: {terminator_stopped}"
            )

            # If we were just launching monitor, go to top of loop; start over.
            if monitor_launched or terminator_stopped:
                monitor_launched = False
                terminator_stopped = False
                continue

            activity_msg = dag_msg[1]["activity"]
            predecessors = dag_msg[1]["predecessors"]

            self._logger.info(f"[FFF5.4] {dag_msg}")
            transfer_tokens = dag_msg[1]['transfer_tokens']

            # *** HERE WE DO PREDECESSOR CHECKING (to unlock actual activity task) ***
            self._logger.info(f"[executor] Activity has predecessors: {predecessors}")

            self._logger.info(f"[FFF5.5] {activity_msg.data}")

            # STEP 1. Confirm the monitor is MONITORING.
            campaign_id = activity_msg.data.campaign_id

            self._logger.info(f"[FFF6] Transfer tokens: {transfer_tokens}")

            if "MONITOR" in predecessors:  # TODO: allow MONITOR *AND OTHER* predecessors.

                self._logger.info(
                    f"[executor] Checking monitor message for campaign ID: "
                    f"{campaign_id}"
                )

                # Wait until we receive a monitoring heartbeat.
                while True:
                    status_msg = self.incoming_control_q.get()
                    if (
                        status_msg["campaign_id"] == campaign_id
                        and status_msg["status"] == "MONITORING"
                    ):
                        self._logger.debug(
                            "[executor] Eligible MONITOR heartbeat. Continuing!"
                        )
                        break
            # Step 2. If not waiting on monitor... make sure all other predecessors are met.
            else:
                self._logger.debug("[executor] Entering predecessor waiting loop...")
                pred_track_dict = {key: None for key in predecessors}

                # while loop ascertains that we 'keep trying the status scan' until it is successful (/failed).
                while True:

                    success_count = 0
                    failure_count = 0

                    # for loop means we check every possible predecessor for an activity.
                    for pred_activity_id in pred_track_dict:
                        self._logger.debug(
                            "[executor] Fetching predecessor status message..."
                        )

                        # A: See if activity in pred_track_dict. If not... continue...
                        if pred_activity_id not in self.control_dict:
                            self._logger.info(f"Predecessor ID: {pred_activity_id} not received. Continuing...")
                            time.sleep(5)  # TODO: remove.
                            break

                        # B: Check the status of the activity ID.
                        pred_activity_status = self.control_dict[pred_activity_id]['status']

                        if pred_activity_status == "SUCCEEDED":
                            success_count += 1
                        elif pred_activity_status == "FAILED":
                            failure_count += 1

                    total_completed = success_count + failure_count

                    self._logger.info(
                        f"[executor] PREDECESSOR COMPLETED COUNT: {total_completed}"
                        )
                    if total_completed == len(pred_track_dict):
                        break
            self._logger.info("[FFF6.9]")
            if activity_msg.data.body.type == "SHELL":
                self._logger.info("[executor] SHELL message received:")
                self._logger.info(json.dumps(asdict(activity_msg.data), indent=4))

                # Determine if the shell activity has files that
                # Need to be moved to be executed
                if activity_msg.data.body.files:

                    self._logger.info(f"[FFF7]")
                    if len(activity_msg.data.body.files) > 0:

                        try:
                            self.__process_files(
                                activity_msg.data.body.files,
                                activity_msg.data.campaign_id,
                                activity_msg.data.activity_id,
                                transfer_tokens
                            )
                        except Exception as e:
                            status_msg = {
                                "status": "FAILED",
                                "activity_id": dag_msg[0],
                                "msg": "UNABLE TO ACQUIRE FILES.",
                                "details": e
                            }
                            self.to_status_q.put(status_msg)
                            self._logger.error(
                                f"[executor.py] Unable to acquire files. Caught {e}"
                            )
                            self._logger.exception("ERROR-123")
                            #self._logger.error(traceback.print_exc())
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

                self._logger.debug("EXECUTOR CHECKING RESULT...")
                # checked_result = self._settings.plugins.check(activity_msg.data.body)
                # self._logger.debug(f"[EXECUTOR] Checked result: {checked_result}")
                self._logger.debug("SKIPPING FAULTY CHECK...")

                # TODO: have psij instead run the plugins.

                # if psij_flag:
                #    Run through psi_j

                self._settings.plugins.run(activity_msg)
                # TODO: bring proper validation back (below)
                # if checked_result.error_detected() is False:
                #     self._settings.plugins.run(activity_msg)
                # else:
                #     self._logger.debug(
                #         "Skipping run - error detected when running " "plugin check"
                #     )

            else:
                raise Exception("Only SHELL currently supported")

            # If we get here, it should be because nothing failed
            # TODO: confirm (unit-test somehow)
            status_msg = {
                "status": "SUCCEEDED",
                "activity_id": dag_msg[0],
                "msg": "SUCCESSFULLY COMPLETED TASK.",
            }
            self.to_status_q.put(status_msg)

            self._logger.info("[EXECUTOR] Waiting for messages")

    def __process_files(
        self, files: list[str], campaign_id: str, activity_id: str, tokens=None
    ) -> None:
        """
        Process a list of files by generating transfer requests when files are
        not available locally.

        :param files: List of files
        :type files: list[str]
        """

        self._logger.debug("[FFF8] Processing files...")

        # TODO: we raise exceptions and handle them in __process with an agent
        # shutdown?!
        transfer_type = None
        globus_transfer_clients = dict()  # should be source_ep_id: {'task_data': xxx, 'transfer_client': yyy}
        globus_task_ids = []

        for file_path in files:
            # file_url = urlparse(file_path)  # TODO!
            file_url = file_path
            self._logger.debug(f"File to parse {file_url}")

            # If file scheme local, then do not upgrade to transfer!
            # if file_url.scheme == "file":
            #TODO: TYLER---BRING BACK. Just diagnosing minor path issue.
            # if file_url.startswith("file"):
            #     if not pathlib.Path(file_url).exists():
            #         raise Exception(f"Unable to find file: {file_url}")  # TODO: add back 'file_url.path'

            # If globus, then upgrade to transfer
            # elif file_url.scheme == "globus":
            # TODO: TYLER---change this back to elif.
            if file_url.startswith("globus"):

                # self._logger.info(f"GLOBUS FILE PATH RECEIVED: {file_url.path}")
                transfer_type = "globus"
                if "globus" not in self._settings.settings["plugins"]:
                    self._logger.info(f"GLOBUS ERROR")
                    raise Exception("Globus may not be configured locally")

                self._logger.info(f"[GGG-1]")

                # Just get the 36-character UUID of the source endpoint.
                source_ep = re.search(r"(.{36})@", file_url).group(1)
                dest_ep = self._settings.settings["plugins"]["globus"]["local_ep"]

                if source_ep not in globus_transfer_clients:
                    # construct an AccessTokenAuthorizer and use it to construct the
                    # TransferClient
                    globus_transfer_clients[source_ep] = dict()
                    globus_transfer_clients[source_ep]['transfer_client'] = globus_sdk.TransferClient(
                        authorizer=globus_sdk.AccessTokenAuthorizer(tokens["globus"]["access_token"])
                    )

                    # create a Transfer task consisting of one or more items
                    globus_transfer_clients[source_ep]['task_data'] = globus_sdk.TransferData(
                        source_endpoint=source_ep,
                        destination_endpoint=dest_ep,
                        transfer_client=globus_transfer_clients[source_ep]['transfer_client']
                    )

                source_filename = file_url[46:]
                filename = source_filename.split('/')[-1]

                # Can be 'here' since we're already in working directory.
                dest_filename = f"{os.path.join(os.getcwd(), filename)}"
                globus_transfer_clients[source_ep]['task_data'].add_item(
                    file_url[46:],  # source
                    dest_filename,  # dest
                )

            # elif file_url.scheme == "rsync":
            elif file_url.startswith('rsync'):
                transfer_type = "rsync"
                if "rsync" not in self._settings.settings["plugins"]:
                    raise Exception("Rsync may not be configured locally")

            # elif file_url.scheme == "https":
            elif file_url.startswith('https'):
                transfer_type = "https"

            # Create activity messages (if no transfer, will do be empty).
            activity_messages = self._transfer_hippo.pack(
                activity_id=activity_id,
                campaign_id=campaign_id,
                file_url=file_url,
                transfer_type=None,  # TODO: bring this back.
            )
            for msg in activity_messages:
                self.to_new_activity_q.put(msg)

        self._logger.info(f"[GGG-4] I AM HERE.")
        for source_ep in globus_transfer_clients:
            transfer_client = globus_transfer_clients[source_ep]['transfer_client']
            task_data = globus_transfer_clients[source_ep]['task_data']
            task_doc = transfer_client.submit_transfer(task_data)

            transfer_task_id = task_doc["task_id"]
            self._logger.info(f"submitted transfer, task_id={transfer_task_id}")

            globus_task_ids.append(transfer_task_id)

        self._logger.info("[HHH] WAITING FOR ALL TASKS TO COMPLETE...")
        # globus_success_count = 0
        # globus_fail_count = 0
        for task_id in globus_task_ids:

            while True:
                # TODO: proper creation of transfer_client
                status = transfer_client.get_task(task_id)['status']
                if status != "SUCCEEDED" and status != "FAILED":
                    time.sleep(2)
                else:
                    break
            time.sleep(0.5)  # Just gentle rate limiting.

        self._logger.info(f"[GGG-5] end of transfers.")


    def monitor_check(self):
        # TODO: whenever we want to query status, get info from MONITOR here.
        self._logger.info("[executor] Monitor check initializing...")

        while True:
            self._logger.info(
                f"[executor] Monitor completed?: {self.monitor.completed}"
            )

            if self.monitor.completed:
                self.monitor.to_monitor_q.put("KILL")
                self.monitor = None  # reset to None for now.
                self._logger.info("[executor] MONITOR check sending kill signal...")
                break
            else:
                self._logger.info("MONITOR NOT COMPLETED YET!!!")
                time.sleep(2)


def download_https_file(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File downloaded and saved as {save_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
