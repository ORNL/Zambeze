#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin import Plugin
from .rsync_common import (
    buildRemotePath,
    isTheHostTheSourceOrDestination,
    PLUGIN_NAME,
    requiredSourceAndDestinationValuesValid,
    SUPPORTED_ACTIONS,
)
from .rsync_message_validator import RsyncMessageValidator
from ...system_utils import isExecutable

# Standard imports
from typing import Optional

import logging
import pathlib
import socket
import subprocess


#############################################################
# Class
#############################################################
class Rsync(Plugin):
    """Class serves as an example of a plugin"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)
        self._configured = False
        self._supported_actions = SUPPORTED_ACTIONS
        self._hostname = socket.gethostname()
        self._local_ip = socket.gethostbyname(self._hostname)
        self._ssh_key = pathlib.Path.home().joinpath(".ssh/id_rsa")
        self._message_validator = RsyncMessageValidator(logger)

    def messageTemplate(self, args=None) -> dict:
        """Args can be used to generate a more flexible template. Say for
        instance you wanted to transfer several different items.
        """
        return {
            "plugin": self._name,
            "cmd": [
                {
                    "transfer": {
                        "source": {"ip": "", "path": "", "user": ""},
                        "destination": {"ip": "", "path": "", "user": ""},
                    }
                }
            ],
        }

    def configure(self, config: dict) -> None:
        """Configure rsync

        :param config: configuration options
        :type config: dict

        In this case the configure method checks to make sure that the rsync binary is
        available. If an ssh key file path is provided it also checks to make sure it
        is a valid path.

        :Example:

        >>> config = {
        >>>     "private_ssh_key": "path to ssh key"
        >>> }
        >>> instance = Rsync()
        >>> instance.configure(config)
        """
        self._logger.debug(f"Configuring {self._name} plugin")

        # Check that rsync is available
        if isExecutable("rsync"):
            self._configured = True
            self._supported_actions["transfer"] = True
            if "private_ssh_key" in config:
                if pathlib.Path(config["private_ssh_key"]).exists():
                    self._ssh_key = config["private_ssh_key"]
                else:
                    error_msg = (
                        f'Private ssh key does not exist {config["private_ssh_key"]}'
                    )
                    raise Exception(error_msg)
            self._logger.debug(f"  Private key: {self._ssh_key}")

        for config_argument in config.keys():
            if config_argument == "private_ssh_key":
                pass
            else:
                raise Exception(
                    f"Unsupported rsync config option encountered: {config_argument}"
                )

    @property
    def configured(self) -> bool:
        return self._configured

    @property
    def help(self) -> str:
        return "rsync plugin supports a single action 'transfer'"

    @property
    def supportedActions(self) -> list[str]:
        supported_actions = []
        for action in self._supported_actions:
            if self._supported_actions[action]:
                supported_actions.append(action)
        return supported_actions

    @property
    def info(self) -> dict:
        """Provides information about the instance of the plugin"""
        supported_actions = []
        for action in self._supported_actions:
            if self._supported_actions[action]:
                supported_actions.append(action)

        return {
            "configured": self._configured,
            "supported_actions": supported_actions,
            "hostname": self._hostname,
            "local_ip": self._local_ip,
            "ssh_key": self._ssh_key,
        }

    def check(self, arguments: list[dict]) -> list[dict]:
        """Check the arguments are supported

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
                schema_checks = self._message_validator.validateAction(
                    arguments[index], action
                )

                if len(schema_checks) > 0:
                    if schema_checks[0][action][0] is False:
                        checks.extend(schema_checks)
                        continue

                if action == "transfer":
                    match_host = isTheHostTheSourceOrDestination(
                        arguments[index][action]["items"][0], self._local_ip
                    )

                    # Now that we know the fields exist ensure that they are valid
                    # Ensure that at either the source or destination ip addresses
                    # are associated with the local machine
                    check = requiredSourceAndDestinationValuesValid(
                        arguments[index][action]["items"][0], match_host
                    )
                    if not check[0]:
                        checks.append(
                            {
                                action: (
                                    False,
                                    f"Error detected while running {action}. "
                                    + check[1],
                                )
                            }
                        )
                        continue

                checks.append({action: (True, "")})

        return checks

    def process(self, arguments: list[dict]):
        """Equivalent to running the plugin after it has been set up

        :param arguments: arguments needed to run the rsync plugin
        :type arguments: list[dict]

        :Example:

        >>> config = {
        >>>     "private_ssh_key": "path to ssh key"
        >>> }
        >>> arguments = [
        >>>     {
        >>>         "transfer": {
        >>>             "source": {
        >>>                 "ip": "valid ip address",
        >>>                 "path": "path to items that will be transferred",
        >>>                 "user": "user name"
        >>>             },
        >>>             "destination": {
        >>>                 "ip": "valid ip address",
        >>>                 "path": "path to items that will be transferred",
        >>>                 "user": "user name"
        >>>             },
        >>>             "arguments": ["-a"]
        >>>         }
        >>>     }
        >>> ]
        >>> instance = Rsync()
        >>> instance.configure(config)
        >>> if instance.check(arguments):
        >>>     instance.process(arguments)
        """
        if not self._configured:
            raise Exception(
                f"Cannot process {self._name} plugin, {self._name} "
                "plugin must first be configured."
            )

        for action in arguments:
            if "transfer" in action:
                action_inst = action["transfer"]

                command_list = ["rsync"]
                ssh_commands = ["-e", "ssh -i " + self._ssh_key]
                for argument in ssh_commands:
                    command_list.append(argument)

                if "arguments" in action_inst:
                    for argument in action_inst["arguments"]:
                        command_list.append(argument)

                for item in action_inst["items"]:
                    if item["source"]["ip"] == self._local_ip:
                        command_list.append(item["source"]["path"])
                        command_list.append(buildRemotePath(item["destination"]))

                    elif item["destination"]["ip"] == self._local_ip:
                        command_list.append(buildRemotePath(item["source"]))
                        command_list.append(item["destination"]["path"])
                    # only support one item
                    break

                #subprocess.call(command_list)
                shell_exec = subprocess.Popen(
                    command_list,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1)

                for line in shell_exec.stdout:
                    self._logger.debug(line)

                return_code = shell_exec.wait()
                self._logger.debug(f"Return Code: {return_code}")
        return {}
