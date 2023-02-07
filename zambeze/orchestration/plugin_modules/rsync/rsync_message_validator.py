#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from __future__ import annotations

# Local imports
from ..abstract_plugin_message_validator import PluginMessageValidator
from ..common_dataclasses import RsyncTransferTemplate
from .rsync_common import PLUGIN_NAME, validateRequiredSourceAndDestinationValuesValid

# Standard imports
from dataclasses import asdict
from typing import Optional, overload
import logging


class RsyncMessageValidator(PluginMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)

    def _validateAction(self, action: str, checks: list, arguments: dict):
        if not isinstance(arguments, dict):
            arguments = asdict(arguments)

        if action == "transfer":
            # Start by checking that all the files have been provided
            print("**************************************************")
            print(arguments)
            for item in arguments["transfer"]["items"]:
                check = validateRequiredSourceAndDestinationValuesValid(item)

                if not check[0]:
                    checks.append(
                        {action: (False, f"Error detected for {action}. " + check[1])}
                    )

        else:
            checks.append({action: (False, f"{action} unsupported action\n")})
            return checks

        checks.append({action: (True, "")})
        return checks

    def validateAction(self, arguments: dict, action) -> list:
        """Check the arguments are supported.

        :param arguments: arguments needed to run the rsync plugin
        :type arguments: dict

        Rsync must have a source and end destination machine provided.

        :Example:

        >>> config = {
        >>>     "private_ssh_key": "path to ssh key"
        >>> }
        >>> # Assumes you are provided with a single dict not a list of dicts
        >>> arguments = {
        >>>     "transfer": {
        >>>         "source" : {
        >>>             "ip": "128.219.183.34",
        >>>             "user: "",
        >>>             "path: "",
        >>>         },
        >>>         "destination": {
        >>>             "ip": "172.231.41.3",
        >>>             "user: "",
        >>>             "path: "",
        >>>         }
        >>>         "arguments": ["argument1","argument2"]
        >>>     }
        >>> }
        >>> instance = Rsync()
        >>> instance.configure(config)
        >>> checked_arguments = instance.check(arguments)
        >>> # If there is no problem will return the following
        >>> # checked_arguments = [
        >>> # {
        >>> #   "transfer": (True, "")
        >>> # }]
        >>> assert checked_arguments[0]["transfer"][0]
        """
        checks = []
        return self._validateAction(action, checks, arguments)

    @overload
    def validateMessage(self, arguments: RsyncTransferTemplate) -> list:
        ...

    @overload
    def validateMessage(self, arguments: list[dict]) -> list:
        ...

    def validateMessage(self, arguments):
        """Check the arguments are supported.

        :param arguments: arguments needed to run the rsync plugin
        :type arguments: list[dict]

        Rsync must have a source and end destination machine provided.

        :Example:

        >>> config = {
        >>>     "private_ssh_key": "path to ssh key"
        >>> }
        >>> # Assumes you are provided with a list of dicts
        >>> arguments = [
        >>>     {
        >>>         "transfer": {
        >>>             "source" : {
        >>>                 "ip": "128.219.183.34",
        >>>                 "user: "",
        >>>                 "path: "",
        >>>             },
        >>>             "destination": {
        >>>                 "ip": "172.231.41.3",
        >>>                 "user: "",
        >>>                 "path: "",
        >>>             }
        >>>             "arguments": ["argument1","argument2"]
        >>>         }
        >>>     }
        >>> ]
        >>> instance = Rsync()
        >>> instance.configure(config)
        >>> checked_arguments = instance.check(arguments)
        >>> # If there is no problem will return the following
        >>> # checked_arguments = [
        >>> # {
        >>> #   "transfer": (True, "")
        >>> # }]
        >>> assert checked_arguments[0]["transfer"][0]
        """

        if isinstance(arguments, list):
            pass
        elif isinstance(arguments, RsyncTransferTemplate):
            arguments = [arguments]
        else:
            error = (
                f"Unsupported argument type encountered. arguments = {type(arguments)}"
            )
            error += f" where {type(RsyncTransferTemplate)} is expected"
            raise Exception(error)

        checks = []

        # Here we are cycling a list of dicts
        for index in range(len(arguments)):
            if hasattr(arguments[index], "transfer"):
                checks = self._validateAction("transfer", checks, arguments[index])

        return checks
