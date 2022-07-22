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
import time

# Standard imports
from typing import Optional

import logging


class Git(Plugin):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.__name = "git"
        super().__init__(self.__name, logger=logger)
        self.__supported_actions = {
            "authorize": False,
            "clone": False,
            "commit": True,
            "create_repo": False,
            "create_branch": False,
            "delete": False,
            "delete_branch": False,
        }

        self.__configured = False
        self.__api_base = "https://api.github.com/"

    def __checkRepoOwnerExists(self, repo_owner: str) -> (bool, str):
        """Will check that the repo owner exists on GitHub

        :param repo_owner: The GitHub repository owner
        :type repo_owner: string
        """
        api_url = self.__api_base + f"users/{repo_owner}"
        try:
            response = requests.get(api_url)
        except requests.ConnectionError as e:
            return False, str(e)

        results = response.json()

        if "message" in results:
            error_msg = ""
            if "Not Found" == results["message"]:
                error_msg = f"Repository owner is unknown {repo_owner}"
            else:
                error_msg = results["message"]
            return False, error_msg
        return True, ""

    def __checkRepoExists(self, repo_name, repo_owner, token=None) -> (bool, str):
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
        header = {"Authorization": f"token {token}"}

        if repo_name.endswith(".git"):
            return (
                False,
                f"Please remove '.git' from the repo name \
{repo_name}",
            )

        try:
            if token is None:
                response = requests.get(api_url)
            else:
                response = requests.get(api_url, headers=header)
        except requests.ConnectionError as e:
            return False, str(e)

        results = response.json()

        if "message" in results:
            msg = ""
            if "Not Found" == results["message"]:
                msg = f"Repo is not known {repo_name}, if it is a private repo make\
 sure you provide authentication."
            else:
                msg = results["message"]
            return (False, msg)
        return (True, "")

    def __checkCommit(self, action_obj: dict) -> (bool, str):
        """Function ensures that the action_obj is provided with the right fields

        :param action_obj: json paramters needed to commit an object to a GitHub repo
        :type action_obj: dict
        :return: True if the action_obj has the required components, False
        otherwise, if there is an error a string is also returned
        :rtype: (bool, str)

        Required parameters include:

        "repo"
        "owner"
        "source"
        "destination"
        "credentials"
        """
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

        check_success = True
        if "path" not in action_obj["source"]:
            msg = msg + "\n'path' key not found in 'source' in 'commit' action"
            check_success = False

        if "type" not in action_obj["source"]:
            msg = msg + "\n'type' key not found in 'source' in 'commit' action"
            check_success = False

        if "path" not in action_obj["destination"]:
            msg = msg + "\n'path' key not found in 'destination' in 'commit' action"
            check_success = False

        if "type" not in action_obj["destination"]:
            msg = msg + "\n'type' key not found in 'destination' in 'commit' action"
            check_success = False

        if "user_name" not in action_obj["credentials"]:
            msg = msg + "\n'user_name' key not found in 'credentials' in "
            msg = msg + "'commit' action"
            check_success = False

        if "access_token" not in action_obj["credentials"]:
            msg = (
                msg
                + "\n'access_token' key not found in 'credentials' in \
                        'commit' action"
            )
            check_success = False

        if "email" not in action_obj["credentials"]:
            msg = (
                msg
                + "'access_token' key not found in 'credentials' in \
                        'commit' action"
            )
            check_success = False

        if check_success:
            owner_exists, error_msg = self.__checkRepoOwnerExists(action_obj["owner"])
            if not owner_exists:
                msg = msg + error_msg
                check_success = False

            dest_path = action_obj["destination"]["path"]
            if not dest_path:
                msg = msg + "\nError destionation path cannot be empty"
                check_success = False

            if dest_path.endswith("/"):
                msg = msg + "\nError destination path must end with a filename"
                check_success = False

            # Only run these checks if previous checks have all passed
            token = action_obj["credentials"]["access_token"]
            repo_exists, error_msg = self.__checkRepoExists(
                action_obj["repo"], action_obj["owner"], token=token
            )
            if not repo_exists:
                msg = msg + error_msg
                msg = (
                    msg
                    + f" \nUnable to verify the existance of the 'repo':\
 {action_obj['repo']} in 'commit' action"
                )
                check_success = False

        return check_success, msg

    def __commit(self, action_obj: dict):
        """Function for commiting contents to GitHub

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
        >>>             "path": "path to file as it should appear in the repo"
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
        print("Trying to read from file")
        print(action_obj["source"]["path"])
        with open(action_obj["source"]["path"]) as f:
            file_content = f.read()
            print(file_content)
            encoded_content = base64.b64encode(bytes(file_content, "utf-8"))

            clean_dest_path_and_file = action_obj["destination"]["path"]
            if clean_dest_path_and_file.startswith("/"):
                clean_dest_path_and_file = clean_dest_path_and_file[1:]

            url = (
                self.__api_base
                + "repos/"
                + action_obj["owner"]
                + "/"
                + action_obj["repo"]
                + "/contents/"
                + clean_dest_path_and_file
            )
            headers = {
                "Authorization": "token " + action_obj["credentials"]["access_token"],
                "Accept": "application/vnd.github+json",
            }
            body = {
                "message": action_obj["commit_message"],
                "committer": {
                    "name": action_obj["credentials"]["user_name"],
                    "email": action_obj["credentials"]["email"],
                },
                "content": encoded_content.decode("utf-8"),
            }

            print("url")
            print(url)
            print("headers")
            print(headers)
            print("body")
            print(body)
            response = requests.put(url, data=json.dumps(body), headers=headers)
            print(response.json())

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
        """Configuration to set up the plugin.

        :param config: Configuration for the plugin
        :type config: dict
        """
        # self.__supported_actions["authorize"] = True
        self.__supported_actions["commit"] = True
        # self.__supported_actions["commit"] = True
        # self.__supported_actions["clone"] = True
        # self.__supported_actions["create_branch"] = True
        # self.__supported_actions["create_repo"] = True
        # self.__supported_actions["delete"] = True
        # self.__supported_actions["delete_branch"] = True

        self.__configured = True

    @property
    def configured(self) -> bool:
        return self.__configured

    @property
    def supportedActions(self) -> list[str]:
        supported_actions = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
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
        information = {}

        supported_actions = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
                supported_actions.append(action)

        information["actions"] = supported_actions
        return information

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

        :Example: Concrete

        >>> arguments = [
        >>>     {   "commit": {
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
        >>> checked_actions = git_plugin.check(arguments)
        >>>
        >>> for action in checked_actions:
        >>>     print(f"{action}: {checked_actions[action]}")
        >>> # Should print
        >>> # commit (True,"")

        """
        supported_actions = {}
        for action_obj in arguments:
            # Make sure that the action is supported

            for key in action_obj:
                if key not in self.__supported_actions:
                    supported_actions[key] = (False, f"{key} is not supported.")
                    continue

                if key == "commit":
                    supported_actions[key] = self.__checkCommit(action_obj[key])

        return supported_actions

    def process(self, arguments: list[dict]) -> dict:
        """Run actions

        :NOTE: Authentication

        All users must provide an access token and username any time they want
        to execute a command with one of their repositories.

        :Example:

        >>> arguments = [
        >>>     {   "commit": {
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

                if key == "commit":
                    self.__commit(action_obj[key])
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
