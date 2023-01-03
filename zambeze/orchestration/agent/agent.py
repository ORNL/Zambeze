#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import asyncio
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
    """A distributed Agent.

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
        self._agent_id = uuid4()
        self._activity_dao = ActivityDAO(self._logger)

        self._settings = ZambezeSettings(conf_file=conf_file, logger=self._logger)

        # Create and start an executor thread.
        self._executor = Executor(settings=self._settings, logger=self._logger)
        self._executor.start()

        # Create and start a MessageHandler thread object.
        self._msg_handler_thd = MessageHandler(self._agent_id, settings=self._settings, logger=self._logger)

        # Create and start the sorter threads!
        _activity_sorter_thd = threading.Thread(target=self.recv_activity_process_thd, args=())
        _activity_sorter_thd.start()

    @property
    def executor(self) -> Executor:
        return self._executor

    def send_control_thd(self):
        """ Move process-eligible control messages to the message_handler from the executor. """
        self._logger.info("Starting send control thread!")
        while True:
            activ_to_sort = self._executor.to_status_q.get()
            self._msg_handler_thd.send_control_q.put(activ_to_sort)
            self._logger.debug("Put new activity into message handler control queue!")

    def recv_activity_process_thd(self):
        """ Move process-eligible activities to the executor's to_process_q! """
        self._logger.info("Starting activity sorter thread!")
        while True:
            activ_to_sort = self._msg_handler_thd.check_activity_q.get()
            self._executor.to_process_q.put(activ_to_sort)
            self._logger.debug("Put new activity into executor processing queue!")

    def send_activity_thd(self):
        """ We created an activity! Now time to enqueue it to be sent to Zambeze's central queue... """
        self._logger.info("Starting send activity thread!")
        while True:
            activ_to_sort = self._executor.to_new_activity_q.get()
            self._msg_handler_thd.send_activity_q.put(activ_to_sort)
            self._logger.debug("Put new activity into executor processing queue!")