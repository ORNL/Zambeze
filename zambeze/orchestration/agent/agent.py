#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import pathlib
import threading
from uuid import uuid4
from typing import Optional

from zambeze.orchestration.agent.message_handler import MessageHandler
from zambeze.orchestration.db.dao.activity_dao import ActivityDAO
from zambeze.orchestration.executor import Executor
from zambeze.settings import ZambezeSettings


class Agent:
    """
    A distributed Agent that operates asynchronously using threads to observe and
    manage the state and interactions between an executor and a message handler.

    Attributes:
        _logger (logging.Logger): Logger for the agent.
        _agent_id (str): Unique identifier for the agent.
        _activity_dao (ActivityDAO): Data access object for activities.
        _settings (ZambezeSettings): Configuration settings for the agent.
        _executor (Executor): Executor thread that performs tasks.
        _msg_handler_thd (MessageHandler): MessageHandler thread for handling messages.

    Args:
        conf_file (Optional[pathlib.Path]): Path to the configuration file.
        logger (Optional[logging.Logger]): Logger object for logging messages.
    """

    def __init__(self, conf_file: Optional[pathlib.Path],
                 logger: Optional[logging.Logger] = None):
        """Initializes the Agent with given configuration file and logger."""

        self._logger = logger or logging.getLogger(__name__)

        self._logger.info("111")
        self._agent_id = str(uuid4())
        self._activity_dao = ActivityDAO(self._logger)
        self._settings = ZambezeSettings(conf_file=conf_file,
                                         logger=self._logger)
        self._logger.info("222")
        self._executor = Executor(settings=self._settings,
                                  agent_id=self._agent_id,
                                  logger=self._logger)
        self._logger.info("333")
        self._msg_handler_thd = self._init_message_handler()

        self._start_thread(self.recv_activity_process_thd, name="ActivitySorterThread")
        self._start_thread(self.send_control_thd, name="ControlSenderThread")
        self._start_thread(self.recv_control_thd, name="ControlReceiverThread")

        self._logger.info("444")
        self._executor.start()
        self._logger.info("555")

    def _init_message_handler(self):
        """Initializes the MessageHandler thread."""
        try:
            return MessageHandler(self._agent_id,
                                  settings=self._settings,
                                  logger=self._logger)
        except Exception as e:
            self._logger.error("[agent] ERROR IN CREATING MESSAGE HANDLER: "
                               "%s: %s", type(e).__name__, e)
            self._logger.error("[agent] TERMINATING AGENT...")
            exit(1)

    def _start_thread(self, target, name):
        """Starts a thread with the given target function and name."""
        thread = threading.Thread(target=target, name=name)
        thread.daemon = True  # Daemonize thread to exit when the main program exits
        thread.start()

    def send_control_thd(self):
        """Move processable control messages to the message_handler from executor.
        OBSERVES message_handler (via send_control_q)
        """
        self._logger.info("[agent] Starting send control thread!")
        while True:
            try:
                # Check the executor's queue for control messages to send.
                if self._executor.to_status_q.qsize() > 0:
                    status_to_send = self._executor.to_status_q.get()
                    self._msg_handler_thd.msg_handler_send_control_q.put(status_to_send)
                    self._logger.debug(
                        "[agent] Put new status/control into message handler control queue!"
                    )

                # Check the executor's monitor queue, if it exists and has messages.
                if self._executor.monitor is not None \
                        and self._executor.monitor.to_status_q.qsize() > 0:
                    self._logger.info("[agent] Grabbing MONITOR status message...")
                    status_to_send = self._executor.monitor.to_status_q.get()
                    self._msg_handler_thd.msg_handler_send_control_q.put(status_to_send)
                    self._logger.debug(
                        "[agent] Put new MONITOR STATUS into message handler control queue!"
                    )
            except Exception as e:
                self._logger.error(
                    "[agent] send_control_thd encountered an error: %s: %s",
                    type(e).__name__, e)

    def recv_activity_process_thd(self):
        """Move process-eligible activities to the executor's to_process_q.
        OBSERVES message_handler (via to_process_q)
        """
        self._logger.info("Starting activity sorter thread!")
        while True:
            try:
                # Retrieve an activity from the message handler's activity queue.
                activ_to_sort = self._msg_handler_thd.check_activity_q.get()
                self._logger.info(f"[agent] Received activity: {activ_to_sort}")

                # Place the activity into the executor's processing queue.
                self._executor.to_process_q.put(activ_to_sort)
                self._logger.debug(
                    "[agent] Put new activity into executor processing queue!"
                )

            except Exception as e:
                self._logger.error(
                    "[agent] recv_activity_process_thd encountered an error: %s: %s",
                    type(e).__name__, e)

    def recv_control_thd(self):
        """Move process-eligible control messages to the appropriate queues for processing.
        OBSERVES message_handler (via recv_control_q)
        """
        self._logger.info("[agent] Starting control sorter thread!")
        while True:
            try:
                # Retrieve a control message from the message handler's control queue.
                control_to_sort = self._msg_handler_thd.recv_control_q.get()
                self._logger.info(f"[agent] Received control message: {control_to_sort}")

                # TEMPORARY: update local dict for non-MONITOR / non-TERMINATOR controls
                activity_id = control_to_sort["activity_id"]
                if activity_id not in self._executor.control_dict:
                    self._executor.control_dict[activity_id] = dict()

                self._executor.control_dict[activity_id]["status"] = control_to_sort["status"]
                # ************************************************

                # The control message needs to be processed in two places:
                # 1. If there is an executor monitor, it may need the control message.
                if self._executor.monitor is not None:
                    self._executor.monitor.to_monitor_q.put(control_to_sort)
                    self._logger.debug("[agent] Put control message into monitor queue.")

                # 2. The executor itself may need the control message.
                self._executor.incoming_control_q.put(control_to_sort)
                self._logger.debug("[agent] Put control message into executor queue.")

            except Exception as e:
                self._logger.error(
                    "[agent] recv_control_thd encountered an error: %s: %s",
                    type(e).__name__, e)

    def send_activity_thd(self):
        """Periodically checks and forwards new activities from the executor to the message handler."""
        self._logger.info("[agent] Starting send activity thread!")
        while True:
            try:
                # Get a new activity from the executor's queue.
                activ_to_sort = self._executor.to_new_activity_q.get()

                # Put new activity into message handler's queue for further processing.
                self._msg_handler_thd.msg_handler_send_activity_q.put(activ_to_sort)
                self._logger.debug("[agent] Put new activity into message handler's queue.")
            except Exception as e:
                self._logger.error("[agent] send_activity_thd encountered an error: %s: %s",
                                   type(e).__name__, e)
