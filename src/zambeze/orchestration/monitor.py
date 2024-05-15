# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import threading
from time import time, sleep
from queue import Queue


class Monitor(threading.Thread):
    """
    Monitor thread that enables an agent to track
    task state across Zambeze.

    Attributes:
        dag_msg (dict): A dictionary message holding the task graph.
        _logger (logging.Logger): Logger object (local log).
        monitor_hb_s (int): Seconds between heartbeat messages.
        to_monitor_q (queue.Queue): Queue to receive messages to monitor.
        to_status_q (queue.Queue): Queue to send status messages.
        dag_dict (dict): Dictionary to keep track of the tasks status.
        completed (bool): Flag to indicate if monitoring is completed.
    """

    def __init__(self, dag_msg, logger):
        super().__init__()

        self.dag_msg = dag_msg
        self._logger = logger
        self.monitor_hb_s = 5  # seconds between heartbeats

        self.to_monitor_q = Queue()
        self.to_status_q = Queue()

        self.dag_dict = {
            activity_id: "PROCESSING"
            for activity_id in dag_msg[1]["all_activity_ids"]
            if activity_id != "MONITOR"
        }

        self._logger.info(
            f"[monitor] Monitoring initialized for activities: {self.dag_dict.keys()}"
        )
        self.completed = False
        self.last_logged_proc_count = None

    def run(self):
        """
        Runs the monitor process when the thread starts. It checks for
        task completion, processes incoming messages, and sends heartbeat
        messages at regular intervals.
        """
        last_hb_time = time()
        last_proc_log_time = time()  # Variable to track the last proc count log time
        while not self.completed:
            self._check_activities()
            self._process_messages()

            # Log the process count only every 10 seconds
            current_time = time()
            if current_time - last_proc_log_time >= 10:
                self._log_proc_count()
                last_proc_log_time = current_time  # Update the last proc count log time

            last_hb_time = self._send_heartbeat(last_hb_time)
            sleep(0.1)

        self._logger.info("[monitor] Monitoring completed.")

    def _log_proc_count(self):
        """
        Log the current process count, if it has changed since last log.
        """
        proc_count = sum(status == "PROCESSING" for status in self.dag_dict.values())
        if proc_count != self.last_logged_proc_count:
            self._logger.debug(
                f"[monitor] Current proc count: {proc_count}, Status dict: {self.dag_dict}"
            )
            self.last_logged_proc_count = proc_count

    def _check_activities(self):
        """
        Check the status of all activities and update the monitoring status
        if all activities are completed.
        """
        # self._logger.info("IN CHECK ACTIVITIES")

        proc_count = sum(status == "PROCESSING" for status in self.dag_dict.values())

        if proc_count == 0:
            self.completed = True
            self._logger.info(f"[monitor] Final campaign status dict: {self.dag_dict}")

    def _process_messages(self):
        """
        Process messages from the to_monitor_q and update the status of activities.
        """
        # self._logger.info("IN PROCESS MESSAGES")
        if not self.to_monitor_q.empty():
            status_msg = self.to_monitor_q.get()

            self._logger.info(f"[monitor] Received control message: {status_msg}")

            if status_msg == "KILL":
                self._logger.info(
                    "[monitor] Healthy KILL signal received. Tearing down..."
                )
                self.completed = True
                return

            activity_id = status_msg["activity_id"]
            if activity_id in self.dag_dict:
                self.dag_dict[activity_id] = status_msg["status"]

    def _send_heartbeat(self, last_hb_time):
        """
        Send a heartbeat message if the time since the last heartbeat exceeds
        the threshold. Updates and returns the last heartbeat time.

        Args:
            last_hb_time (float): The last recorded time a heartbeat was sent.

        Returns:
            float: The updated last heartbeat time.
        """
        current_time = time()
        if current_time - last_hb_time > self.monitor_hb_s:
            hb_monitor_msg = {
                "status": "MONITORING",
                "activity_id": "MONITOR",
                "campaign_id": self.dag_msg[1]["campaign_id"],
                "msg": "simple heartbeat notification.",
            }

            self.to_status_q.put(hb_monitor_msg)
            self._logger.debug(f"[monitor] Enqueued monitor hb message! | Queue size: {self.to_status_q.qsize()}")
            return current_time  # return the updated time

        return last_hb_time  # return the original time if no heartbeat was sent
