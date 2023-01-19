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

from typing import Optional
from uuid import uuid4

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

    def __init__(
        self,
        conf_file: Optional[pathlib.Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an object that represents a distributed agent."""
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )

        # Create an ID for our agent.
        self._agent_id = str(uuid4())

        self._activity_dao = ActivityDAO(self._logger)
        self._settings = ZambezeSettings(conf_file=conf_file, logger=self._logger)

        # Create and start an executor thread.
        self._executor = Executor(
            settings=self._settings, agent_id=self._agent_id, logger=self._logger
        )
        self._executor.start()

        self._logger.info("EARTH TO JOSH A")

        # Create and start a MessageHandler thread object.
        try:
            self._msg_handler_thd = MessageHandler(
                self._agent_id, settings=self._settings, logger=self._logger
            )
        except Exception as e:
            self._logger.error("[AGENT] ERROR IN CREATING MESSAGE HANDLER")
            self._logger.error(e)
            self._logger.error("[AGENT] TERMINATING AGENT...")
            exit(1)

        self._logger.info("EARTH TO JOSH B")

        # Create and start the sorter threads!
        _activity_sorter_thd = threading.Thread(
            target=self.recv_activity_process_thd, args=()
        )
        _activity_sorter_thd.start()

    @property
    def executor(self) -> Executor:
        return self._executor

    # TODO: CHANGE THE WORD FROM SORT, PLEASE.
    def send_control_thd(self):
        """ Move processable control messages to the message_handler from executor.
            OBSERVES message_handler (via send_control_q)
        """
        self._logger.info("Starting send control thread!")
        while True:
            activ_to_sort = self._executor.to_status_q.get()
            self._msg_handler_thd.send_control_q.put(activ_to_sort)
            self._logger.debug("Put new activity into message handler control queue!")

    def recv_activity_process_thd(self):
        """ Move process-eligible activities to the executor's to_process_q!
            OBSERVES message_handler (via to_process_q)
        """
        self._logger.info("Starting activity sorter thread!")
        while True:
            activ_to_sort = self._msg_handler_thd.check_activity_q.get()
            self._executor.to_process_q.put(activ_to_sort)
            self._logger.debug("Put new activity into executor processing queue!")

    def send_activity_thd(self):
        """ We created an activity! Now enqueue it in Zambeze's central queue...
            OBSERVES executor (via to_new_activity_q)

        """
        self._logger.info("Starting send activity thread!")
        while True:
            activ_to_sort = self._executor.to_new_activity_q.get()
            self._msg_handler_thd.msg_handler_send_activity_q.put(activ_to_sort)
            self._logger.debug("Put new activity into executor processing queue!")
