#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from .abstract_plugin import Plugin

from ..system_utils import isExecutable
from ..system_utils import userExists
from ..network import isAddressValid

# Standard imports
from typing import Optional

import logging
import pathlib
import socket
import subprocess


#############################################################
# Assistant Functions
#############################################################
def requiredEndpointKeysExist(action_endpoint: dict) -> (bool, str):
    """Returns a tuple with the first element set to true if
    action_endpoint contains "ip","user" and "path" keys

    :param action_endpoint: the object that is being checked
    :type action_endpoint: dict

    :Example:

    >>> action_endpoint = {
    >>>     "ip": "138.131.32.5",
    >>>     "user": "cades",
    >>>     "path": "/home/cades/folder1/out.txt"
    >>> }
    >>> fields_exist = requiredEndpointKeysExist( action_endpoint)
    >>> assert fields_exist[0]
    >>> action_endpoint = {
    >>>     "ip": "138.131.32.5",
    >>>     "path": "/home/cades/folder1/out.txt"
    >>> }
    >>> # Should fail because missing "user"
    >>> fields_exist = requiredEndpointKeysExist( action_endpoint)
    >>> assert not fields_exist[0]
    """
    if "ip" not in action_endpoint:
        return (False, "Missing 'ip' field")
    if "user" not in action_endpoint:
        return (False, "Missing 'user' field")
    if "path" not in action_endpoint:
        return (False, "Missing 'path' field")
    return (True, "")


def requiredSourceAndDestinationKeysExist(action_inst: dict) -> (bool, str):
    """Returns a tuple, with first element a bool that is set to true
    if both source and destination endpoints contain the correct fields

    Note this function does not check that the fields make since so you could have
    a completely bogus ip address and this will function will return true.

    :Example:

    >>> action_inst = {
    >>>     "source": {
    >>>         "ip": "",
    >>>         "user": "",
    >>>         "path": ""
    >>>     },
    >>>     "destination": {
    >>>         "ip": "",
    >>>         "user": "",
    >>>         "path": ""
    >>>     }
    >>> }
    >>> keys_exist = requiredSourceAndDestinationKeysExist(action_inst)
    >>> assert keys_exist[0]
    """

    if "source" in action_inst:
        field_check = requiredEndpointKeysExist(action_inst["source"])
        if not field_check[0]:
            return (False, field_check[1] + "\nRequired by 'source'")
    else:
        return (False, "Missing required 'source' field")

    if "destination" in action_inst:
        field_check = requiredEndpointKeysExist(action_inst["destination"])
        if not field_check[0]:
            return (False, field_check[1] + "\nRequired by 'destination'")
    else:
        return (False, "Missing required 'destination' field")

    return (True, "")


def requiredSourceAndDestinationValuesValid(
    action_inst: dict, match_host
) -> (bool, str):
    """Determines if the values are valid

    :Example:

    >>> action_inst = {
    >>>     "source": {
    >>>         "ip": "172.198.43.14",
    >>>         "user": "cades",
    >>>         "path": "/home/cades/Folder1/in.txt"
    >>>     },
    >>>     "destination": {
    >>>         "ip": "198.128.243.15",
    >>>         "user": "jeff",
    >>>         "path": "/home/jeff/local/out.txt"
    >>>     }
    >>> }
    >>> values_valid = requiredSourceAndDestinationValuesValid(action_inst, "source")
    >>> assert values_valid[0]

    Extra checks are run on the source or destination
    values depending on which machine this code is running on.
    """
    if not isAddressValid(action_inst["source"]["ip"]):
        return (
            False,
            f"Invalid 'source' ip address detected: {action_inst['source']['ip']}",
        )

    if not isAddressValid(action_inst["destination"]["ip"]):
        return (
            False,
            f"Invalid 'destination' ip address detected: {action_inst['source']['ip']}",
        )

    if match_host is None:
        return (
            False,
            "rsync requires running on either the source or destination machine you "
            + "are running from neither",
        )
    # If make sure that paths defined on the host exist
    if not pathlib.Path(action_inst[match_host]["path"]).exists():
        # If it is the destination it doesn't matter as much because
        # we will try to create it
        if match_host == "source":
            return (
                False,
                f"Source path does not exist: {action_inst[match_host]['path']}",
            )

    if not userExists(action_inst[match_host]["user"]):
        return (False, f"User does not exist: {action_inst[match_host]['user']}")

    return (True, "")


def isTheHostTheSourceOrDestination(action_inst, host_ip: str) -> str:
    """Determine which machine the code is running on

    If source ip address matches this machine then returns "source"
    if the "destination" ip address matches returns "destination", and
    if neither is a match returns None
    """
    if isAddressValid(action_inst["source"]["ip"]):
        if action_inst["source"]["ip"] == host_ip:
            return "source"

    if isAddressValid(action_inst["destination"]["ip"]):
        if action_inst["destination"]["ip"] == host_ip:
            return "destination"

    return None


def buildRemotePath(action_endpoint: dict) -> str:
    """Combines user ip and path to create a remote path"""
    path = action_endpoint["user"]
    path = path + "@" + action_endpoint["ip"]
    return path + ":" + action_endpoint["path"]


#############################################################
# Class
#############################################################
class Rsync(Plugin):
    """Class serves as an example of a plugin"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("rsync", logger=logger)
        self._configured = False
        self._supported_actions = {"transfer": False}
        self._hostname = socket.gethostname()
        self._local_ip = socket.gethostbyname(self._hostname)
        self._ssh_key = pathlib.Path.home().joinpath(".ssh/id_rsa")

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
                # Check if the action is supported
                if self._supported_actions[action] is False:
                    checks.append({action: (False, "action is not supported.")})
                    continue

                if action == "transfer":

                    # Start by checking that all the files have been provided
                    check = requiredSourceAndDestinationKeysExist(
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

                    match_host = isTheHostTheSourceOrDestination(
                        arguments[index][action], self._local_ip
                    )

                    # Now that we know the fields exist ensure that they are valid
                    # Ensure that at either the source or destination ip addresses
                    # are associated with the local machine
                    check = requiredSourceAndDestinationValuesValid(
                        arguments[index][action], match_host
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
                else:
                    checks.append({action: (False, f"{action} unsupported action\n")})
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

                if action_inst["source"]["ip"] == self._local_ip:
                    command_list.append(action_inst["source"]["path"])
                    command_list.append(buildRemotePath(action_inst["destination"]))

                elif action_inst["destination"]["ip"] == self._local_ip:
                    command_list.append(buildRemotePath(action_inst["source"]))
                    command_list.append(action_inst["destination"]["path"])

                print(command_list)
                subprocess.call(command_list)
        return {}
