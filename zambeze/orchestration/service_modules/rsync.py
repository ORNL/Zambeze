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
        self.__ssh_key = os.path.expanduser("~") + "/.ssh/id_rsa"
        pass

    def configure(self, config: dict):
        """Configure rsync

        In this case the configure method doesn't really do much and doesn't
        actually use the 'config' argument passed in.
        """

        # Check that rsync is available
        if isExecutable("rsync"):
            self.__configured = True
            self.__supported_actions["transfer"] = True
            if "private_ssh_key" in config:
                if os.path.exists(config["private_ssh_key"]):
                    self.__ssh_key = config["private_ssh_key"]
                else:
                    key_path = config["private_ssh_key"]
                    raise Exception(
                        f"Private ssh key does not appear to exist "
                        "{config[key_path]}"
                    )

        for config_argument in config.keys():
            if config_argument == "private_ssh_key":
                pass
            else:
                raise Exception(
                    f"Unsupported rsync config option encountered: "\
                            "{config_argument}"
                )
        self.__config = deepcopy(config)

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
                action_inst = action[action_key]
                # Start by checking that all the files have been provided
                if "source" in action_inst:
                    if "ip" not in action_inst["source"]:
                        supported_actions[action_key] = False
                        continue
                    if "user" not in action_inst["source"]:
                        supported_actions[action_key] = False
                        continue
                    if "path" not in action_inst["source"]:
                        supported_actions[action_key] = False
                        continue
                else:
                    supported_actions[action_key] = False
                    continue

                if "destination" in action_inst:
                    if "ip" not in action_inst["destination"]:
                        supported_actions[action_key] = False
                        continue
                    if "user" not in action_inst["destination"]:
                        supported_actions[action_key] = False
                        continue
                    if "path" not in action_inst["destination"]:
                        supported_actions[action_key] = False
                        continue
                else:
                    supported_actions[action_key] = False
                    continue

                # Now that we know the fields exist ensure that they are valid
                # Ensure that at either the source or destination ip addresses
                # are associated with the local machine
                match_host = "none"
                if not isAddressValid(action_inst["source"]["ip"]):
                    supported_actions[action_key] = False
                    continue
                else:
                    if action_inst["source"]["ip"] == self.__local_ip:
                        match_host = "source"

                if not isAddressValid(action_inst["destination"]["ip"]):
                    supported_actions[action_key] = False
                    continue
                else:
                    if action_inst["destination"]["ip"] == self.__local_ip:
                        match_host = "destination"

                if match_host == "none":
                    supported_actions[action_key] = False
                    continue
                # If make sure that paths defined on the host exist
                if os.path.exists(action_inst[match_host]["path"]) == False:
                    supported_actions[action_key] = False
                    continue

                if not userExists(action_inst[match_host]["user"]):
                    supported_actions[action_key] = False
                    continue
            # If the action is not "transfer"
            else:
                supported_actions[action_key] = False
                continue

            supported_actions[action_key] = True
        return supported_actions

    def process(self, arguments: list[dict]):
        if not self.__configured:
            raise Exception(
                "Cannot process rsync service, rsync service must first be "
                "configured."
            )

        for action in arguments:
            if "transfer" in action.keys():
                action_inst = action["transfer"]
                command_list = []
                if action_inst["source"]["ip"] == self.__local_ip:
                    command_list = ["rsync"]
                    ssh_commands = ["-e", "ssh -i " + self.__ssh_key]
                    for argument in ssh_commands:
                        command_list.append(argument)

                    if "arguments" in action_inst:
                        for argument in action_inst["arguments"]:
                            command_list.append(argument)

                    command_list.append(action_inst["source"]["path"])

                    dest = action_inst["destination"]["user"]
                    dest = dest + "@" + action_inst["destination"]["ip"]
                    dest = dest + ":" + action_inst["destination"]["path"]
                    command_list.append(dest)

                elif action_inst["destination"]["ip"] == self.__local_ip:
                    command_list = ["rsync"]
                    ssh_commands = ["-e", "ssh -i " + self.__ssh_key]
                    for argument in ssh_commands:
                        command_list.append(argument)

                    if "arguments" in action_inst:
                        for argument in action_inst["arguments"]:
                            # Cannot use extend because they are strings and will break
                            # each work into separate characters
                            command_list.append(argument)

                    source = action_inst["source"]["user"]
                    source = source + "@" + action_inst["source"]["ip"]
                    source = source + ":" + action_inst["source"]["path"]
                    command_list.append(source)

                    command_list.append(action_inst["destination"]["path"])

                print("rsync command list is")
                print(command_list)
                subprocess.call(command_list)
