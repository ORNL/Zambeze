# Local imports
from .plugin import Plugin
from ..identity import validUUID
from ..network import externalNetworkConnectionDetected

# Third party imports
from globus_sdk import GlobusError
import globus_sdk

# Standard imports
from copy import deepcopy
from os.path import basename
from os.path import exists
from os.path import isdir
from os.path import isfile
from socket import gethostname

import json
import logging
import re
import shutil


class Globus(Plugin):
    def __init__(self):
        # Client id is specific to Zambeze project it was created by registering
        # at developers.globus.org
        self.__access_to_globus_cloud = False
        # This is the default for Zambeze
        self.__client_id = "435d07fa-8b10-4e04-b005-054c68be3f14"
        self.__collections = []
        self.__configured = False
        self.__flow = "client credential"
        self.__hostname = None
        self.__name = "globus"
        self.__supported_actions = {
            "transfer": False,
            "move_to_globus_collection": False,
            "move_from_globus_collection": False,
        }
        pass

    ###################################################################################
    # Private Methods
    ###################################################################################
    # Validation Methods
    # -----------------

    def __validConfig(self, config: dict):
        """Purpose of this method is to determine if the coniguration is correct"""

        if "authentication flow" not in config:
            raise Exception(
                "'authentication flow' key value missing from config"
                "config must have 'authentication flow' specified"
            )

        # Check that the authentication flow is supported
        if "native" == config["authentication flow"]["type"]:
            self.__flow = "native"
        elif "client credential" == config["authentication flow"]["type"]:
            self.__flow = "client credential"
        else:
            raise Exception(
                "Unsupported authentication flow detected "
                f"{config['authentication flow']['type']}"
            )

        # Check that the UUIDs are correct
        if "collections" in config:
            for local_collection in config["collections"]:
                print(local_collection)
                if not validUUID(local_collection["UUID"]):
                    raise Exception("Invalid UUID detected in plugin.")
                if not exists(local_collection["path"]):
                    # Check that the collection path is correct and exists on the local
                    # POSIX filesystem
                    raise Exception(
                        f"Invalid path detected in plugin: {local_collection['path']}"
                    )

    def __validEndPoint(self, config: dict):
        """This method can only be run after the authentication flow has been run"""

        # Check that the endpoints actually exist in Globus and are not just made up
        if "collections" in config:
            for local_collection in config["collections"]:
                # Check that the collection id is recognized by Globus and is a
                # valid globus collection UUID
                try:
                    self.__tc.get_endpoint(local_collection["UUID"])
                except globus_sdk.GlobusAPIError as e:
                    if e.http_status == 404:
                        # data = e.raw_json
                        raise Exception(
                            "Invalid collection id. Collection is unknown.")
                    else:
                        raise

    def __validActions(self):
        # If we were able to communicate with Globus then the transfer action should be
        # possible
        if self.__access_to_globus_cloud:
            self.__supported_actions["transfer"] = True
        # If we have no errors at this point then and there is at least one collection
        # then we can move to and from them
        if len(self.__collections):
            self.__supported_actions["move_to_globus_collection"] = True
            self.__supported_actions["move_from_globus_collection"] = True

    # Authentication methods
    # ----------------------
    def __nativeAuthFlow(self):
        # Using Native auth flow
        client = globus_sdk.NativeAppAuthClient(self.__client_id)

        client.oauth2_start_flow(refresh_tokens=True)
        authorize_url = client.oauth2_get_authorize_url()
        print(f"Please go to this URL and login:\n\n{authorize_url}\n")

        auth_code = input("Please enter the code you get after login here: ").strip()
        token_response = client.oauth2_exchange_code_for_tokens(auth_code)

        # globus_auth_data = 
        token_response.by_resource_server["auth.globus.org"]
        globus_transfer_data = token_response.by_resource_server[
            "transfer.api.globus.org"
        ]

        # most specifically, you want these tokens as strings
        # AUTH_TOKEN = globus_auth_data["access_token"]
        transfer_rt = globus_transfer_data["refresh_token"]
        transfer_at = globus_transfer_data["access_token"]
        expires_at_s = globus_transfer_data["expires_at_seconds"]

        # construct a RefreshTokenAuthorizer
        # note that `client` is passed to it, to allow it to do the refreshes
        self.__authorizer = globus_sdk.RefreshTokenAuthorizer(
            transfer_rt, client, access_token=transfer_at, expires_at=expires_at_s
        )

        # and try using `tc` to make TransferClient calls. Everything should just
        # work -- for days and days, months and months, even years
        self.__tc = globus_sdk.TransferClient(authorizer=self.__authorizer)

    def __clientCredentialAuthFlow(self, config: dict):
        # https://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials.html
        print("Config is")
        print(f"client id is {self.__client_id}")
        print(json.dumps(config, indent=4))
        confidential_client = globus_sdk.ConfidentialAppAuthClient(
            client_id=self.__client_id,
            client_secret=config["authentication flow"]["secret"],
        )
        print(f"client secret: {config['authentication flow']['secret']}")
        scopes = "urn:globus:auth:scope:transfer.api.globus.org:all"
        self.__authorizer = globus_sdk.ClientCredentialsAuthorizer(
            confidential_client, scopes
        )
        # create a new client
        self.__tc = globus_sdk.TransferClient(authorizer=self.__authorizer)

    # Run methods
    # -----------
    def __runTransfer(self, transfer: dict):
        # transfer dict must have the following format
        #
        # {
        #     "source_collection_UUID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        #     "destination_collection_UUID": "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
        #     "items": [
        #         { "source": {
        #               "type": "globus relative",
        #               "path": "/file1.txt"
        #               },
        #           "destination": {
        #               "type": "globus relative",
        #               "path": "dest/file1.txt"
        #               }
        #         },
        #         { "source": {
        #               "type": "globus relative",
        #               "path": "/file2.txt"
        #               },
        #           "destination": {
        #               "type": "globus relative",
        #               "path": "dest/file2.txt"
        #               }
        #         }
        #     ]
        # }
        tdata = globus_sdk.TransferData(
            self.__tc,
            transfer["source_collection_UUID"],
            transfer["destination_collection_UUID"],
            label="Zambeze Workflow",
            sync_level="checksum",
        )

        for item in transfer["items"]:
            clean_source_path = re.sub('/+', '/', item["source"]["path"])
            clean_destination_path = re.sub('/+', '/', item["destination"]["path"])
            tdata.add_item(clean_source_path, clean_destination_path)

        transfer_result = self.__tc.submit_transfer(tdata)
        print(transfer_result)

    def __runMoveToGlobusCollection(self, action_package: dict):
        """Method is designed to move a local file to a Globus collection"""
        # move dict must have the following format
        # {
        #     "source_host_name": "",
        #     "destination_collection_UUID": ""
        #     "items": [
        #         {
        #           "source": {
        #               "type": "posix users home",
        #               "path": "/file1.txt"
        #               },
        #           "destination": {
        #               "type": "globus relative",
        #               "path": "dest/file1.txt"
        #               }
        #         },
        #         {
        #           "source": {
        #               "type": "posix users home",
        #               "path": "/file2.txt"
        #               },
        #           "destination": {
        #               "type": "globus relative",
        #               "path": "dest/file2.txt"
        #               }
        #         }
        #     ]
        # }
        endpoint_path = ""
        for endpoint in self.__collections:
            if endpoint["UUID"] == action_package["destination_collection_UUID"]:
                endpoint_path = endpoint["path"] 
                
        for item in action_package["items"]:
            source = ""
            if item["source"]["type"] == "posix absolute":
                source = item["source"]["path"]
            else:
                print("only posix absolute is currently supported")

            destination = endpoint_path + "/" + item["destination"]["path"]
            if isdir(destination):
                # Then name the file the same as the source file
                if isfile(source):
                    destination = destination + "/" + basename(source)

            print(f"Source is: {source}")
            print(f"Destination is: {destination}")
            shutil.copyfile(source, destination)
        

    def __runTransferSanityCheck(self, action_package: dict) -> bool:
        # Any agent with the globus plugin can submit a job to globus if it
        # has access to the globus cloud
        if not self.__access_to_globus_cloud:
            return False

        if "source_collection_UUID" not in action_package:
            return False
        if "destination_collection_UUID" not in action_package:
            return False

        if "items" not in action_package:
            return False
        else:
            for item in action_package["items"]:
                if "source" not in item:
                    return False
                else:
                    if "type" not in item["source"]:
                        return False
                    else:
                        # Only "globus relative" path type supported
                        if "globus relative" != item["source"]["type"]:
                            return False

                    if "path" not in item["source"]:
                        return False

                if "destination" not in item:
                    return False
                else:
                    if "type" not in item["destination"]:
                        return False
                    else:
                        # Only "globus relative" path type supported
                        if "globus relative" != item["destination"]["type"]:
                            return False

                    if "path" not in item["destination"]:
                        return False
        return True

    def __runMoveToGlobusSanityCheck(self, action_package: dict) -> bool:
        supported_source_path_types = ["posix absolute", "posix user home"]
        supported_destination_path_types = ["globus relative"]

        # This is needed in case there is more than a single collection on
        # the machine
        if not validUUID(action_package["destination_collection_UUID"]):
            return False

        # This is needed so the correct orchestrator picks executes the task
        # a bit redundant though becuase the globus collection UUID should
        # be unique
        if self.__hostname != action_package["source_host_name"]:
            return False

        for item in action_package["items"]:
            if "source" not in item:
                return False

            if "type" not in item["source"]:
                return False
            else:
                if (
                    item["source"]["type"]
                    not in supported_source_path_types
                ):
                    return False
            # Check if the item path is valid for the file
            if "path" not in item["source"]:
                return False
            if item["source"]["type"] == "posix absolute":
                if not exists(item["source"]["path"]):
                    return False
                
            if "destination" not in item:
                return False

            # Check if the item path is valid for the file
            if "type" not in item["destination"]:
                return False
            else:
                if (
                    item["destination"]["type"]
                    not in supported_destination_path_types
                ):
                    return False

            if "path" not in item["destination"]:
                return False
            if item["source"]["type"] == "posix absolute":
                if not exists(item["destination"]["path"]):
                    return False

        return True

    def __runMoveFromGlobusSanityCheck(self, action_package: dict) -> bool:
        # action_package = {
        #    "source_host_name": "",
        #    "destination_collection_UUID": "",
        #    "items": [
        #        {
        #            "source": {
        #                "type": "globus relative",
        #                "path": "dest/file1.txt"
        #                },
        #            "destination": {
        #                "type": "posix user home",
        #                "path": "/file1.txt"
        #                }
        #        },
        #        {
        #            "source": {
        #                "type": "globus relative",
        #                "path": "dest/file2.txt"
        #                },
        #            "destination": {
        #                "type": "posix user home",
        #                "path": "/file2.txt"
        #                }
        #        }
        #    ]
        # }

        supported_source_path_types = ["globus relative"]
        supported_destination_path_types = [
            "posix absolute",
            "posix user home",
        ]
        if not validUUID(action_package["source_collection_UUID"]):
            return False

        # Check that the UUID is associated with this machine
        if (
            not action_package["source_collection_UUID"]
            in self.__collections
        ):
            return False

        if self.__hostname != action_package["destination_host_name"]:
            return False

        for item in action_package["items"]:
            if "source" not in item:
                return False
            # Check if the item path is valid for the file
            if "type" not in item["source"]:
                return False
            else:
                if (
                    item["source"]["type"]
                    not in supported_source_path_types
                ):
                    return False

            if item["source"]["type"] == "posix absolute":
                if "path" not in item["source"]:
                    return False

            if "destination" not in item:
                return False
            # Check if the item path is valid for the file
            if "type" not in item["destination"]:
                return False
            else:
                if (
                    item["destination"]["type"]
                    not in supported_destination_path_types
                ):
                    return False

            if "path" not in item["destination"]:
                return False
            
        return True

###################################################################################
# Public Methods
###################################################################################
    def configure(self, config: dict):
        # When configuring should provide the endpoint id(s) located on
        # the same machine where the Zambeze agent is running along with
        # their paths on the posix system
        #
        # One should NOT define collecitons that are not local to where the python
        # script are running. The colletions posix endpoint must be viewable from
        # the point of view of this script.
        #
        # config = {
        #   "collections": [
        #       { "UUID": "", "path": ""},
        #       { "UUID": "", "path": ""}
        #   ],
        #   "authentication flow": {
        #       "type": "'native' or 'client credential'"
        #       "secret": "blahblah"
        #   },
        #   "client id": "UUID"
        # }
        #
        self.__validConfig(config)

        if "client id" in config:
            self.__client_id = config["client id"]

        # Detect hostname
        self.__hostname = gethostname()
        if externalNetworkConnectionDetected() is False:
            print("Unable to connect to external network access to globus cloud denied")
            self.__access_to_globus_cloud = False
            return

        try:
            if self.__flow == "native":
                self.__nativeAuthFlow()
            elif self.__flow == "client credential":
                print("Client credential authorization")
                self.__clientCredentialAuthFlow(config)

            self.__access_to_globus_cloud = True
        except GlobusError:
            logging.exception(
                "Error detected while attempting to authenticate and"
                "communicate with the Globus API"
            )

        self.__validEndPoint(config)
        if "collections" in config:
            self.__collections = deepcopy(config["collections"])
        
        # self.__collections must be defined before __validActions is called
        self.__validActions()
        self.__configured = True

    @property
    def supportedActions(self) -> list[str]:
        supported = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
                supported.append(action)
        return supported

    @property
    def help(self) -> str:
        message = (
            "Plugin globus when configured takes the following options\n"
            "'collections': [\n"
            "       { 'UUID': '', 'path': ''},\n"
            "       { 'UUID': '', 'path': ''}\n"
            "   ],\n"
            "   'authentication flow': {\n"
            "       'type': 'native or client credential',\n"
            "       'client id': '',\n"
            "       'secret': ''\n"
            " }\n"
        )
        return message

    @property
    def name(self) -> str:
        return self.__name

    @property
    def configured(self) -> bool:
        return self.__configured

    @property
    def info(self) -> dict:
        information = {}
        information["globus_app_id"] = self.__client_id
        information["collections"] = self.__collections

        supported_actions = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
                supported_actions.append(action)

        information["actions"] = supported_actions
        information["authentication flow type"] = self.__flow
        information["hostname"] = self.__hostname
        information["configured"] = self.__configured
        return information

    def check(self, package: list[dict]) -> dict:
        """Cycle through the items in the package and checks if this instance
        can execute them. This method should be called before process with
        the same package.

        arguments = [
          { "transfer": {
                  "source_collection_UUID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                  "destination_collection_UUID": "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
                  "items": [
                        {
                            "source": {
                                "type": "globus relative",
                                "path": "/file1.txt"
                                },
                            "destination": {
                                "type": globus relative",
                                "path": "dest/file1.txt"
                                }
                        },
                        {
                            "source": {
                                "type": "globus relative",
                                "path": "/file2.txt"
                                },
                            "destination": {
                                "type": "globus relative",
                                "path": "dest/file2.txt"
                                }
                        }
                  ]
              }
            }
        ]


        """
        checks = {}
        # Here we are cycling a list of dicts
        for index in range(len(package)):
            print(f"Index is {index}")
            print(f"Package length is {len(package)}")
            for action in package[index]:

                # Check if the action is supported
                if self.__supported_actions[action] is False:
                    checks[action] = False
                    continue

                if action == "transfers":
                    # Any agent with the globus plugin can submit a job to globus if it
                    # has access to the globus cloud
                    checks[action] = self.__runTransferSanityCheck(
                            package[index][action])

                elif action == "move_to_globus_collection":
                    checks[action] = self.__runMoveToGlobusSanityCheck(
                            package[index][action])
                
                elif action == "move_from_globus_collection":
                    checks[action] = self.__runMoveFromGlobusSanityCheck(
                            package[index][action])
        return checks

    def process(self, arguments: list[dict]) -> dict:

        if not self.__configured:
            raise Exception("Cannot run globus plugin, must first be configured.")

        print("Running Globus plugin")
        # Specify the path of the file as it appears in the Globus Collection
        # Specify the source collection UUID
        # Specify the path of the file as it appears in the final Globus Collection
        # specify the destination collection UUID
        #
        # Example 1
        #
        # arguments = [
        #   "transfer": 
        #       {
        #           "source_collection_UUID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        #           "destination_collection_UUID": "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
        #           "items": [
        #                 {
        #                     "source": {
        #                           "type": "globus relative",
        #                           "path": "/file1.txt"
        #                           },
        #                     "destination": {
        #                           "type": globus relative",
        #                           "path": "dest/file1.txt"
        #                           }
        #                 },
        #                 {
        #                     "source": {
        #                           "type": "globus relative",
        #                           "path": "/file2.txt"
        #                           },
        #                     "destination": {
        #                           "type": "globus relative",
        #                           "path": "dest/file2.txt"
        #                           }
        #                 }
        #           ]
        #       }
        #   }
        # ]
        #
        # Example 2
        #
        # arguments = [
        #   "move_to_globus_collection": {
        #       "source_host_name": "",
        #       "destination_collection_UUID": "",
        #       "items": [
        #           {
        #               "source": {
        #                   "type": "posix user home",
        #                   "path": "/file1.txt"
        #                   },
        #               "destination": {
        #                   "type": "globus relative",
        #                   "path": "dest/file1.txt"
        #                   }
        #           },
        #           {
        #               "source": {
        #                   "type": "posix absolute",
        #                   "path": "/home/cades/file2.txt"
        #                   },
        #               "destination": {
        #                   "type": "globus relative",
        #                   "path": "dest/file2.txt"
        #                   }
        #           }
        #       ]
        #   }
        # ]
        #
        # Example 3
        #
        # arguments = [
        #   "move_from_globus_collection": {
        #       "source_host_name": "",
        #       "destination_collection_UUID": "",
        #       "items": [
        #           {
        #               "source": {
        #                   "type": "globus relative",
        #                   "path": "dest/file1.txt"
        #                   },
        #               "destination": {
        #                   "type": "posix user home",
        #                   "path": "/file1.txt"
        #                   }
        #           },
        #           {
        #               "source": {
        #                   "type": "globus relative",
        #                   "path": "dest/file2.txt"
        #                   },
        #               "destination": {
        #                   "type": "posix user home",
        #                   "path": "/file2.txt"
        #                   }
        #           }
        #       ]
        #   }
        # ]

        for action_obj in arguments:
            # Make sure that the action is supported
            print("keys are")
            #print(action_obj[0])

            for key in action_obj:
                print(key)

                if key not in self.__supported_actions:
                    raise Exception(f"{key} is not supported.")

                if key == "transfer":
                    self.__runTransfer(action_obj[key])
                elif key == "move_to_globus_collection":
                    self.__runMoveToGlobusCollection(action_obj[key])
                elif key == "move_from_globus_collection":
                    self.__runMoveFromGlobusCollection(action_obj[key])

        return {}
