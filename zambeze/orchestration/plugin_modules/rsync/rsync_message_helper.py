#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin import PluginMessageHelper
from .rsync_common import (
    validateRequiredSourceAndDestinationValuesValid
    )


# Standard imports
from typing import Optional

import logging


class RsyncMessageHelper(PluginMessageHelper):

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("rsync", logger=logger)

    def messageTemplate(self, args=None) -> dict:
        """Args can be used to generate a more flexible template. Say for
        instance you wanted to transfer several different items.
        """
        return {
                "plugin": self._name,
                "cmd": [
                    {
                        "transfer": {
                            "source": {
                                "ip": "",
                                "path": "",
                                "user": "",
                                },
                            "destination": {
                                "ip": "",
                                "path": "",
                                "user": "",
                                },
                            }
                        }
                    ],
                }

    def validateMessage(self, arguments: list[dict]) -> list:
        """Check the arguments are supported.

        :param arguments: arguments needed to run the rsync plugin
        :type arguments: list[dict]

        Rsync must have a source and end destination machine provided.

        :Example:

        >>> config = {
        >>>     "private_ssh_key": "path to ssh key"
        >>> }
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

        checks = []
        # Here we are cycling a list of dicts
        for index in range(len(arguments)):
            for action in arguments[index]:
                if action == "transfer":
                    # Check if the action is supported
                    if self._supported_actions[action] is False:
                        checks.append({action: (False, "action is not supported.")})
                        continue

                    # Start by checking that all the files have been provided
                    check = validateRequiredSourceAndDestinationValuesValid(
                        arguments[index][action]
                    )
                    if not check[0]:
                        checks.append(
                            {
                                action: (
                                    False,
                                    f"Error detected for {action}. " + check[1],
                                )
                            }
                        )
                        continue

                else:
                    checks.append({action: (False, f"{action} unsupported action\n")})
                    continue

                checks.append({action: (True, "")})
        return checks


