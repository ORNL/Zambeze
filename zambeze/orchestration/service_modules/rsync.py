# Local imports
from .service import Service

from ..system_utils import isExecutable
from ..system_utils import userExists
from ..network import isAddressValid

# Standard imports
from copy import deepcopy

import ipaddress
import os
import subprocess
import socket


class Rsync(Service):
    """Class serves as an example of a service"""

    def __init__(self):
        self.__name = "rsync"
        self.__configured = False
        self.__supported_actions = {"transfer": False}
        self.__hostname = socket.gethostname()
        self.__local_ip = socket.gethostbyname(self.__hostname)
        pass

    def configure(self, config: dict):
        """Configure rsync

        In this case the configure method doesn't really do much and doesn't
        actually use the 'config' argument passed in.
        """
        self.__config = deepcopy(config)
        # Check that rsync is available
        if isExecutable("rsync"):
            self.__configured = True
            self.__supported_actions["transfer"] = True

    @property
    def configured(self) -> bool:
        return self.__configured

    @property
    def name(self) -> str:
        return self.__name

    @property
    def help(self) -> str:
        return "rsync plugin supports a single action 'transfer'"

    @property
    def supportedActions(self) -> list[str]:
        supported_actions = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
                supported_actions.append(action)
        return supported_actions

    @property
    def info(self) -> dict:

        supported_actions = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
                supported_actions.append(action)

        return {
            "configured": self.__configured,
            "supported actions": supported_actions,
            "hostname": self.__hostname,
            "local ip": self.__local_ip,
        }

    def check(self, arguments: list[dict]) -> dict:
        """Check the arguments are supported.

        Rsync must have a source and end destination machine provided.

        [
            { "transfer": {
                "source" : {
                    "ip": "128.219.183.34",
                    "user: "",
                    "path: "",
                    },
                "destination": {
                    "ip": "172.231.41.3",
                    "user: "",
                    "path: "",
                    }
                "arguments": ["argument1","argument2"]
                }
            }
        ]
        """
        supported_actions = {}
        for action in arguments:
            if "transfer" in action.keys():
                action_key = "transfer"
                # Start by checking that all the files have been provided
                if "source" in action[action_key]:
                    if "ip" not in action[action_key]["source"]:
                        supported_actions[action_key] = False
                        continue
                    if "user" not in action[action_key]["source"]:
                        supported_actions[action_key] = False
                        continue
                    if "path" not in action[action_key]["source"]:
                        supported_actions[action_key] = False
                        continue
                else:
                    supported_actions[action_key] = False
                    continue

                if "source" in action[action_key]:
                    if "ip" not in action[action_key]["source"]:
                        supported_actions[action_key] = False
                        continue
                    if "user" not in action[action_key]["source"]:
                        supported_actions[action_key] = False
                        continue
                    if "path" not in action[action_key]["source"]:
                        supported_actions[action_key] = False
                        continue
                else:
                    supported_actions[action_key] = False
                    continue

                # Now that we know the fields exist ensure that they are valid
                # Ensure that at either the source or destination ip addresses
                # are associated with the local machine
                match_host = "none"
                if not isAddressValid(action[action_key]["source"]["ip"]):
                    supported_actions[action_key] = False
                    continue
                else:
                    if action[action_key]["source"]["ip"] == self.__local_ip:
                        match_host = "source"

                if not isAddressValid(action[action_key]["destination"]["ip"]):
                    supported_actions[action_key] = False
                    continue
                else:
                    if action[action_key]["destination"]["ip"] == self.__local_ip:
                        match_host = "destination"

                if match_host == "none":
                    supported_actions[action_key] = False
                    continue
                # If make sure that paths defined on the host exist
                if os.path.exists(action[action_key][match_host]["path"]) == False:
                    supported_actions[action_key] = False
                    continue

                if not userExists(action[action_key][match_host]["user"]):
                    supported_actions[action_key] = False
                    continue
            else:
                supported_actions[action_key] = False
                continue

            supported_actions[action_key] = True

        return supported_actions

    def process(self, arguments: list[dict]):
        if not self.__configured:
            raise Exception("Cannot rsync service, must first be configured.")

        for action in arguments.keys():
            if action == "transfer":
                if arguments[action]["source"]["ip"] == self.__local_ip:
                    command_list = ["rsync"]
                    if "arguments" in arguments[action]:
                        command_list.extend(arguments[action]["arguments"])
                    command_list.extend(
                        arguments[action]["arguments"]["source"]["path"]
                    )

                    dest = arguments[action]["arguments"]["destination"]["user"]
                    dest = (
                        dest + "@" + arguments[action]["arguments"]["destination"]["ip"]
                    )
                    dest = (
                        dest
                        + ":"
                        + arguments[action]["arguments"]["destination"]["path"]
                    )
                    command_list.extend(dest)
                    subprocess.call(command_list)
                elif arguments[action]["destination"]["ip"] == self.__local_ip:
                    command_list = ["rsync"]
                    if "arguments" in arguments[action]:
                        command_list.extend(arguments[action]["arguments"])
                    command_list.extend(
                        arguments[action]["arguments"]["destination"]["path"]
                    )

                    dest = arguments[action]["arguments"]["source"]["user"]
                    dest = dest + "@" + arguments[action]["arguments"]["source"]["ip"]
                    dest = dest + ":" + arguments[action]["arguments"]["source"]["path"]
                    command_list.extend(dest)
                    subprocess.call(command_list)
