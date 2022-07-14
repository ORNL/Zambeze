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
import base64
import json
import requests

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
        self.__api_base = "https://api.github.com/"

    def __checkRepoOwnerExists(self, repo_owner: str) -> bool:
        """Will check that the repo owner exists on GitHub

        :param repo_owner: The GitHub repository owner
        :type repo_owner: string
        """
        api_url = self.__api_base + f"users/{repo_owner}"
        response = requests.get(api_url)
        results = response.json()

        if "message" in results:
            if "Not Found" == results["message"]:
                print(f"Repository owner is unknown {repo_owner}")
            else:
                print("Unknown error")
                print(results["message"])
            return False
        return True

    def __checkRepoExists(self, repo_name, repo_owner, token=None) -> bool:
        """Will check that the repo exists on GitHub

        By default will check that the repo exists if it is public. If you would
        also like to check private repos the owner/user who has access must
        provide a GitHub token.

        :param repo_name: The GitHub repository that will be checked
        :type repo_name: string
        :param repo_owner: The repository owner
        :type repo_owner: string
        :param token: the token to access the repository if it is private
        :type token: string
        :return: True if the repository exists false otherwise
        :rtype: boolA

        :Note: before calling this method the checkRepoOwnerExists should be
        called to ensure the owner exists.
        """
        api_url = self.__api_base + f"repos/{repo_owner}/{repo_name}"
        headers = {
                "Authorization": f"Bearer {token}"
                }

        if token is None:
            response = requests.get(api_url)
        else:
            response = requests.get(api_url, headers=headers)

        results = response.json()

        print(results)

        if "message" in results:
            if "Not Found" == results["message"]:
                print(f"Repo is not known {repo_name}, if it is a private repo make\
                        sure you provide authentication.")
            else:
                print("Unknown error")
                print(results["message"])
            return False
        return True


    def __checkAdd(self, action_obj: dict) -> bool:
        """Function ensures that the action_obj is provided with the right fields

        :param action_obj: json paramters needed to add an object to a GitHub repo
        :type action_obj: dict
        :return: True if the action_obj has the required components, False
        otherwise
        :rtype: bool

        Required parameters include:

        "repo"
        "owner"
        "source"
        "destination"
        "credentials"
        """
        # Check that the following required parameters have been provided
        required_keys = ["repo", "owner", "source", "destination",
                         "credentials"]

        for key in required_keys:
            if key not in action_obj:
                return False

        if "path" not in action_obj["source"]:
            return False

        if "path" not in action_obj["destination"]:
            return False

        if "user_name" not in action_obj["credentials"]:
            return False

        if "access_token" not in action_obj["credentials"]:
            return False

        if "email" not in action_obj["credentials"]:
            return False

        if not self.__checkRepoOwnerExists(action_obj["owner"]):
            return False

        token = action_obj["credentials"]["access_token"]
        if not self.__checkRepoExists(action_obj["repo"],
                                      action_obj["owner"],
                                      token=token):
            return False

        return True

    def __add(self, action_obj: dict):
        """Function for adding contents to GitHub

        :param action_obj: needed content to execute the action
        :type action_obj: dict

        The REST API documentation for this call can be found [here](
        https://docs.github.com/en/rest/repos/contents#create-a-file).

        :Example:

        >>> action_obj = {
        >>>     "repo": "Name of repository",
        >>>     "owner": "Owner of repository",
        >>>     "branch": "Name of branch",
        >>>     "source": {
        >>>             "type": "posix absolute",
        >>>             "path": "path to file local"
        >>>     },
        >>>     "destination": {
        >>>             "type": "GitHub repository root",
        >>>             "path": "path to file local"
        >>>     },
        >>>     "commit_message": "Adding a file",
        >>>     "credentials": {
        >>>         "user_name": "BobMarley",
        >>>         "access_token": "user access token",
        >>>         "email": "user@awesome.com"
        >>>     }
        >>> }

        path will be converted to base64 encoded string and then sent.
        """
        content = ""
        with open(action_obj["source"]["path"]) as f:
            content = base64.b64encode(f.read())

        url = (self.__api_base + "repos/"
               + action_obj["owner"] + "/"
               + action_obj["repo"] + "/"
               + action_obj["destination"]["path"])
        headers = {
                "Authorization": "token " +
                action_obj["credentials"]["access_token"],
                "Accept": "application/vnd.github+json"
                }
        body = {
                "message": action_obj["commit_message"],
                "committer": {
                    "name": action_obj["credentials"]["user_name"],
                    "email": action_obj["credentials"]["email"]
                    },
                "content": content
                }
        response = requests.put(url, data=json.dumps(body), headers=headers)
        response.json()

#    def __clone(this, action_obj: dict):
#        """Function for cloning contents of a GitHub repository"""
#
#    def __commit(this, action_obj: dict):
#        """Function for commit to a GitHub"""
#
#    def __createRepo(this, action_obj: dict):
#        """Function for creating a repo on GitHub"""
#    
#    def __createBranch(this, action_obj: dict):
#        """Function for creating a branch on GitHub"""
#
#    def __delete(this, action_obj: dict):
#        """Function for deleting from a repo on GitHub"""
#
#    def __deleteBranch(this, action_obj: dict):
#        """Function for creating a branch on GitHub"""

    def configure(self, config: dict) -> None:
        """Configure this set up the plugin.

        :param config: Configuration for the plugin
        :type config: dict
        """
        # self._supported_actions["authorize"] = True
        self._supported_actions["add"] = True
        # self._supported_actions["commit"] = True
        # self._supported_actions["clone"] = True
        # self._supported_actions["create_branch"] = True
        # self._supported_actions["create_repo"] = True
        # self._supported_actions["delete"] = True
        # self._supported_actions["delete_branch"] = True

        self.__configured = True

    @property
    def configured(self) -> bool:
        return self.__configured

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
        supported_actions = {}
        for action_obj in arguments:
            # Make sure that the action is supported

            for key in action_obj:
                print(key)

                if key not in self.__supported_actions:
                    raise Exception(f"{key} is not supported.")

                if key == "add":
                    supported_actions["key"] = self.__checkAdd(action_obj[key])

        return supported_actions


    def process(self, arguments: list[dict]) -> dict:
        """Run actions

        :NOTE: Authentication

        All users must provide an access token and username any time they want
        to execute a command with one of their repositories.

        :Example:

        >>> arguments = [
        >>>     {   "add": {
        >>>             "repo": "Name of repository",
        >>>             "branch": "Name of branch",
        >>>             "path": "path to file",
        >>>             "commit_message": "Adding a file",
        >>>             "credentials": {
        >>>                 "user_name": "BobMarley",
        >>>                 "access_token": "user access token",
        >>>                 "email": "user@awesome.com"
        >>>             }
        >>>         }
        >>>     }
        >>> ]
        >>> git_plugin = Git()
        >>> git_plugin.process(arguments)
        """
#        if "base_url" in arguments:
#            # Github Enterprise with custom hostname
#            g = Github(base_url=arguments["base_url"],
#                       login_or_token=arguments["credentials"]["access_token"])
#        else:
#            # using an access token
#            g = Github(arguments["credentials"]["access_token"])
#
        if not self.__configured:
            error_msg = f"Cannot run {self.__name} plugin, must first be configured."
            raise Exception(error_msg)

        for action_obj in arguments:
            # Make sure that the action is supported

            for key in action_obj:
                print(key)

                if key not in self.__supported_actions:
                    raise Exception(f"{key} is not supported.")

                if key == "add":
                    self.__add(action_obj[key])
#                elif key == "authorize":
#                    self.__authorize(action_obj[key])
#                elif key == "clone":
#                    self.__clone(action_obj[key])
#                elif key == "commit":
#                    self.__commit(action_obj[key])
#                elif key == "create_branch":
#                    self.__createBranch(action_obj[key])
#                elif key == "create_repo":
#                    self.__createRepo(action_obj[key])
#                elif key == "delete":
#                    self.__delete(action_obj[key])
#                elif key == "delete_branch":
#                    self.__deleteBranch(action_obj[key])
#
        return {}

