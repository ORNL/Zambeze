# Local imports
from .service import Service

from ..system_utils import isExecutable
from ..network import isAddressValid

# Standard imports
from copy import deepcopy

import ipaddress
import socket

class Rsync(Service):
    """Class serves as an example of a service"""

    def __init__(self):
        self.__name = "rsync"
        self.__configured = False
        self.__supported_actions = { "transfer": False }
        self.__hostname = socket.gethostname()
        self.__local_ip = socket.gethostbyname(self.__hostname)
        pass

    def configure(self, config: dict):
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
        return {

            "configured": self.__configured,
            "supported actions": self.__supported_actions,
            "hostname": self.__hostname,
            "local ip": self.__local_ip
        }

    def check(self, arguments: list[dict]) -> dict:
        """Check the arguments are supported.

        Rsync must have a source and end destination machine provided.

        [
            "transfer": {
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
        ]
        """
        supported_actions = {}
        for action in arguments:
            if action == "transfer":

                # Start by checking that all the files have been provided
                if "source" in arguments[action]:
                    if "ip" not in arguments[action]["source"]:
                        supported_actions[action] = False
                        continue
                    if "user" not in arguments[action]["source"]:
                        supported_actions[action] = False
                        continue
                    if "path" not in arguments[action]["source"]:
                        supported_actions[action] = False
                        continue
                else:
                    supported_actions[action] = False
                    continue

                if "source" in arguments[action]:
                    if "ip" not in arguments[action]["source"]:
                        supported_actions[action] = False
                        continue
                    if "user" not in arguments[action]["source"]:
                        supported_actions[action] = False
                        continue
                    if "path" not in arguments[action]["source"]:
                        supported_actions[action] = False
                        continue
                else:
                    supported_actions[action] = False
                    continue

                # Now that we know the fields exist ensure that they are valid
                # Ensure that at either the source or destination ip addresses 
                # are associated with the local machine
                match_host = "none"
                if not isAddressValid(arguments[action]["source"]["ip"]):
                    supported_actions[action] = False 
                    continue
                else:
                    if arguments[action]["source"] == self.__local_ip:
                        match_host = "source"

                if not isAddressValid(arguments[action]["destination"]):
                    supported_actions[action] = False
                    continue
                else:
                    if arguments[action]["destination"] == self.__local_ip:
                        match_host = "destination"

                if match_host == "none":
                    supported_actions[action] = False
                    continue
                # If make sure that paths defined on the host exist
                elif os.path.exists(arguments["action"][match_host]["path"]) == False:
                    supported_actions[action] = False
                    continue
            else:
                supported_actions[action] = False
                continue

            supported_actions[action] = True

        return supported_actions

    def process(self, arguments: list[dict]):
        if not self.__configured:
            raise Exception("Cannot rsync service, must first be configured.")

        for action in arguments:
            if action == "transfer":
                if arguments[action]["source"]["ip"] == self.__local_ip:
                    command_list = ["rsync"]
                    if "arguments" in arguments[action]:
                        command_list.extend(arguments[action]["arguments"])
                    command_list.extend(arguments[action]["arguments"]["source"]["path"])

                    dest = arguments[action]["arguments"]["destination"]["user"]
                    dest = dest + "@" + arguments[action]["arguments"]["destination"]["ip"]
                    dest = dest + ":" + arguments[action]["arguments"]["destination"]["path"]
                    command_list.extend(dest)
                    subprocess.call(command_list)
                elif arguments[action]["destination"]["ip"] == self.__local_ip:
                    command_list = ["rsync"]
                    if "arguments" in arguments[action]:
                        command_list.extend(arguments[action]["arguments"])
                    command_list.extend(arguments[action]["arguments"]["destination"]["path"])

                    dest = arguments[action]["arguments"]["source"]["user"]
                    dest = dest + "@" + arguments[action]["arguments"]["source"]["ip"]
                    dest = dest + ":" + arguments[action]["arguments"]["source"]["path"]
                    command_list.extend(dest)
                    subprocess.call(command_list)
 

