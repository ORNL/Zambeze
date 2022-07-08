#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from .abstract_plugin import Plugin

# Third party imports
from github import Github

# Standard imports
from typing import Optional

import logging


class Git(Plugin):
    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        self.__name = "git"
        super().__init__(self.__name, logger=logger)
        self._supported_actions = {
            "add": False,
            "authorize": False,
            "clone": False,
            "commit": False,
            "create_repo": False,
            "create_branch": False,
            "delete": False,
            "delete_branch": False,
        }

    def __authorize(this, action_obj: dict):
        """Function for authorizing with GitHub"""

    def __add(this, action_obj: dict):
        """Function for adding contents to GitHub"""

    def __clone(this, action_obj: dict):
        """Function for cloning contents of a GitHub repository"""

    def __commit(this, action_obj: dict):
        """Function for commit to a GitHub"""

    def __createRepo(this, action_obj: dict):
        """Function for creating a repo on GitHub"""
    
    def __createBranch(this, action_obj: dict):
        """Function for creating a branch on GitHub"""

    def __delete(this, action_obj: dict):
        """Function for deleting from a repo on GitHub"""

    def __deleteBranch(this, action_obj: dict):
        """Function for creating a branch on GitHub"""

    def configure(self, config: dict) -> None:
        """Configure this set up the plugin."""
        self._supported_actions["authorize"] = True
        self._supported_actions["add"] = True
        self._supported_actions["commit"] = True
        self._supported_actions["clone"] = True
        self._supported_actions["create_branch"] = True
        self._supported_actions["create_repo"] = True
        self._supported_actions["delete"] = True
        self._supported_actions["delete_branch"] = True

    @property
    def configured(self) -> bool:
        raise NotImplementedError(
            "Method for indicating if plugin has been configured has not been "
            "instantiated."
        )

    @property
    def supportedActions(self) -> list[str]:
        supported_actions = []
        for action in self._supported_actions:
            if self._supported_actions[action]:
                supported_actions.append(action)
        return supported_actions

    @property
    def help(self) -> str:
        raise NotImplementedError("Missing help message that explains plugin")

    @property
    def info(self) -> dict:
        """This method is to be used after configuration step and will return
        information about the plugin such as configuration settings and
        defaults."""
        raise NotImplementedError("returns information about the plugin.")

    def check(self, arguments: list[dict]) -> dict:
        """Determine if the proposed arguments can be executed by this instance.

        :param arguments: The arguments are checked to ensure their types and
        formats are valid
        :type arguments: list[dict]
        :return: Returns the list of actions that are vaid
        :rtype: dict with the actions valid actions listed with bool set to
        True and invalid ones False

        :Example:

        >>> arguments =
        >>> [
        >>>     { "action1": { "dothis": ...} },
        >>>     { "action2": { "dothat": ...} },
        >>> ]
        >>> checked_actions = plugin.check(arguments)
        >>> for action in checked_actions:
        >>>     print(f"{action}: {checked_actions[action]}")
        >>> # Should print
        >>> # action1 True
        >>> # action2 False
        """

    def process(self, arguments: list[dict]) -> dict:

        if "base_url" in arguments:
            # Github Enterprise with custom hostname
            g = Github(base_url=arguments["base_url"],
                       login_or_token=arguments["credentials"]["access_token"])
        else:
            # using an access token
            g = Github(arguments["credentials"]["access_token"])

        if not self.__configured:
            raise Exception(f"Cannot run {self.__name} plugin, must first be configured.")

        for action_obj in arguments:
            # Make sure that the action is supported

            for key in action_obj:
                print(key)

                if key not in self.__supported_actions:
                    raise Exception(f"{key} is not supported.")

                if key == "add":
                    self.__add(action_obj[key])
                elif key == "authorize":
                    self.__authorize(action_obj[key])
                elif key == "clone":
                    self.__clone(action_obj[key])
                elif key == "commit":
                    self.__commit(action_obj[key])
                elif key == "create_branch":
                    self.__createBranch(action_obj[key])
                elif key == "create_repo":
                    self.__createRepo(action_obj[key])
                elif key == "delete":
                    self.__delete(action_obj[key])
                elif key == "delete_branch":
                    self.__deleteBranch(action_obj[key])

        return {}

