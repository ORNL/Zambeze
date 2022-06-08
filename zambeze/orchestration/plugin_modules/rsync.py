# Local imports
from .plugin import Plugin

from ..system_utils import isExecutable
from ..system_utils import userExists
from ..network import isAddressValid

# Standard imports
from copy import deepcopy

import os
import subprocess
import socket

#############################################################
# Assistant Functions
#############################################################


def requiredEndpointKeysExist(action_endpoint: dict) -> bool:
    """Returns true if action_endpoint contains "ip","user" and "path" keys

    param action_endpoint: the object that is being checked
    type action_endpoint: dict

    Examples:

    action_endpoint = {
        "ip": "138.131.32.5",
        "user": "cades",
        "path": "/home/cades/folder1/out.txt"
    }

    fields_exist = requiredEndpointKeysExist( action_endpoint)
    assert fields_exist

    action_endpoint = {
        "ip": "138.131.32.5",
        "path": "/home/cades/folder1/out.txt"
    }

    # Should fail because missing "user"
    fields_exist = requiredEndpointKeysExist( action_endpoint)
    assert not fields_exist

    """
    if "ip" not in action_endpoint:
        return False
    if "user" not in action_endpoint:
        return False
    if "path" not in action_endpoint:
        return False
    return True


def requiredSourceAndDestinationKeysExist(action_inst: dict) -> bool:
    """Returns true if both source and destination endpoints contain the
    correct fields


    Note this function does not check that the fields make since so you could have
    a completely bogus ip address and this will function will return true.

    Example

    action_inst = {
        "source": {
            "ip": "",
            "user": "",
            "path": ""
        },
        "destination": {
            "ip": "",
            "user": "",
            "path": ""
        }
    }

    keys_exist = requiredSourceAndDestinationKeysExist(action_inst)
    assert keys_exist
    """

    if "source" in action_inst:
        if not requiredEndpointKeysExist(action_inst["source"]):
            return False
    else:
        return False

    if "destination" in action_inst:
        if not requiredEndpointKeysExist(action_inst["destination"]):
            return False
    else:
        return False

    return True


def requiredSourceAndDestinationValuesValid(action_inst: dict, match_host) -> bool:
    """Determines if the values are valid

    Example

    action_inst = {
        "source": {
            "ip": "172.198.43.14",
            "user": "cades",
            "path": "/home/cades/Folder1/in.txt"
        },
        "destination": {
            "ip": "198.128.243.15",
            "user": "jeff",
            "path": "/home/jeff/local/out.txt"
        }
    }

    values_valid = requiredSourceAndDestinationValuesValid(action_inst, "source")
    assert values_valid

    Extra checks are run on the source or destination
    values depending on which machine this code is running on.
    """
    if not isAddressValid(action_inst["source"]["ip"]):
        return False

    if not isAddressValid(action_inst["destination"]["ip"]):
        return False

    if match_host is None:
        return False
    # If make sure that paths defined on the host exist
    if not os.path.exists(action_inst[match_host]["path"]):
        return False

    if not userExists(action_inst[match_host]["user"]):
        return False

    return True


def isTheHostTheSourceOrDestination(action_inst, host_ip: str) -> str:
    """Determine which machine the code is running on

    If source ip address matches this machine then returns "source" 
    if the "destination" ip address matches returns "destination", and
    if neither is a match returns None
    """
    if isAddressValid(action_inst["source"]["ip"]):
        if action_inst["source"]["ip"] == host_ip:
            return "source"

    if isAddressValid(action_inst["destination"]["ip"]):
        if action_inst["destination"]["ip"] == host_ip:
            return "destination"

    return None


def buildRemotePath(action_endpoint: dict) -> str:
    """Combines user ip and path to create a remote path"""
    path = action_endpoint["user"]
    path = path + "@" + action_endpoint["ip"]
    return path + ":" + action_endpoint["path"]


#############################################################
# Class
#############################################################
class Rsync(Plugin):
    """Class serves as an example of a plugin"""

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

        param config: configuration options
        type config: dict

        In this case the configure method checks to make sure that the rsync binary is 
        available. If an ssh key file path is provided it also checks to make sure it
        is a valid path.

        config = {
            "private_ssh_key": "path to ssh key"
        }

        instance = Rsync()
        instance.configure(config)
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
                    error_msg = "Private ssh key does not appear to exist" "{}".format(
                        key_path
                    )
                    raise Exception(error_msg)

        for config_argument in config.keys():
            if config_argument == "private_ssh_key":
                pass
            else:
                raise Exception(
                    "Unsupported rsync config option encountered: " f"{config_argument}"
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
        """Provides information about the instance of the plugin"""
        supported_actions = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
                supported_actions.append(action)

        return {
            "configured": self.__configured,
            "supported actions": supported_actions,
            "hostname": self.__hostname,
            "local ip": self.__local_ip,
            "ssh key": self.__ssh_key
        }

    def check(self, arguments: list[dict]) -> dict:
        """Check the arguments are supported.

        param arguments: arguments needed to run the rsync plugin
        type arguments: list[dict]

        Rsync must have a source and end destination machine provided.

        config = {
            "private_ssh_key": "path to ssh key"
        }

        arguments = [
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

        instance = Rsync()
        instance.configure(config)
        assert instance.check(arguments)
        """
        supported_actions = {}
        for action in arguments:
            if "transfer" in action.keys():
                action_key = "transfer"
                action_inst = action[action_key]
                # Start by checking that all the files have been provided

                if not requiredSourceAndDestinationKeysExist(action_inst):
                    supported_actions[action_key] = False
                    continue

                match_host = isTheHostTheSourceOrDestination(
                    action_inst, self.__local_ip
                )

                # Now that we know the fields exist ensure that they are valid
                # Ensure that at either the source or destination ip addresses
                # are associated with the local machine

                if not requiredSourceAndDestinationValuesValid(action_inst, match_host):
                    supported_actions[action_key] = False
                    continue

            # If the action is not "transfer"
            else:
                supported_actions[action_key] = False
                continue

            supported_actions[action_key] = True
        return supported_actions

    def process(self, arguments: list[dict]):
        """Equivalent to running the plugin after it has been set up

        param arguments: arguments needed to run the rsync plugin
        type arguments: list[dict]

        Example 

        config = {
            "private_ssh_key": "path to ssh key"
        }

        arguments = [
            {
                "transfer": {
                    "source": {
                        "ip": "valid ip address",
                        "path": "path to items that will be transferred",
                        "user": "user name"
                    },
                    "destination": {
                        "ip": "valid ip address",
                        "path": "path to items that will be transferred",
                        "user": "user name"
                    }
                }
            }
        ]

        instance = Rsync()
        instance.configure(config)
        if instance.check(arguments):
            instance.process(arguments)
        """

        if not self.__configured:
            raise Exception(
                f"Cannot process {self.__name} plugin, {self.__name} plugin must first be "
                "configured."
            )

        for action in arguments:
            if "transfer" in action.keys():
                action_inst = action["transfer"]

                command_list = ["rsync"]
                ssh_commands = ["-e", "ssh -i " + self.__ssh_key]
                for argument in ssh_commands:
                    command_list.append(argument)

                if "arguments" in action_inst:
                    for argument in action_inst["arguments"]:
                        command_list.append(argument)

                if action_inst["source"]["ip"] == self.__local_ip:
                    command_list.append(action_inst["source"]["path"])
                    command_list.append(buildRemotePath(action_inst["destination"]))

                elif action_inst["destination"]["ip"] == self.__local_ip:
                    command_list.append(buildRemotePath(action_inst["source"]))
                    command_list.append(action_inst["destination"]["path"])

                subprocess.call(command_list)
