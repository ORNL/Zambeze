#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ...system_utils import userExists
from ...network import is_address_valid

# Standard imports
from dataclasses import asdict
import pathlib

SUPPORTED_ACTIONS = {"transfer": False}
PLUGIN_NAME = "rsync"
#############################################################
# Assistant Functions
#############################################################


def validateRequiredSourceAndDestinationValuesValid(
    action_inst: dict,
) -> tuple[bool, str]:
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
    if not isinstance(action_inst, dict):
        action_inst = asdict(action_inst)

    if not is_address_valid(action_inst["source"]["ip"]):
        return (
            False,
            f"Invalid 'source' ip address detected: {action_inst['source']['ip']}",
        )

    if not is_address_valid(action_inst["destination"]["ip"]):
        return (
            False,
            (
                "Invalid 'destination' ip address detected: "
                f"{action_inst['destination']['ip']}"
            ),
        )

    return (True, "")


def requiredSourceAndDestinationValuesValid(
    action_inst: dict, match_host
) -> tuple[bool, str]:
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
    if not isinstance(action_inst, dict):
        action_inst = asdict(action_inst)

    if match_host == "":
        return (
            False,
            "rsync requires running on either the source or destination machine you "
            + "are running from neither",
        )
    # If make sure that paths defined on the host exist
    if match_host == "source":
        if not pathlib.Path(action_inst["source"]["path"]).exists():
            # If it is the destination it doesn't matter as much because
            # we will try to create it
            return (
                False,
                f"Source path does not exist: {action_inst['source']['path']}",
            )

        if not userExists(action_inst["source"]["user"]):
            return (False, f"User does not exist: {action_inst['source']['user']}")
    else:
        if not userExists(action_inst["destination"]["user"]):
            return (False, f"User does not exist: {action_inst['destination']['user']}")

    return (True, "")


def isTheHostTheSourceOrDestination(action_inst, host_ip: str) -> str:
    """Determine which machine the code is running on

    If source ip address matches this machine then returns "source"
    if the "destination" ip address matches returns "destination", and
    if neither is a match returns None
    """
    print(f"action_inst is {action_inst}")
    if hasattr(action_inst, "source"):
        if is_address_valid(action_inst.source.ip):
            if action_inst.source.ip == host_ip:
                return "source"

        if is_address_valid(action_inst.destination.ip):
            if action_inst.destination.ip == host_ip:
                return "destination"

    else:
        if is_address_valid(action_inst["source"]["ip"]):
            if action_inst["source"]["ip"] == host_ip:
                return "source"

        if is_address_valid(action_inst["destination"]["ip"]):
            if action_inst["destination"]["ip"] == host_ip:
                return "destination"

    return ""


def buildRemotePath(action_endpoint: dict) -> str:
    """Combines user ip and path to create a remote path"""
    path = action_endpoint["user"]
    path = path + "@" + action_endpoint["ip"]
    return path + ":" + action_endpoint["path"]
