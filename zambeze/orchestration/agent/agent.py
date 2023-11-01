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

from ..executor import Executor
from ...settings import ZambezeSettings



class Agent:
    """
    A distributed Agent that uses threads to *OBSERVE* the state of the executor
    and message handler, and moves messages between these components, as needed.

    See: https://en.wikipedia.org/wiki/Observer_pattern


    :param conf_file: Path to configuration file
    :type conf_file: Optional[pathlib.Path]
    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, conf_file: Optional[pathlib.Path], logger: logging.Logger):
        """Create an object that represents a distributed agent."""

        self._logger = logger

        # Create an ID for our agent.
        self._agent_id = str(uuid4())

        self._activity_dao = ActivityDAO(self._logger)
        self._settings = ZambezeSettings(conf_file=conf_file, logger=self._logger)

        # Create and start an executor thread.
        self._executor = Executor(
            settings=self._settings, agent_id=self._agent_id, logger=self._logger
        )
        self._executor.start()

        # Create and start a MessageHandler thread object.
        try:
            self._msg_handler_thd = MessageHandler(
                self._agent_id, settings=self._settings, logger=self._logger
            )
        except Exception as e:
            self._logger.error("[agent] ERROR IN CREATING MESSAGE HANDLER")
            self._logger.error(f"[agent] Error of type: {type(e).__name__}: {e}")
            self._logger.error("[agent] TERMINATING AGENT...")
            exit(1)

        # Create and start the sorter threads!
        _activity_sorter_thd = threading.Thread(
            target=self.recv_activity_process_thd, args=()
        )
        _activity_sorter_thd.start()

        # Create and start control sender thread...
        _status_sender_thd = threading.Thread(target=self.send_control_thd, args=())
        _status_sender_thd.start()

        # Create and start control receiver thread...
        _status_receiver_thd = threading.Thread(target=self.recv_control_thd, args=())
        _status_receiver_thd.start()

    @property
    def executor(self) -> Executor:
        return self._executor

    def send_control_thd(self):
        """Move processable control messages to the message_handler from executor.
        OBSERVES message_handler (via send_control_q)
        """
        self._logger.info("Starting send control thread!")
        while True:

            if self._executor.to_status_q.qsize() > 0:
                status_to_send = self._executor.to_status_q.get()
                self._msg_handler_thd.msg_handler_send_control_q.put(status_to_send)
                self._logger.debug(
                    "[agent] Put new status/control into message handler control queue!"
                )
            if self._executor.monitor is not None \
                    and self._executor.monitor.to_status_q.qsize() > 0:
                self._logger.info("[agent] Grabbing MONITOR status message...")
                status_to_send = self._executor.monitor.to_status_q.get()
                self._msg_handler_thd.msg_handler_send_control_q.put(status_to_send)
                self._logger.debug(
                    "[agent] Put new MONITOR STATUS into message handler control queue!"
                )

    def recv_activity_process_thd(self):
        """Move process-eligible activities to the executor's to_process_q!
        OBSERVES message_handler (via to_process_q)
        """
        self._logger.info("Starting activity sorter thread! A110")
        while True:
            activ_to_sort = self._msg_handler_thd.check_activity_q.get()
            self._logger.info(f"[agent] Received activity (A113): {activ_to_sort}")
            self._executor.to_process_q.put(activ_to_sort)
            self._logger.debug(
                "[agent] Put new activity into executor processing queue! (A116)"
            )

    def recv_control_thd(self):
        """Move process-eligible activities to the executor's to_process_q!
        OBSERVES message_handler (via to_process_q)
        """
        self._logger.info("[agent] Starting control sorter thread!")
        while True:
            control_to_sort = self._msg_handler_thd.recv_control_q.get()
            self._logger.info(f"[agent] Received control: {control_to_sort}")

            # TEMPORARY: update local dict for non-MONITOR / non-TERMINATOR activities #
            activity_id = control_to_sort["activity_id"]
            if activity_id not in self.executor.control_dict:
                self.executor.control_dict[activity_id] = dict()

            self.executor.control_dict[activity_id]["status"] = control_to_sort["status"]
            # ************************* #

            # We want to process these control messages in 2 places...
            # 1. Let the executor's MONITOR see if it needs it.
            # 2. Let the executor itself see if it needs it.
            if self._executor.monitor is not None:
                # Send control messages to the executor's monitor.
                self._executor.monitor.to_monitor_q.put(control_to_sort)
                self._logger.debug(
                    "[agent] Put new activity into monitor processing queue!"
                )

            self._executor.incoming_control_q.put(control_to_sort)
            self._logger.debug("[agent] Put new activity into executor control queue!")

    def send_activity_thd(self):
        """We created an activity! Now enqueue it in Zambeze's central queue...
        OBSERVES executor (via to_new_activity_q)

        """
        self._logger.info("Starting send activity thread!")
        while True:
            activ_to_sort = self._executor.to_new_activity_q.get()
            self._msg_handler_thd.msg_handler_send_activity_q.put(activ_to_sort)
            self._logger.debug(
                "[agent] Put new activity into executor processing queue!"
            )
