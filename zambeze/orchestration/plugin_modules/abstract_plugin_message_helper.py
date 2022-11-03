#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from abc import ABC, abstractmethod
from typing import Optional


class PluginMessageHelper(ABC):
    """
    Abstract base class for ensuring that all registered plugins have a
    valid message helper

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self._name = name

    def messageTemplate(self, args) -> dict:
        """Returns the message Template that can be attached to an activity"""
        raise NotImplementedError("messageTemplate method has not been created.")

    def validateMessage(self, args: list[dict]) -> list:
        """Return whether the schema of the message is valid.

        This is similar to the "check" method but the "check" command will run
        additional tests because it is assuming that it is about to run the
        plugin on the same agent that the "check" is being called from. The
        validateMessage method is to ensure that the message fields and keys
        are appropriate but does not make any assumptions about what agent
        the message will be executed on.

        So for instance calling the "check" method with the globus plugin will
        fail if the agent cannot connect to the Globus Service. Wheras,
        the "validateMessage" will not fail if it does not have access to
        the Globus service. It just ensures the message content makes sense and
        contains the correct schema.
        """
        raise NotImplementedError("validateMessage method has not been created.")
