#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin import Plugin
from .git_uri_separator import GitURISeparator
from ..file_uri_separator import FileURISeparator

# Third party imports
import base64
import json
import requests

# Standard imports
from typing import Optional

import logging


class Git(Plugin):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.__name = "git"
        super().__init__(self.__name, logger=logger)
        self.__git_uri_separator = GitURISeparator(logger=logger)
        self.__file_uri_separator = FileURISeparator(logger=logger)
        self.__supported_actions = {
            "authorize": False,
            "clone": False,
            "commit": False,
            "create_repo": False,
            "create_branch": False,
            "delete": False,
            "delete_branch": False,
            "download": False,
        }

        self.__configured = False
        self.__api_base = "https://api.github.com/"

    def __testConnectionToGitHubAPI(self) -> tuple[bool, str]:
        """Will test the connection to the GitHub API

        :return: True if able to connect, False otherwise with error message
        :rtype: tuple[bool, st])
        """
        api_url = self.__api_base + "users/octocat"
        try:
            requests.get(api_url)
        except Exception as e:
            error_msg = "Unable to connect to GitHub API\n"
            error_msg = error_msg + repr(e)
            return False, error_msg

        return True, ""

    def __checkBranchExists(
        self, repo_name, repo_owner, branch="main", access_token=None
    ) -> tuple[bool, str]:
        """Will check if the branch exists on the remote repository"""
        api_url = self.__api_base
        api_url = api_url + f"repos/{repo_owner}/{repo_name}/branches/{branch}"
        try:
            if access_token:
                header = {"Authorization": f"token {access_token}"}
                response = requests.get(api_url, headers=header)
            else:
                response = requests.get(api_url)
        except requests.ConnectionError as e:
            return False, str(e)

        results = response.json()

        if "message" in results:
            error_msg = ""
            if "Branch not found" == results["message"]:
                error_msg = f"Branch is not found {branch}"
            else:
                error_msg = results["message"]
            return False, error_msg
        return True, ""

    def __checkRepoOwnerExists(
        self, repo_owner: str, access_token=None
    ) -> tuple[bool, str]:
        """Will check that the repo owner exists on GitHub

        :param repo_owner: The GitHub repository owner
        :type repo_owner: string
        :param access_token: Though you don't need an access token to query the
        repo owner, if you provide one you will be given higher rate limits to
        the GitHub API.
        :type access_token: str or None
        """
        api_url = self.__api_base + f"users/{repo_owner}"
        try:
            if access_token:
                header = {"Authorization": f"token {access_token}"}
                response = requests.get(api_url, headers=header)
            else:
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

    def __checkRepoExists(self, repo_name, repo_owner, token=None) -> tuple[bool, str]:
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

    def __checkDownload(self, action_obj: dict) -> tuple[bool, str]:
        """Function ensures that the action_obj is provided with the right fields

        :param action_obj: json paramters needed to commit an object to a GitHub repo
        :type action_obj: dict
        :return: True if the action_obj has the required components, False
        otherwise, if there is an error a string is also returned
        :rtype: tuple[bool, str]

        Required parameters include:

        "items[0].source"
        "destination"

        Optional parameters
        "credentials.email"
        "credentials.access_token"
        "credentials.user_name"

        :Example:

        >>> action_obj = {
        >>>     "items": [{
        >>>         "source": "git URI",
        >>>     }],
        >>>     "destination": "file URI",
        >>>     "credentials": {
        >>>         "access_token": "user access token",
        >>>         "user_name": "users user name",
        >>>         "email": "user email",
        >>>     }
        >>> }


        """
        split_uri = self.__git_uri_separator.separate(action_obj["items"][0]["source"])

        owner_exists, error_msg = self.__checkRepoOwnerExists(split_uri["owner"])
        msg = ""
        success = True
        if not owner_exists:
            msg += error_msg
            success = False

        # Only run these checks if previous checks have all passed
        token = action_obj["credentials"]["access_token"]
        repo_exists, error_msg = self.__checkRepoExists(
            split_uri["project"], split_uri["owner"], token=token
        )
        if not repo_exists:
            msg += error_msg
            msg = (
                msg
                + f" \nUnable to verify the existance of the 'repo':\
{split_uri['project']} in 'download' action"
            )
            success = False

        return success, msg

    def __checkCommit(self, action_obj: dict) -> tuple[bool, str]:
        """Function ensures that the action_obj is provided with the right fields

        :param action_obj: json paramters needed to commit an object to a GitHub repo
        :type action_obj: dict
        :return: True if the action_obj has the required components, False
        otherwise, if there is an error a string is also returned
        :rtype: tuple[bool, str]

        Required parameters include:

        "repo"
        "owner"
        "source"
        "source.type"
        "source.path"
        "destination"
        "destination.type"
        "destination.path"
        "credentials"
        "credentials.user_name"
        "credentials.access_token"
        "credentials.email"

        Optional paramters
        "branch"

        :Example:

        >>> action_obj = {
        >>>     "repo": "Name of repository",
        >>>     "owner": "Owner of repository",
        >>>     "branch": "Name of branch",
        >>>     "source": {
        >>>         "type": "posix absolute",
        >>>         "path": "path to file local"
        >>>     },
        >>>     "destination": {
        >>>         "type": "GitHub repository root",
        >>>         "path": "path to file as it should appear in the repo"
        >>>     },
        >>>     "commit_message": "Adding a file",
        >>>     "credentials": {
        >>>         "user_name": "BobMarley",
        >>>         "access_token": "user access token",
        >>>         "email": "user@awesome.com"
        >>>     }
        >>> }
        """
        split_uri = self.__git_uri_separator.separate(action_obj["destination"])
        token = action_obj["credentials"]["access_token"]
        success = True
        msg = ""
        # Check if branch exists
        branch_exists, error_msg = self.__checkBranchExists(
            split_uri["project"], split_uri["owner"], split_uri["branch"], token
        )

        if not branch_exists:
            msg = (
                f"'branch' {split_uri['branch']} does not exist on GitHub repo "
                + f"{split_uri['project']} for owner {split_uri['owner']} "
            )
            success = False

        if success:
            owner_exists, error_msg = self.__checkRepoOwnerExists(
                split_uri["owner"], token
            )

            if not owner_exists:
                msg += error_msg
                success = False

            # Only run these checks if previous checks have all passed
            repo_exists, error_msg = self.__checkRepoExists(
                split_uri["project"], split_uri["owner"], token=token
            )
            if not repo_exists:
                msg += error_msg
                msg = (
                    msg
                    + f" \nUnable to verify the existance of the 'repo':\
 {split_uri['project']} in 'commit' action"
                )
                success = False

        return success, msg

    def __fileExistsOnRepo(self, action_obj, file_path) -> tuple[bool, dict]:
        """Function for getting file if it exists

        :param action_obj: needed content to execute the action
        :type action_obj: dict

        :Example:

        >>> action_obj = {
        >>>     "repo": "Name of repository",
        >>>     "owner": "Owner of repository",
        >>>     "branch": "Name of branch",
        >>>     "credentials": {
        >>>         "access_token": "user access token",
        >>>     }
        >>> }
        >>> file_obj = {
        >>>     "type": "GitHub repository root",
        >>>     "path": "path to file as it should appear in the repo"
        >>> }

        """

        clean_file_path_and_file = file_path
        if clean_file_path_and_file.startswith("/"):
            clean_file_path_and_file = clean_file_path_and_file[1:]

        url = (
            self.__api_base
            + "repos/"
            + action_obj["owner"]
            + "/"
            + action_obj["project"]
            + "/contents/"
            + clean_file_path_and_file
        )
        print(f"url is {url}")
        headers = {
            "Authorization": "token " + action_obj["credentials"]["access_token"],
            "Accept": "application/vnd.github+json",
        }

        if "branch" in action_obj:
            response = requests.get(
                url, headers=headers, params={"ref": action_obj["branch"]}
            ).json()
        else:
            print("Checking if file exists on default branch")
            response = requests.get(url, headers=headers)

        if "message" in response:
            return False, response

        return True, response

    def __GitHubAPICommitConflict(self, response: dict):
        """Function for checking if the GitHub API throws a curve ball and
        the commit requests returns with a non-ideal response.
        """
        # Check for the case where there is an API issue, possible
        # conflicts caused by race condition to API, response body will
        # look like this:
        # {
        #   'message': 'is at c72037af2b1ac70c2e7cdb539cd8bfe3d8ac353f
        # but expected 7a82ba49bdfb1ad383b3cbd2dea32f6cedd776f8',
        #   'documentation_url':
        # 'https://docs.github.com/rest/reference/repos#create-or-update-file-contents'}
        #
        # A successful response should look something like this (values have been
        # appreviated for clarity):
        #
        # {
        #   'content': {
        #      'name': 'file_name.txt',
        #      'path': 'path_in_repo_to_file.txt',
        #      'sha': 'e27944d6aeb1508de40bc9c2780104ae98204e9a',
        #      'size': 11,
        #      'url': 'https://api.github.com/repos/...2145601.txt?ref=main',
        #      'html_url': 'https://github.com/...30112145601.txt',
        #      'git_url': 'https://api.github.../blobs/e27944104ae98204e9a',
        #      'download_url': 'https://raw.githubuserc...8630112145601.txt',
        #      'type': 'file',
        #      '_links': {
        #         'self': 'https://api.github.com...668008630112145601.txt?ref=main',
        #         'git': 'https://api.github.co...t/blobs/e27944d62780104ae98204e9a',
        #         'html': 'https://github.com/Zambez...8008630112145601.txt'}},
        #         'commit': {
        #            'sha': 'c72037af2b1ac70c2e7cdb539cd8bfe3d8ac353f',
        #            'node_id': 'C_kwDOHsdMdtoAK...1MzljZDhiZmUzZDhhYzM1M2Y',
        #            'url': 'https://api.github.com/r...2e7cdb539cd8bfe3d8ac353f',
        #            'html_url': 'https://github.com/Zambeze84...0b539cd8bfe3d8ac353f',
        #            'author': {
        #               'name': 'zambeze84',
        #               'email': 'zambeze84@gmail.com',
        #               'date': '2022-11-09T15:43:55Z'
        #            },
        #            'committer': {
        #               'name': 'zambeze84',
        #               'email': 'zambeze84@gmail.com',
        #               'date': '2022-11-09T15:43:55Z'
        #            },
        #            'tree': {
        #               'sha': 'f7e7a2a2ec6dac3fd5a22d582edcc3994e24c13e',
        #               'url': 'https://api.github.com/repos/Za...2d582edcc3924c13e'},
        #               'message': 'Adding a file',
        #               'parents': [
        #                  {'sha': '7a82ba49bdfb1ad383b3cbd2dea32f6cedd776f8',
        #                   'url': 'https://api.github.com/repos/Zamb...a2f6cedd776f8',
        #                   'html_url': 'https://github.com...3cbd2dea32f6cedd776f8'
        #                  }],
        #               'verification': {
        #                  'verified': False,
        #                  'reason': 'unsigned',
        #                  'signature': None,
        #                  'payload': None
        #               }
        #           }
        #       }
        if "message" in response:
            if response["message"].startswith("is at "):
                return True
        return False

    def __commit(self, action_obj: dict):
        """Function for committing contents to GitHub

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
        >>>         "type": "posix absolute",
        >>>         "path": "path to file local"
        >>>     },
        >>>     "destination": {
        >>>         "type": "GitHub repository root",
        >>>         "path": "path to file as it should appear in the repo"
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
        file_split_uri = self.__file_uri_separator.separate(
            action_obj["items"][0]["source"]
        )
        print(file_split_uri)
        posix_file_path = file_split_uri["path"] + file_split_uri["file_name"]
        with open(posix_file_path) as f:
            file_content = f.read()
            print(file_content)

            git_split_uri = self.__git_uri_separator.separate(action_obj["destination"])
            github_repo_info = {}
            github_repo_info["project"] = git_split_uri["project"]
            github_repo_info["owner"] = git_split_uri["owner"]
            github_repo_info["branch"] = git_split_uri["branch"]
            github_repo_info["credentials"] = action_obj["credentials"]
            git_file_path = git_split_uri["path"] + git_split_uri["file_name"]
            file_exists, response = self.__fileExistsOnRepo(
                github_repo_info, git_file_path
            )

            print("Checking if file exists")
            print(response)

            encoded_content = base64.b64encode(bytes(file_content, "utf-8"))

            clean_dest_path_and_file = git_split_uri["path"]
            clean_dest_path_and_file += git_split_uri["file_name"]
            if clean_dest_path_and_file.startswith("/"):
                clean_dest_path_and_file = clean_dest_path_and_file[1:]

            url = (
                self.__api_base
                + "repos/"
                + git_split_uri["owner"]
                + "/"
                + git_split_uri["project"]
                + "/contents/"
                + clean_dest_path_and_file
            )
            headers = {
                "Authorization": "token " + action_obj["credentials"]["access_token"],
                "Accept": "application/vnd.github+json",
            }

            body = {
                "message": str(action_obj["commit_message"]),
                "committer": {
                    "name": action_obj["credentials"]["user_name"],
                    "email": action_obj["credentials"]["email"],
                },
                "content": encoded_content.decode("utf-8"),
            }

            if file_exists:
                # Need to add the "sha" to the body
                body["sha"] = response["sha"]

            print("Body of commit")
            print(body)

            attempts = 0
            while True:
                response = requests.put(
                    url, data=json.dumps(body), headers=headers
                ).json()
                print("Response")
                print(response)

                if not self.__GitHubAPICommitConflict(response):
                    break
                if attempts > 10:
                    break
                attempts += 1

            return response

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

    def __download(self, action_obj: dict):
        """Function for downloading contents from GitHub

        :param action_obj: needed content to execute the action
        :type action_obj: dict

        :Example:

        >>> action_obj = {
        >>>     "items": [{
        >>>         "source": "Git URI"
        >>>     }].
        >>>     "destination": "File URI",
        >>>     "credentials": {
        >>>         "user_name": "user name",
        >>>         "access_token": "git repo token",
        >>>         "email": "User email"
        >>>     }
        >>> }

        path will be converted to base64 encoded string and then sent.
        """
        source_split_uri = self.__git_uri_separator.separate(
            action_obj["items"][0]["source"]
        )
        destination_split_uri = self.__file_uri_separator.separate(
            action_obj["destination"]
        )
        file_path = destination_split_uri["path"]
        file_path += destination_split_uri["file_name"]
        print(f"File to write to is {file_path}")
        with open(file_path, "w+") as f:
            clean_source_path_and_file = source_split_uri["path"]
            clean_source_path_and_file += source_split_uri["file_name"]
            if clean_source_path_and_file.startswith("/"):
                clean_source_path_and_file = clean_source_path_and_file[1:]

            github_repo_info = {}
            github_repo_info["project"] = source_split_uri["project"]
            github_repo_info["owner"] = source_split_uri["owner"]
            github_repo_info["branch"] = source_split_uri["branch"]
            github_repo_info["credentials"] = action_obj["credentials"]
            git_file_path = source_split_uri["path"]
            git_file_path += source_split_uri["file_name"]

            file_exists, response = self.__fileExistsOnRepo(
                github_repo_info, git_file_path
            )

            if "message" in response:
                error_msg = ""
                if "Not Found" == response["message"]:
                    error_msg = f"File does not exist in the repo\
 {clean_source_path_and_file}"
                else:
                    error_msg = response["message"]
                print(error_msg)
                return error_msg

            content = base64.b64decode(response["content"].encode("utf-8")).decode(
                "utf-8"
            )

            print("Content to write to file is ")
            print(content)

            f.write(content)

    def configure(self, config: dict) -> None:
        """Configuration to set up the plugin.

        :parameter config: Configuration for the plugin
        :type config: dict
        """
        can_connect, message = self.__testConnectionToGitHubAPI()
        if can_connect:
            # self.__supported_actions["authorize"] = True
            self.__supported_actions["commit"] = True
            # self.__supported_actions["commit"] = True
            # self.__supported_actions["clone"] = True
            # self.__supported_actions["create_branch"] = True
            # self.__supported_actions["create_repo"] = True
            # self.__supported_actions["delete"] = True
            # self.__supported_actions["delete_branch"] = True
            self.__supported_actions["download"] = True
            self.__configured = True
        else:
            # If we cannot connect any longer to the GitHub repo we are no
            # longer correctly configured
            self.__configured = False

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

    def check(self, arguments: list[dict]) -> list[dict]:
        """Determine if the proposed arguments can be executed by this instance.

        :param arguments: The arguments are checked to ensure their types and
        formats are valid
        :type arguments: list[dict]
        :return: Returns the list of actions that are vaid
        :rtype: list[dict] with the actions valid actions listed with bool set to
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
        >>> for item in checked_actions:
        >>>     for action in item:
        >>>         print(f"{action}: {item['action']}")
        >>> # Should print
        >>> # commit (True,"")
        """
        checks = []
        for index in range(len(arguments)):
            for action in arguments[index]:
                if action not in self.__supported_actions:
                    checks.append({action: (False, "action is not supported.")})
                    continue

                if action == "commit":
                    checks.append(
                        {action: self.__checkCommit(arguments[index][action])}
                    )
                elif action == "download":
                    checks.append(
                        {action: self.__checkDownload(arguments[index][action])}
                    )

        return checks

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
                elif key == "download":
                    print("Running download section")
                    self.__download(action_obj[key])
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
