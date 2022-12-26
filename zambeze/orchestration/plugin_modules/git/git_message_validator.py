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
from .git_common import (
    PLUGIN_NAME,
)

# Standard imports
from dataclasses import asdict
from typing import Optional, overload
import logging

def check_path(path_name: str, path: str, msg: str, success: bool) -> tuple[bool, str]:
    """Takes a path string and ensures it is correctly formatted.

    :param path_name: The name of the type of the file path i.e. "source"
    :type path_name: str
    :param path: The actual path that is being checked
    :type path: str
    :param msg: The existing error messages that the function will append to
    :type msg: str
    :param success: Whether all previous checks have been successful or not
    :type success: bool
    """
    if not path:
        msg = msg + f"\nError {path_name} path cannot be empty"
        return False, msg

    if path.endswith("/"):
        msg = msg + f"\nError {path_name} path must end with a filename, path"
        msg = msg + f" is {path}"
        return False, msg
    return success, msg


def contains_subkey(
    action_name: str, obj: dict, key: str, subkey: str, is_success: bool, msg: str
) -> tuple[bool, str]:
    """Checks if the the object contains a subkey

    :param action_name: Describes what action is being called for better logging
    :type action_name: str
    :param obj: The object being checked
    :type obj: The object is a dict
    :param key: The objects key, where we will be checking for a subkey
    :type key: str
    :param subkey: The subkey of the object that is being checked
    :type subkey: str
    :param is_success: The parameter that determines if previous checks have
    been successful.
    :type is_success: bool
    :param msg: The error messages that have been accumulated.
    :type msg: str

    This function checks to see if a subkey exists, if no problems are detected
    then the original 'is_success' and 'msg' will be returned, if problems
    are detected, then an error message will be appeneded to 'msg' and a 'False'
    value will be returned.
    """
    if subkey not in obj[key]:
        msg = msg + f"\n'{subkey}' key not found in '{key}' in {action_name} action"
        return False, msg
    return is_success, msg



class GitMessageValidator(PluginMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)


    def __validateCommit(self, action_obj: dict) -> tuple[bool, str]:
        # Check that the following required parameters have been provided
        required_keys = ["repo", "owner", "source", "destination", "credentials"]

        msg = ""
        for key in required_keys:
            if key not in action_obj:
                return (
                    False,
                    f"\nrequired key: {key} is missing from the \
'commit' action.",
                )

        success = True
        keys = [
            "source",
            "source",
            "destination",
            "destination",
            "credentials",
            "credentials",
            "credentials",
        ]
        subkeys = ["path", "type", "path", "type", "user_name", "access_token", "email"]
        for (key, subkey) in zip(keys, subkeys):
            success, msg = contains_subkey(
                "commit action", action_obj, key, subkey, success, msg
            )

        access_token = None
        if success:
            access_token = action_obj["credentials"]["access_token"]


        dest_path = action_obj["destination"]["path"]
        success, msg = check_path("destination", dest_path, msg, success)



    def __validateDownload(self, action_obj: dict) -> tuple[bool, str]:
        # Check that the following required parameters have been provided
        required_keys = ["repo", "owner", "source", "destination", "credentials"]

        msg = ""
        for key in required_keys:
            if key not in action_obj:
                return (
                    False,
                    f"\nrequired key: {key} is missing from the \
'download' action.",
                )

        success = True
        keys = ["source", "source", "destination", "destination", "credentials"]
        subkeys = ["path", "type", "path", "type", "access_token"]
        for (key, subkey) in zip(keys, subkeys):
            success, msg = contains_subkey(
                "download action", action_obj, key, subkey, success, msg
            )

        source_path = action_obj["source"]["path"]
        success, msg = check_path("source", source_path, msg, success)

    def _validateAction(self, action: str, checks: list, arguments: dict):

        if not isinstance(arguments, dict):
            arguments = asdict(arguments)

        if action == "commit":
            # Start by checking that all the files have been provided
            print("**************************************************")
            print(arguments)
            for item in arguments["commit"]["items"]:
#                check = validateRequiredSourceAndDestinationValuesValid(item)
#
#                if not check[0]:
#                    checks.append(
#                        {action: (False, f"Error detected for {action}. " + check[1])}
#                    )
#
        else:
            checks.append({action: (False, f"{action} unsupported action\n")})
            return checks

        checks.append({action: (True, "")})
        return checks

    def validateAction(self, arguments: dict, action) -> list:
        """Check the arguments are supported.

        >>> config = {
        >>> }
        >>> # Assumes you are provided with a single dict not a list of dicts
        >>> arguments = {
        >>>     
        >>> }
        >>> instance = Git()
        >>> instance.configure(config)
        >>> checked_arguments = instance.check(arguments)
        >>> # If there is no problem will return the following
        >>> # checked_arguments = [
        >>> # {
        >>> #   "transfer": (True, "")
        >>> # }]
        >>> assert checked_arguments[0]["commit"][0]
        """
        checks = []
        return self._validateAction(action, checks, arguments)

    @overload  # pyre-ignore[14]
    def validateMessage(self, arguments: RsyncTransferTemplate) -> list:
        ...

    @overload
    def validateMessage(self, arguments: list[dict]) -> list:
        ...

    def validateMessage(self, arguments):
        """Check the arguments are supported.

        :param arguments: arguments needed to run the rsync plugin
        :type arguments: list[dict]


        :Example:

        >>> config = {
        >>> }
        >>> # Assumes you are provided with a list of dicts
        >>> arguments = [
        >>>     {
        >>>         
        >>>     }
        >>> ]
        >>> instance = Git()
        >>> instance.configure(config)
        >>> checked_arguments = instance.check(arguments)
        >>> # If there is no problem will return the following
        >>> # checked_arguments = [
        >>> # {
        >>> #   "transfer": (True, "")
        >>> # }]
        """

        if isinstance(arguments, list):
            pass
        elif isinstance(arguments, GitTemplate):
            arguments = [arguments]
        else:
            error = (
                f"Unsupported argument type encountered. arguments = {type(arguments)}"
            )
            error += f" where {type(GitTemplate)} is expected"
            raise Exception(error)

        checks = []

        # Here we are cycling a list of dicts
        for index in range(len(arguments)):
            if hasattr(arguments[index], "commit"):
                checks = self._validateAction("commit", checks, arguments[index])
            if hasattr(arguments[index], "download"):
                checks = self._validateAction("download", checks, arguments[index])

        return checks
