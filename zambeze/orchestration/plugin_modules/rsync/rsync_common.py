#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ...system_utils import userExists
from ...network import isAddressValid

# Standard imports
from dataclasses import asdict
import pathlib

SUPPORTED_ACTIONS = {"transfer": False}
PLUGIN_NAME = "rsync"
#############################################################
# Assistant Functions
#############################################################


# def requiredEndpointKeysExist(action_endpoint: dict) -> tuple[bool, str]:
#    """Returns a tuple with the first element set to true if
#    action_endpoint contains "ip","user" and "path" keys
#
#    :param action_endpoint: the object that is being checked
#    :type action_endpoint: dict
#
#    :Example:
#
#    >>> action_endpoint = {
#    >>>     "ip": "138.131.32.5",
#    >>>     "user": "cades",
#    >>>     "path": "/home/cades/folder1/out.txt"
#    >>> }
#    >>> fields_exist = requiredEndpointKeysExist( action_endpoint)
#    >>> assert fields_exist[0]
#    >>> action_endpoint = {
#    >>>     "ip": "138.131.32.5",
#    >>>     "path": "/home/cades/folder1/out.txt"
#    >>> }
#    >>> # Should fail because missing "user"
#    >>> fields_exist = requiredEndpointKeysExist( action_endpoint)
#    >>> assert not fields_exist[0]
#    """
#    if hasattr(action_endpoint, "ip") or hasattr(action_endpoint, "user") or hasattr(action_endpoint, "path"):
#        if not hasattr(action_endpoint, "ip"):
#            return (False, "Missing 'ip' attr")
#        if not hasattr(action_endpoint, "user"):
#            return (False, "Missing 'user' attr")
#        if not hasattr(action_endpoint, "path"):
#            return (False, "Missing 'path' attr")
#    else:
#        if "ip" not in action_endpoint:
#            return (False, "Missing 'ip' field")
#        if "user" not in action_endpoint:
#            return (False, "Missing 'user' field")
#        if "path" not in action_endpoint:
#            return (False, "Missing 'path' field")
#    return (True, "")


# def requiredSourceAndDestinationKeysExist(action_inst: dict) -> tuple[bool, str]:
#    """Returns a tuple, with first element a bool that is set to true
#    if both source and destination endpoints contain the correct fields
#
#    Note this function does not check that the fields make since so you could have
#    a completely bogus ip address and this will function will return true.
#
#    :Example:
#
#    >>> action_inst = {
#    >>>     "source": {
#    >>>         "ip": "",
#    >>>         "user": "",
#    >>>         "path": ""
#    >>>     },
#    >>>     "destination": {
#    >>>         "ip": "",
#    >>>         "user": "",
#    >>>         "path": ""
#    >>>     }
#    >>> }
#    >>> keys_exist = requiredSourceAndDestinationKeysExist(action_inst)
#    >>> assert keys_exist[0]
#    """
#
#    if "source" in action_inst:
#        field_check = requiredEndpointKeysExist(action_inst["source"])
#        if not field_check[0]:
#            return (False, field_check[1] + "\nRequired by 'source'")
#    else:
#        return (False, "Missing required 'source' field")
#
#    if "destination" in action_inst:
#        field_check = requiredEndpointKeysExist(action_inst["destination"])
#        if not field_check[0]:
#            return (False, field_check[1] + "\nRequired by 'destination'")
#    else:
#        return (False, "Missing required 'destination' field")
#
#    return (True, "")


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

    if not isAddressValid(action_inst["source"]["ip"]):
        return (False, f"Invalid 'source' ip address detected: {action_inst['source']['ip']}")

    if not isAddressValid(action_inst["destination"]["ip"]):
        return (
            False,
            f"Invalid 'destination' ip address detected: {action_inst['destination']['ip']}",
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
            return (False, f"Source path does not exist: {action_inst['source']['path']}")

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
        if isAddressValid(action_inst.source.ip):
            if action_inst.source.ip == host_ip:
                return "source"

        if isAddressValid(action_inst.destination.ip):
            if action_inst.destination.ip == host_ip:
                return "destination"

    else:
        if isAddressValid(action_inst["source"]["ip"]):
            if action_inst["source"]["ip"] == host_ip:
                return "source"

        if isAddressValid(action_inst["destination"]["ip"]):
            if action_inst["destination"]["ip"] == host_ip:
                return "destination"

    return ""


def buildRemotePath(action_endpoint: dict) -> str:
    """Combines user ip and path to create a remote path"""
    path = action_endpoint["user"]
    path = path + "@" + action_endpoint["ip"]
    return path + ":" + action_endpoint["path"]
