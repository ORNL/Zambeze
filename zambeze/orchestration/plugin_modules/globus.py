# Local imports
from .plugin import Plugin
from ..identity import validUUID
from ..network import  externalNetworkConnectionDetected

# Third party imports
from globus_sdk import GlobusError
import globus_sdk

# Standard imports
from copy import deepcopy
from os.path import exists
from socket import gethostname
import logging

class Globus(Plugin):

    def __init__(self):
        # Client id is specific to Zambeze project it was created by registering
        # at developers.globus.org
        self.__access_to_globus_cloud = False
        # This is the default for Zambeze
        self.__client_id = "435d07fa-8b10-4e04-b005-054c68be3f14"
        self.__collections = {}
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
    # ------------------

    def __validConfig(self, config: dict):
        """Purpose of this method is to determine if the coniguration is correct"""

        print(config)
        # Check that the authentication flow is supported
        if "native" == config["authentication flow"]["type"]:
            self.__flow = "native"
        elif "client credential" == config["authentication flow"]["type"]:
            self.__flow = "client credential"
        else: 
            raise Exception(f"authentication flow chosen {config['authentication flow']['type']}")

        # Check that the UUIDs are correct
        if "collections" in config:
            for local_collection in config["collections"]:
                print(local_collection)
                if not validUUID(local_collection["UUID"]):
                    raise Exception("Invalid UUID detected in plugin.")
                if not exists(local_collection["path"]):
                    # Check that the collection path is correct and exists on the local
                    # POSIX filesystem
                    raise Exception(f"Invalid path detected in plugin: {local_collection['path']}")



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
                        #data = e.raw_json
                        raise Exception("Invalid collection id. Collection is unknown.")
                    else:
                        raise


    def __validActions(self):
        # If we were able to communicate with Globus then the transfer action should be possible
        if self.__access_to_globus_cloud:
            self.__supported_actions["transfer"] = True
        # If we have no errors at this point then and there is at least one collection then 
        # we can move to and from them
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

        globus_auth_data = token_response.by_resource_server["auth.globus.org"]
        globus_transfer_data = token_response.by_resource_server["transfer.api.globus.org"]

        # most specifically, you want these tokens as strings
        AUTH_TOKEN = globus_auth_data["access_token"]
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
        confidential_client = globus_sdk.ConfidentialAppAuthClient(
            client_id=self.__client_id, client_secret=config["authentication flow"]["secret"]
        )
        scopes = "urn:globus:auth:scope:transfer.api.globus.org:all"
        self.__authorizer = globus_sdk.ClientCredentialsAuthorizer(confidential_client, scopes)
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
        #         {"source": "/file1.txt","destination": "dest/file1.txt"},
        #         {"source": "/file2.txt","destination": "dest/file2.txt"},
        #     ]
        # }
        tdata = globus_sdk.TransferData(
            self.__tc, 
            transfer["source_collection_UUID"],
            transfer["destination_collection_UUID"],
            label="Zambeze Workflow",
            sync_level="checksum")

        for item in items:
            tdata.add_item(
                item["source"],
                item["destination"])
        
        transfer_result = tc.submit_transfer(tdata)


    def __runMoveToGlobusCollection(self, move: dict):
        """Method is designed to move a local file to a Globus collection"""
        # move dict must have the following format
        # {
        #     "source_host_name": "",
        #     "destination_collection_UUID": ""
        #     "items": [
        #         {"source": "/file1.txt","destination": "dest/file1.txt"},
        #         {"source": "/file2.txt","destination": "dest/file2.txt"},
        #         ]
        # }
        # All checks should have already been done at this point with the check method

    ###################################################################################
    # Public Methods
    ###################################################################################
    def configure(self, config: dict):
        # When configuring should provide the endpoint id(s) located on 
        # the same machine where the Zambeze agent is running along with
        # their paths on the posix system
        #
        # config = {
        #   "collections": [
        #       { "UUID": "", "path": ""},
        #       { "UUID": "", "path": ""}
        #   ],
        #   "authentication flow": {
        #       "type": "'native' or 'client credential'"
        #       "secret": ""
        # }
        #
        print(config)
        self.__validConfig(config)

        if "client id" in config:
            self.__client_id = config["client id"]

        # Detect hostname
        self.__hostname = gethostname()
        if externalNetworkConnectionDetected() == False:
            self.__access_to_globus_cloud = False
            return

        try:
            if self.__flow == "native":
                self.__nativeAuthFlow()            
            elif self.__flow == "client credential":
                self.__clientCredentialAuthFlow(config)    

            self.__access_to_globus_cloud = True
        except GlobusError:
            logging.exeception("Error detected while attempting to authenticate and"
            "communicate with the Globus API")             

        self.__validEndPoint(config)
        self.__validActions()
        if "collections" in config:
            self.__collections = deepcopy(config["collections"])
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
        message = ("Plugin globus when configured takes the following options\n"
        "'collections': [\n"
        "       { 'UUID': '', 'path': ''},\n"
        "       { 'UUID': '', 'path': ''}\n"
        "   ],\n"
        "   'authentication flow': {\n"
        "       'type': 'native or client credential',\n"
        "       'client id': '',\n"
        "       'secret': ''\n"
        " }\n")
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
        the same package."""
        checks = {}
        # Here we are cycling a list of dicts
        for index in range(len(package)):
            for action in package[index]:

                # Check if the action is supported
                if self.__supported_actions[action] == False:
                    checks[action] = False
                    continue

                if action == "transfers":
                    # Any agent with the globus plugin can submit a job to globus if it has
                    # access to the globus cloud
                    checks[action] = True
                    if not self.__access_to_globus_cloud:
                        checks[action] = False
                        continue

                elif action == "move_to_globus_collection":
                    action_package = package[index][action]
                    checks[action] = True
                    if not validUUID(action_package["destination_collection_UUID"]):
                        checks[action] = False
                        continue

                    if self.__hostname != action_package["source_host_name"]:
                        checks[action] = False
                        continue

                    for item in action_package["items"]:
                        if not exists(item["source"]):
                            # Check if the item path is valid for the file
                            checks[action] = False
                            break
                        if not exists(item["destination"]):
                            # Check if the item path is valid for the file
                            checks["action"] = False
                            break

                elif action == "move_from_globus_collection":
                    action_package = package[index][action]
                    checks[action] = True
                    if not validUUID(action_package["source_collection_UUID"]):
                        checks[action] = False
                        continue

                    # Check that the UUID is associated with this machine
                    if not action_package["source_collection_UUID"] in self.__collections:
                        checks[action] = False
                        continue

                    if self.__hostname != action_package["destination_host_name"]:
                        checks[action] = False
                        continue

                    for item in action_package["items"]:
                        if not exists(item["source"]):
                            # Check if the item path is valid for the file
                            checks["action"] = False
                            break
                        if not exists(item["destination"]):
                            # Check if the item path is valid for the file
                            checks["action"] = False
                            break
        return checks

    def process(self, arguments: list[dict]):

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
        # arguments = {
        #   "transfer": [
        #       {
        #           "source_collection_UUID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        #           "destination_collection_UUID": "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
        #           "items": [
        #               {"source": "/file1.txt","destination": "dest/file1.txt"},
        #               {"source": "/file2.txt","destination": "dest/file2.txt"},
        #           ]
        #       }
        #   ]
        # }
        # 
        # Example 2
        #
        # arguments = {
        #   "move_to_globus_collection": {
        #       "source_host_name": "",
        #       "destination_collection_UUID": "",
        #       "items": [
        #           {"source": "/file1.txt","destination": "dest/file1.txt"},
        #           {"source": "/file2.txt","destination": "dest/file2.txt"},
        #       ]
        #   }
        # }
        #
        # Example 3
        #
        # arguments = {
        #   "move_from_globus_collection": {
        #       "source_host_name": "",
        #       "destination_collection_UUID": "",
        #       "items": [
        #           {"source": "/file1.txt","destination": "dest/file1.txt"},
        #           {"source": "/file2.txt","destination": "dest/file2.txt"},
        #       ]
        #   }
        # }

        for action in arguments:
            # Make sure that the action is supported
            if not self.__supported_actions[action]:
                raise Exception(f"{action} is not supported.")
                
            if action == "transfer":
                self.__runTransfer(arguments[action])
            elif action == "move_to_globus_collection":
                self.__runMoveToGlobusCollection(arguments[action])
            elif action == "move_from_globus_collection":
                self.__runMoveFromGlobusCollection(arguments[action])

