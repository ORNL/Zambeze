# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import json
import logging
import os
import requests
import threading
import time

from queue import Queue
from typing import Optional
from dataclasses import asdict

from zambeze.orchestration.monitor import Monitor
from zambeze.settings import ZambezeSettings
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.data.transfer_hippo import TransferHippo


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

    def __process(self):  # noqa: C901
        """
        Evaluate and process messages if requested activity is supported.
        """

        self._logger.info("[executor] In __process! ")

        self._logger.info("eins")

        # Change to the agent's desired working directory.
        default_working_dir = self._settings.settings["plugins"]["All"][
            "default_working_directory"
        ]
        self._logger.info(
            f"[executor] Moving to working directory {default_working_dir}"
        )

        try:
            # First try to switch into working directory if it exists.
            os.chdir(default_working_dir)
            self._logger.info("zwei")
        except FileNotFoundError:
            self._logger.error(
                "[exec] Working directory not found... attempting to create!"
            )
            os.makedirs(default_working_dir)
            self._logger.error("[exec] Working directory successfully created!")
        except Exception as e2:
            self._logger.error(f"[exec]CAUGHT: {type(e2).__name__}")
            self._logger.error(f"[exec] CAUGHT: {e2}")

        monitor_launched = False
        terminator_stopped = False

        while True:
            self._logger.info("[exec] Retrieving a message! ")
            self._logger.info(f" SIZE OF QUEUE: {self.to_process_q.qsize()}")
            dag_msg = self.to_process_q.get()

            self._logger.info("drei")

            self._logger.debug(f"[exec] Retrieved message! {dag_msg}...")

            # Check 1. If MONITOR, then we want to STICK the process
            if dag_msg[0] == "MONITOR":
                self._logger.info("[executor] (E117) ENTERING MONITOR TASK THREAD!")
                monitor_thread = Monitor(dag_msg, self._logger)
                monitor_thread.start()

                self._logger.info("[executor] (E121) Creating MONITOR reader thread!")
                monitor_reader = threading.Thread(target=self.monitor_check, args=())
                monitor_reader.start()

                # Save the monitor thread so we can scan it.
                self.monitor = monitor_thread
                monitor_launched = True

                self._logger.info("vier")

            elif dag_msg[0] == "TERMINATOR":
                self._logger.info("funf")
                # TERMINATOR ALWAYS SUCCEEDS.
                status_msg = {
                    "status": "SUCCEEDED",
                    "activity_id": dag_msg[0],
                    "msg": "TERMINATION CONDITION ACTIVATED.",
                }

                self._logger.debug(
                    "[exec] Putting TERMINATOR success on to_status_q..."
                )
                self.to_status_q.put(status_msg)
                terminator_stopped = True
                self._logger.info("sechs")

            s = f"[exec] Monitor launched {monitor_launched}"
            s2 = f", Terminator stopped: {terminator_stopped}"
            self._logger.info(s + s2)

            # If we were just launching monitor, go to top of loop; start over.
            if monitor_launched or terminator_stopped:
                monitor_launched = False
                terminator_stopped = False
                continue

            self._logger.info("sieben")

            activity_msg = dag_msg[1]["activity"]
            predecessors = dag_msg[1]["predecessors"]

            self._logger.info("acht")

            # transfer_params = dag_msg[1]["transfer_params"]
            transfer_tokens = dag_msg[1]["transfer_tokens"]

            self._logger.info(f"JTRANSFER TOKENS: {transfer_tokens}")

            # *** HERE WE DO PREDECESSOR CHECKING (to unlock actual activity task) ***
            self._logger.info(f"[exec] Activity has predecessors: {predecessors}")

            self._logger.info(f"Foo the bar: {activity_msg}")
            # STEP 1. Confirm the monitor is MONITORING.
            campaign_id = activity_msg.campaign_id

            self._logger.info("neun")

            if (
                "MONITOR" in predecessors
            ):  # TODO: allow MONITOR *AND OTHER* predecessors.
                self._logger.info(
                    f"[exec] Checking monitor message for campaign ID: {campaign_id}"
                )

                # Wait until we receive a monitoring heartbeat.
                while True:
                    status_msg = self.incoming_control_q.get()
                    if (
                        status_msg["campaign_id"] == campaign_id
                        and status_msg["status"] == "MONITORING"
                    ):
                        self._logger.debug(
                            "[exec] Eligible MONITOR heartbeat. Continuing!"
                        )
                        break
            # Step 2. If not waiting on monitor... make sure all other predecessors are met.
            else:
                self._logger.debug("[exec] Entering predecessor waiting loop...")
                pred_track_dict = {key: None for key in predecessors}

                # while loop ascertains that we 'keep trying the status scan' until it is
                # successful (/failed).
                while True:
                    success_count = 0
                    failure_count = 0

                    # for loop means we check every possible predecessor for an activity.
                    for pred_activity_id in pred_track_dict:
                        self._logger.debug(
                            "[exec] Fetching predecessor status message..."
                        )

                        # A: See if activity in pred_track_dict. If not... continue...
                        if pred_activity_id not in self.control_dict:
                            self._logger.info(
                                f"Predecessor ID: {pred_activity_id} not received. Continuing..."
                            )
                            time.sleep(5)  # TODO: remove.
                            break

                        # B: Check the status of the activity ID.
                        pred_activity_status = self.control_dict[pred_activity_id][
                            "status"
                        ]

                        if pred_activity_status == "SUCCEEDED":
                            success_count += 1
                        elif pred_activity_status == "FAILED":
                            failure_count += 1

                    total_completed = success_count + failure_count

                    self._logger.info(
                        f"[exec] PREDECESSOR COMPLETED COUNT: {total_completed}"
                    )
                    if total_completed == len(pred_track_dict):
                        break

            if activity_msg.type.upper() == "SHELL":
                self._logger.info("[exec] SHELL message received:")
                #self._logger.info(json.dumps(asdict(activity_msg.data), indent=4))

                self._logger.info("zehn")

                # self._logger.info(activity_msg.data.body)

                # Determine if the shell activity has files that
                # Need to be moved to be executed
                if activity_msg.files:  # TODO: I think this always exists and defaults to empty.
                    self._logger.info("elf")
                    if len(activity_msg.files) > 0:
                        self._logger.info("zwolf")
                        try:
                            self.__process_files(
                                activity_msg.files,
                                activity_msg.campaign_id,
                                activity_msg.activity_id,
                                transfer_tokens,
                            )
                        except Exception as e:
                            status_msg = {
                                "status": "FAILED",
                                "activity_id": dag_msg[0],
                                "msg": "UNABLE TO ACQUIRE FILES.",
                                "details": e,
                            }
                            self.to_status_q.put(status_msg)
                            self._logger.error(
                                f"[exec] Unable to acquire files. Caught {e}"
                            )
                            self._logger.exception("ERROR-123")
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

                # TODO -- bring these back in next version.
                # self._logger.info("[EXECUTOR] Command to be executed.")
                # self._logger.info(json.dumps(data["cmd"], indent=4))
                self._logger.warning("[exec] SKIPPING FAULTY CHECK...")

                # checked_result = self._settings.plugins.check(activity_msg.data.body)
                # self._logger.debug(f"[EXECUTOR] Checked result: {checked_result}")

                self._logger.info("dreizehn")

                # TODO: handle failures from the SHELL activity.
                try:
                    self._settings.plugins.run(activity_msg)
                except Exception as e:
                    self._logger.error(f"[vierzehn] caught: {e}")

                self._logger.info("vierzehn.1")

                # if checked_result.error_detected() is False:
                #     self._settings.plugins.run(activity_msg)
                # else:
                #     self._logger.debug(
                #         "Skipping run - error detected when running " "plugin check"
                #     )
            elif activity_msg.data.body.type == "TRANSFER":
                source_file = activity_msg.data

                transfer_hippo = TransferHippo(
                    agent_id=self._agent_id,
                    settings=self._settings,
                    logger=self._logger,
                    tokens=transfer_tokens,
                )

                # Load all files into the TransferHippo.
                self._logger.info("[exec] Loading files into TransferHippo.")
                transfer_hippo.load(source_file)
                # Validate that all files are accessible.
                self._logger.info("[exec] Validating file accessibility.")
                transfer_hippo.validate()
                # Ensure that all authentication is achieved.
                self._logger.info("[exec] Checking user auth.")
                transfer_hippo.check_auth()
                # Submit the transfer
                self._logger.info("[exec] Submit the transfer.")
                transfer_hippo.start_transfer()
                # BLOCK: wait for transfer to finish
                self._logger.info("[exec] Wait for transfer...")
                transfer_hippo.transfer_wait()
                self._logger.info("[exec] File transfer finished!")

            # If we get here, it should be because nothing failed
            status_msg = {
                "status": "SUCCEEDED",
                "activity_id": dag_msg[0],
                "msg": "SUCCESSFULLY COMPLETED TASK.",
                "result": None,
            }
            self.to_status_q.put(status_msg)

            self._logger.info("[exec] Waiting for messages")

    def __process_files(
        self, files: list[str], campaign_id: str, activity_id: str, tokens=None
    ) -> None:
        """
        Process a list of files by generating transfer requests when files are
        not available locally.

        :param files: List of files
        :type files: list[str]
        """

        self._logger.info(f"ex TRANSFER TOKENS??? {tokens}")

        transfer_hippo = TransferHippo(
            agent_id=self._agent_id,
            settings=self._settings,
            logger=self._logger,
            tokens=tokens,
        )

        # Load all files into the TransferHippo.
        self._logger.info("[exec] Loading files into TransferHippo.")
        transfer_hippo.load(files)
        # Validate that all files are accessible.
        self._logger.info("[exec] Validating file accessibility.")
        transfer_hippo.validate()
        # Ensure that all authentication is achieved.
        self._logger.info("[exec] Checking user auth.")
        transfer_hippo.check_auth()
        # Submit the transfer
        self._logger.info("[exec] Submit the transfer.")
        transfer_hippo.start_transfer()
        # BLOCK: wait for transfer to finish
        self._logger.info("[exec] Wait for transfer...")
        transfer_hippo.transfer_wait()
        self._logger.info("[exec] File transfer finished!")

    def monitor_check(self):
        # TODO: whenever we want to query status, get info from MONITOR here.
        self._logger.info("[exec] Monitor check initializing...")

        while True:
            self._logger.info(f"[exec] Monitor completed?: {self.monitor.completed}")

            if self.monitor.completed:
                self.monitor.to_monitor_q.put("KILL")
                self.monitor = None  # reset to None for now.
                self._logger.info("[exec] MONITOR check sending kill signal...")
                break
            else:
                self._logger.debug("MONITOR NOT COMPLETED YET!")
                time.sleep(2)


def download_https_file(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File downloaded and saved as {save_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
