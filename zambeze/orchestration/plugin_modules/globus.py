# Local imports
from .abstract_plugin import Plugin
from ..identity import validUUID
from ..network import externalNetworkConnectionDetected

# Third party imports
from globus_sdk import GlobusError
import globus_sdk

# Standard imports
from copy import deepcopy
import os
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import isdir
from os.path import isfile
from socket import gethostname
from typing import Optional

import logging
import pickle
import re
import shutil

def localEndpointExists(globus_uuid: str, endpoint_list: list[dict]) -> str:
    for item in endpoint_list:
      print(f"Comparing items {item['uuid'].lower()} with {globus_uuid.lower()}")
      if item["uuid"].lower() == globus_uuid.lower():
        return True
    return False


def globusURISeparator(uri: str, default_uuid) -> dict:
    """Will take a globus URI and break it into its components

    :Example:

    >>> default_uri = "YYYYZZZZ-YYYY-ZZZZ-YYYY-ZZZZYYYYZZZZ"
    >>> globus_uri = globus://XXXXYYYY-XXXX-XXXX-XXXX-XXXXYYYYXXXX/path/file.txt
    >>> uri_components = globusURISeparator(globus_uri, default_uri)
    >>> print( uri_components.UUID )
    >>> print( uri_components.path )
    >>> print( uri_components.file_name )
    >>> print( uri_components.error_msg )

    The output should be

    >>> XXXXYYYY-XXXX-XXXX-XXXX-XXXXYYYYXXXX
    >>> /path/
    >>> file.txt

    :Example: When no endpoint UUID is provided in the URI the default should be used

    >>> default_uri = "YYYYZZZZ-YYYY-ZZZZ-YYYY-ZZZZYYYYZZZZ"
    >>> globus_uri = globus://path/file.txt
    >>> uri_components = globusURISeparator(globus_uri, default_uri)
    >>> print( uri_components.UUID )
    >>> print( uri_components.path )
    >>> print( uri_components.file_name )
    >>> print( uri_components.error_msg )

    The output should be

    >>> YYYYZZZZ-YYYY-ZZZZ-YYYY-ZZZZYYYYZZZZ
    >>> /path/
    >>> file.txt
    """
    uri = uri.lstrip(' ').rstrip(' ') 

    globus_uri_tag = "globus://"
    # Start by ensuring the start of the uri begins with globus://
    if not uri.startswith(globus_uri_tag):
        error_msg = f"Incompatible Globus URI format {uri} must start with "
        error_msg = error_msg + "globus://"
        return ("", "", "", error_msg)

    UUID_and_path = uri[len(globus_uri_tag):]
    # Replace multiple occurances of // with single /
    UUID_and_path = re.sub(os.sep + '{2,}', os.sep, UUID_and_path) 

    UUID = UUID_and_path[0:36]

    file_and_path = UUID_and_path
    valid_uuid = default_uuid
    # Check if the first 36 chars contains os.sep it is probably a file_path 
    # in which case the default uuid should be provided
    if not os.sep in UUID:
        if not validUUID(UUID):
            error_msg = f"Incompatible Globus URI format {uri} must contain 36 "
            error_msg = error_msg + "character valid UUID of the form "
            error_msg = error_msg + "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
            error_msg = error_msg + f" the provided UUID is {UUID} it must also"
            error_msg = error_msg + " conform to RFC4122"
            return ("", "", "", error_msg)
        valid_uuid = UUID
        file_and_path = UUID_and_path[36:]

    path = dirname(file_and_path)

    if not path.startswith(os.sep):
        path = os.sep + path

    if not path.endswith(os.sep):
        path = path + os.sep

    print("Contents of globusURISeparator")
    print(valid_uuid)
    print(path)
    print(basename(file_and_path))
    return (valid_uuid, path, basename(file_and_path), "")

def fileURISeparator(uri: str) -> dict:
    """Will take a file URI and break it into its components

    :Example:

    >>> file_uri = file://path/file.txt
    >>> uri_components = fileURISeparator(file_uri)
    >>> print( uri_components.path )
    >>> print( uri_components.file_name )
    >>> print( uri_components.error_msg )

    The output should be

    >>> /path/
    >>> file.txt
    """
    uri = uri.lstrip(' ').rstrip(' ') 

    file_uri_tag = "file://"
    # Start by ensuring the start of the uri begins with globus://
    if not uri.startswith(file_uri_tag):
        error_msg = f"Incompatible file URI format {uri} must start with "
        error_msg = error_msg + "file://"
        return ("", "", "", error_msg)

    file_and_path = uri[len(file_uri_tag):]
    path = dirname(file_and_path)

    if not path.startswith(os.sep):
        path = os.sep + path

    if not path.endswith(os.sep):
        path = path + os.sep

    return (path, basename(file_and_path), "")


def checkTransferEndpoint(action_package: dict) -> (bool, str):
    """Makes sure each item to be transferred has the correct format

    :Example:

    >>> "items": [
    >>>     {
    >>>          "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1/txt"
    >>>          "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file1/txt"
    >>>     },
    >>>     {
    >>>          "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2/txt"
    >>>          "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file2/txt"
    >>>     }
    >>> ]

    """
    for item in action_package["items"]:
        if "source" not in item:
            return False, "'source' missing from 'items' in 'transfer'"
        else:
            valid, msg = checkEndpoint(item["source"], ["globus"])
            if not valid:
                return (False, "Error in source\n" + msg)

        if "destination" not in item:
            return False, "'destination' missing from 'items' in 'transfer'"
        else:
            valid, msg = checkEndpoint(item["destination"], ["globus"])
            if not valid:
                return (False, "Error in destination\n" + msg)
    return True, ""


def getMappedCollections(config: dict) -> list[str]:
    """Returns a list of the UUIDs that are mapped collections

    :Example:

    >>> config = {
    >>>     "local_endpoints": [
    >>>         { "UUID": "XXXX...XXXX", "path": "/here/file", "type": "guest"},
    >>>         { "UUID": "YYYY...YYYY", "path": "/there/file2", "type": "mapped"}
    >>>     ]
    >>> }
    >>> mapped_coll = getMappedCollections(config)
    >>> print(mapped_coll)
    >>> # Single entry would be printed in this case
    >>> # ["YYYY...YYYY"]
    """
    mapped_collections = []
    if "local_endpoints" in config:
        for local_endpoint in config["local_endpoints"]:
            if local_endpoint["type"] == "mapped":
                mapped_collections.append(local_endpoint["uuid"])

    return mapped_collections


def is_36char(item: str):
    return len(item) == 36


def getGlobusScopes(mapped_collections: list[str]) -> str:
    """Get the globus scopes needed to access the mapped collections

    :param mapped_collections: This should contain the UUIDs of only mapped
        collections
    :type mapped_collections: list[str]

    For globus mapped collections, explicit scope has to be requested to
    access the collection.

    :Example: First example empty mapped collection list

    >>> mapped_coll = [""]
    >>> scopes = getGlobusScopes(mapped_coll)
    >>> print(scopes)
    >>> # Will print general scopes
    >>> # urn:globus:auth:scope:transfer.api.globus.org:all

    :Example: Second example

    >>> mapped_coll = ["XXXX...XXXX", "YYYY...YYYY"]
    >>> scopes = getGlobusScopes(mapped_coll)
    >>> print(scopes)
    >>> # Will print general scopes
    >>> # urn:globus:auth:scope:transfer.api.globus.org:all[*https://auth.globus.org/scopes/XXXX...XXXX/data_access *https://auth.globus.org/scopes/YYYY...YYYY/data_access] # noqa: E501
    """
    # Clean the UUIDs in the list make sure they are all 36 characters
    mapped_collections = list(filter(is_36char, mapped_collections))

    scopes = "urn:globus:auth:scope:transfer.api.globus.org:all"
    if len(mapped_collections):
        scopes = scopes + "["
        index = 1
        for mapped_collection in mapped_collections:
            scopes = (
                scopes
                + f"*https://auth.globus.org/scopes/{mapped_collection}/data_access"
            )
            if index < len(mapped_collections):
                scopes = scopes + " "
                index = index + 1
        scopes = scopes + "]"
    return scopes


def checkEndpoint(item: str, supported_types: list[str]) -> (bool, str):
    """Check that the approprite keys and values exist in the endpoint

    :param item: uri
    :type item: str
    :param supported_types: Supported types, defines what values are allowed
    :type supported_types: list[str]
    :rtype: bool

    This function will return False if the item provided is an inappropriate value. 
        * type - only two types are currently supported
        ["globus", "file"]

    :Example:

    >>> item = "globus:://XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
    >>> valid, msg = checkEndpoint(item)
    >>> assert valid
    """
    # Only "globus relative" path type supported
    for supported_type in supported_types:
        if item.startswith(supported_type + "://" ):
            return True, ""
            
    return (
        False,
        f"Missing {item} not in supported types \
                {supported_types} uri should start with i.e. globus://"
    )
    
def checkAllItemsHaveValidEndpoints(
    items: list[dict],
    supported_source_path_types: list[str],
    supported_destination_path_types: list[str],
) -> (bool, str):
    """Check that all items that are too be moved are schematically correct

    :return: Returns true if the schema of the items is valid and false otherwise
    :rtype: bool

    :Example: Input

    Provided a list of items to be moved

    >>> "items": [
    >>>       {
    >>>           "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
    >>>           "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file1.txt"
    >>>       },
    >>>       {
    >>>           "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt",
    >>>           "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file2.txt"
    >>>       }
    >>> ]

    "Example: Input 2

    >>> "items": [
    >>>     {
    >>>         "source": "file://file1.txt",
    >>>         "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file1.txt"
    >>>     },
    >>>     {
    >>>         "source": "file://file2.txt",
    >>>         "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file2.txt"
    >>>     }
    >>> ]


    >>> supported_source_path_types = ["file"]
    >>> supported_destination_path_types = ["globus"]
    >>> assert checkAllItemsHaveValidEndpoints(
    >>>     items,
    >>>     supported_source_path_types,
    >>>     supported_destination_path_types)
    """
    for item in items:
        if "source" not in item:
            return False, "Item is missing source key"
        if "destination" not in item:
            return False, "Item is missing destination key"

        valid, msg = checkEndpoint(item["source"], supported_source_path_types)
        if not valid:
            return False, "Invalid source\n" + msg

        valid, msg = checkEndpoint(
            item["destination"], supported_destination_path_types
        )
        if not valid:
            return False, "Invalid destination\n" + msg

    return True, ""


class Globus(Plugin):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.__name = "globus"
        super().__init__(self.__name, logger=logger)
        # Client id is specific to Zambeze project it was created by registering
        # at developers.globus.org
        self.__access_to_globus_cloud = False
        # This is the default for Zambeze
        self.__client_id = "435d07fa-8b10-4e04-b005-054c68be3f14"
        self.__endpoints = []
        self.__configured = False
        self.__flow = "client credential"
        self.__hostname = None
        self.__default_endpoint = None
        self.__supported_actions = {
            "transfer": False,
            "move_to_globus_collection": False,
            "move_from_globus_collection": False,
            "get_task_status": False,
        }
        pass

    ###################################################################################
    # Private Methods
    ###################################################################################
    # Validation Methods
    # -----------------

    def __validConfig(self, config: dict):
        """Purpose of this method is to determine if the coniguration is correct

        :Example: Config

        >>> config = {
        >>>   "local_endpoints": [
        >>>       { "uuid": "4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5", "path": "/scratch/", "type": "guest"},
        >>>       { "uuid": "JD3D597A-2D2B-1MP8-A53F-0Z89A04C68A5", "path": "/project/", "type": "mapped"}
        >>>   ],
        >>>   "authentication_flow": {
        >>>       "type": "'native' or 'client credential'"
        >>>       "secret": "blahblah"
        >>>   },
        >>>   "default_endpoint": "4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5"
        >>>   "client_id": "9c9fee8f-f686-4e28-a961-647af41fe021"
        >>> }
        """

        if "authentication_flow" not in config:
            raise Exception(
                "'authentication_flow' key value missing from config"
                " config must have 'authentication_flow' specified"
            )

        # Check that the authentication flow is supported
        if "native" == config["authentication_flow"]["type"].lower():
            self.__flow = "native"
        elif "client credential" == config["authentication_flow"]["type"].lower():
            self.__flow = "client credential"
        else:
            raise Exception(
                "Unsupported authentication flow detected "
                f"{config['authentication_flow']['type']}"
            )


        # Check that the UUIDs are correct
        if "local_endpoints" in config:
            for local_endpoint in config["local_endpoints"]:
                if not validUUID(local_endpoint["uuid"]):
                    raise Exception(f"Invalid uuid detected in plugin: {local_endpoint['uuid']}")
                if not exists(local_endpoint["path"]):
                    # Check that the collection path is correct and exists on the local
                    # POSIX filesystem
                    raise Exception(
                        f"Invalid path detected in plugin: {local_endpoint['path']}"
                    )

            if "default_endpoint" not in config:
                raise Exception(
                    "'default_endpoint' key value missing from config"
                    " config must have 'default_endpoint' specified if local_endpoints are configured."
                )

            if not validUUID(config["default_endpoint"]):
                raise Exception(f"Invalid uuid detected in plugin for default endpoint: {config['default_endpoint']}")

            
            # Make sure that default_endpoint is one of the endpoints that has been configured

            if not localEndpointExists(config["default_endpoint"], config["local_endpoints"]):
                error_msg = f"Invalid default endpoint {config['default_endpoint']}"
                error_msg = error_msg + " not one of the 'local_endpoints'"
                error_msg = error_msg + " check your "
                error_msg = error_msg + " agent.yaml file. Local endpoints are:"
                error_msg = error_msg + f"\n{config['local_endpoints']}"
                raise Exception(error_msg)

    def __validEndPoints(self, config: dict):
        """This method can only be run after the authentication flow has been run"""

        # Check that the endpoints actually exist in Globus and are not just made up
        if "local_endpoints" in config:
            for local_collection in config["local_endpoints"]:
                # Check that the collection id is recognized by Globus and is a
                # valid globus collection UUID
                try:
                    self.__tc.get_endpoint(local_collection["uuid"])
                except globus_sdk.GlobusAPIError as e:
                    if e.http_status == 404:
                        # data = e.raw_json
                        uid = local_collection["uuid"]
                        raise Exception(f"Invalid collection id {uid}. Collection is unknown.")
                    else:
                        raise


    def __validActions(self):
        # If we were able to communicate with Globus then the transfer action should be
        # possible
        if self.__access_to_globus_cloud:
            self.__supported_actions["transfer"] = True
            self.__supported_actions["get_task_status"] = True
        # If we have no errors at this point then and there is at least one collection
        # then we can move to and from them
        if len(self.__endpoints):
            self.__supported_actions["move_to_globus_collection"] = True
            self.__supported_actions["move_from_globus_collection"] = True

    # Authentication methods
    # ----------------------
    def __nativeAuthFlow(self):
        # Using Native auth flow

        home_dir = os.path.expanduser('~')
        if not exists(home_dir + "/.zambeze"):
            os.mkdir( home_dir + "/.zambeze" )

        token_file = home_dir + "/.zambeze/globus.tokens"
        if exists(token_file):
            infile = open(token_file, 'rb')
            self.__authorizer = pickle.load(infile)
            infile.close()
        else:
            client = globus_sdk.NativeAppAuthClient(self.__client_id)
           
            client.oauth2_start_flow(requested_scopes=self.__scopes, refresh_tokens=True)
            authorize_url = client.oauth2_get_authorize_url()
            print(f"Please go to this URL and login:\n\n{authorize_url}\n")

            auth_code = input("Please enter the code you get after login here: ").strip()
            token_response = client.oauth2_exchange_code_for_tokens(auth_code)
   
            # {
            #   "transfer.api.globus.org": {
            #     "scope": "urn:globus:auth:scope:transfer.api.globus.org:all",
            #     "access_token": "Agb3BPYkMlePplDMnKPeO6Vobb2nzXKamzjkblVynnjg0z782zT5C47bv56Dm0G9v5lBqrBxW2J9m1HkY6vErc2wJgY",
            #     "refresh_token": "Agr6m6D4geqKv03YQzKPNxjOqK8Ob79aPEwrzmyGBly8xKY1yMs3Uow1E4VozBYxprxvp5OxOp2dozW79Gr8rpgraEeVg",
            #     "token_type": "Bearer",
            #     "expires_at_seconds": 1661652891,
            #     "resource_server": "transfer.api.globus.org"
            #   }
            # }

            globus_transfer_data = token_response.by_resource_server[
                "transfer.api.globus.org"
            ]

            # most specifically, you want these tokens as strings
            transfer_rt = globus_transfer_data["refresh_token"]
            transfer_at = globus_transfer_data["access_token"]
            expires_at_s = globus_transfer_data["expires_at_seconds"]

            # construct a RefreshTokenAuthorizer
            # note that `client` is passed to it, to allow it to do the refreshes
            self.__authorizer = globus_sdk.RefreshTokenAuthorizer(
                transfer_rt, client, access_token=transfer_at, expires_at=expires_at_s
            )

            outfile = open(token_file,'wb')
            pickle.dump(self.__authorizer, outfile)
            outfile.close()

        # and try using `tc` to make TransferClient calls. Everything should just
        # work -- for days and days, months and months, even years
        self.__tc = globus_sdk.TransferClient(authorizer=self.__authorizer)



    def __clientCredentialAuthFlow(self, config: dict):
        # https://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials.html

        if config["authentication_flow"]["secret"] is None:
            raise Exception(
                "Cannot authenticate with Globus the client secret"
                " has not been defined and is None.\n"
                "The provided erronous config is:\n\n"
                f"{config}"
            )

        confidential_client = globus_sdk.ConfidentialAppAuthClient(
            client_id=self.__client_id,
            client_secret=config["authentication_flow"]["secret"],
        )
        self.__authorizer = globus_sdk.ClientCredentialsAuthorizer(
            confidential_client, self.__scopes
        )
        # create a new client
        self.__tc = globus_sdk.TransferClient(authorizer=self.__authorizer)

    # Run methods
    # -----------
    def __runTransfer(self, transfer: dict):
        """transfer dict must have the following format

        :Example:

        >>> {
        >>>     "type": "synchronous",
        >>>     "items": [
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
        >>>                     "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file1.txt"
        >>>                 },
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt",
        >>>                     "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file2.txt"
        >>>                 }
        >>>     ]
        >>> }

        If the type is asynchrouns a runTransfer will return a callback action
        that can be executed to check the status of the generated task
        """

        for item in transfer["items"]:
            print("Separating source item")
            source_globus_uri = globusURISeparator(item["source"], self.__default_endpoint)
            print(source_globus_uri)
            print("Separating destination item")
            dest_globus_uri = globusURISeparator(item["destination"], self.__default_endpoint)
            
            tdata = globus_sdk.TransferData(
                self.__tc,
                source_globus_uri[0],
                dest_globus_uri[0],
                label="Zambeze Workflow",
                sync_level="checksum",
            )

            source_file_path = source_globus_uri[1] + source_globus_uri[2]
            dest_file_path = dest_globus_uri[1] + dest_globus_uri[2]
            tdata.add_item(source_file_path, dest_file_path)

            print("Submitting packet to be transferred")
            print(tdata)
            transfer_result = {}
            if "synchronous" == transfer["type"].lower():
                transfer_result = self.__tc.submit_transfer(tdata)
                print("Transfer result")
                self._logger.info(transfer_result)
                print(transfer_result)
                task_id = transfer_result["task_id"]
                while not self.__tc.task_wait(task_id, timeout=60):
                    print("Another minute went by without {0} terminating".format(task_id))
            elif "asynchronous" == transfer["type"].lower():
                result = self.__tc.submit_transfer(tdata)
                self._logger.info(result)
                transfer_result = {
                    "callback": {"get_task_status": {"task_id": result["task_id"]}},
                    "result": {"status": result["code"], "message": result["message"]},
                }

        return transfer_result

    def __runGetTaskStatus(self, action_package: dict):
        """Method will check the status of a task

        :Example:

        >>> action_package = {
        >>>     "task_id": result["task_id"]
        >>> }
        """
        result = self.__tc.get_task(action_package["task_id"])
        get_status_result = {
            "callback": {"get_task_status": {"task_id": result["task_id"]}},
            "result": {"status": result["status"], "message": result["nice_status"]},
        }
        return get_status_result

    def __getPOSIXpathToEndpoint(self, globus_uuid: str) -> str:
        return next((endpoint["path"] for endpoint in self.__endpoints if endpoint["uuid"] == globus_uuid), None)


    def __runMoveToGlobusCollection(self, action_package: dict):
        """Method is designed to move a local file to a Globus collection

        Example:

        "action_package" dict must have the following format

        >>> action_package = {
        >>>     "items": [
        >>>           {
        >>>               "source": "file://file1.txt",
        >>>               "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file1.txt"
        >>>           },
        >>>           {
        >>>               "source": "file://file2.txt",
        >>>               "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file2.txt"
        >>>           }
        >>>     ]
        >>> }
        """
#        endpoint_path = ""
#        for endpoint in self.__endpoints:
#            if endpoint["UUID"] == action_package["destination_collection_UUID"]:
#                endpoint_path = endpoint["path"]
#
        for item in action_package["items"]:
            source_sep_file_uri = fileURISeparator(item["source"])
            source_path = source_sep_file_uri[0] + source_sep_file_uri[1]
            #source = ""

            #if item["source"]["type"].lower() == "file":
            #    source = item["source"]["path"]
            #else:
            #    print("only file is currently supported")
            destination_sep_globus_uri = globusURISeparator(item["destination"], self.__default_endpoint)

            destination_uuid = destination_sep_globus_uri[0]
            destination_file_name = destination_sep_globus_uri[2]
            destination_endpoint_path = self.__getPOSIXpathToEndpoint(destination_uuid)
                
            # /mnt/globus/collections
            destination_path = destination_endpoint_path

            # /mnt/globus/collections + /file_path/
            destination_path = destination_path + destination_sep_globus_uri[1]

            if isdir(destination_path):

                if len(destination_file_name) > 0:
                    # /mnt/globus/collections + /file_path/ + file.txt
                    destination_path = destination_path + destination_file_name 
                else:
                    # Then name the file the same as the source file
                    if isfile(source_path):
                        destination_path = destination_path + basename(source_path)

            shutil.copyfile(source_path, destination_path)


    def __runMoveFromGlobusCollection(self, action_package: dict):
        """Method is designed to move a local file from a Globus collection

        Example:

        "action_package" dict must have the following format

        >>> action_package = {
        >>>     "items": [
        >>>           {
        >>>               "source": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file2.txt"
        >>>               "destination": "file://file2.txt",
        >>>           }
        >>>     ]
        >>> }
        """
#        endpoint_path = ""
#        for endpoint in self.__endpoints:
#            if endpoint["UUID"] == action_package["destination_collection_UUID"]:
#                endpoint_path = endpoint["path"]
#
        for item in action_package["items"]:
            print("Called moving from Globus moving items")
            print("item is")
            print(item)
            destination_sep_file_uri = fileURISeparator(item["destination"])
            print(destination_sep_file_uri)
            destination_path = destination_sep_file_uri[0]
            destination_file_name = destination_sep_file_uri[1]

            #source = ""

            #if item["source"]["type"].lower() == "file":
            #    source = item["source"]["path"]
            #else:
            #    print("only file is currently supported")
            source_sep_globus_uri = globusURISeparator(item["source"], self.__default_endpoint)

            source_uuid = source_sep_globus_uri[0]
            source_file_name = source_sep_globus_uri[2]
            source_endpoint_path = self.__getPOSIXpathToEndpoint(source_uuid)
                
            # /mnt/globus/collections
            source_path = source_endpoint_path 

            # /mnt/globus/collections + /file_path/
            source_path = source_path + source_sep_globus_uri[1]

            # /mnt/globus/collections/file_path/file.txt
            source_path = source_path + source_file_name

            if isdir(destination_path):

                if len(destination_file_name) > 0:
                    # /mnt/globus/collections + /file_path/ + file.txt
                    destination_path = destination_path + destination_file_name 
                else:
                    # Then name the file the same as the source file
                    if isfile(source_path):
                        destination_path = destination_path + source_file_name

            shutil.copyfile(source_path, destination_path)


    def __runTransferSanityCheck(self, action_package: dict) -> (bool, str):
        """Checks to ensure that the action_package has the right format and
        checks for errors.

        :Example:

        >>> {
        >>>     "type": "synchronous",
        >>>     "items": [
        >>>         {
        >>>             "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
        >>>             "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file1.txt"
        >>>         },
        >>>         {
        >>>             "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt",
        >>>             "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file2.txt"
        >>>         }
        >>>     ]
        >>> }
        """

        # Any agent with the globus plugin can submit a job to globus if it
        # has access to the globus cloud
        if not self.__access_to_globus_cloud:
            return False, "No access to Globus Service to conduct 'transfer'."

        required_keys = [
            "type",
            "items",
        ]
        for required in required_keys:
            if required not in action_package:
                return False, f"{required} key missing from 'transfer' action."

        if action_package["type"] != "synchronous":
            if action_package["type"] != "asynchronous":
                return (
                    False,
                    "Unsupported 'type' detected. Supported types are \
            synchronous and asynchronous you have specified {action_package['type']}",
                )

        return checkTransferEndpoint(action_package)

    def __runMoveToGlobusSanityCheck(self, action_package: dict) -> (bool, str):
        supported_source_path_types = ["file"]
        supported_destination_path_types = ["globus"]


        valid, msg = checkAllItemsHaveValidEndpoints(
            action_package["items"],
            supported_source_path_types,
            supported_destination_path_types,
        )

        if valid:
            for item in action_package["items"]:
                globus_sep_uri = globusURISeparator(item["destination"], self.__default_endpoint)
                if not validUUID(globus_sep_uri[0]):
                    error_msg = f"Invalid uuid dectected in \
                                'move_from_globus_collection' item: {item} \nuuid: \
                                {globus_sep_uri[0]}"
                    return (False, error_msg)
                if not localEndpointExists(globus_sep_uri[0], self.__endpoints):
                    error_msg = f"Invalid source endpoint uuid dectected in \
                                'move_from_globus_collection' item: {item} \nuuid: \
                                {globus_sep_uri[0]}\nRecognized endpoints are {self.__endpoints}."
                    return (False, error_msg)

                file_sep_uri = fileURISeparator(item["source"])
                file_path = file_sep_uri[0] + file_sep_uri[1]
                if not exists(file_path):
                    return False, f"Item does not exist {file_path}"

        return (valid, msg)


    def __runGetTaskStatusSanityCheck(self, action_package: dict) -> (bool, str):
        """Checks that the get_task_status action is correctly configured

        :Example:

        >>> action_package = {
        >>>     "task_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
        >>> }
        """
        if "task_id" not in action_package:
            return (False, "Missing 'task_id' in get_task_status action")

        if not validUUID(action_package["task_id"]):
            return (
                False,
                f"Invalid 'task_id' detected in 'get_task_status': \
            {action_package['task_id']}",
            )
        return (True, "")

    def __runMoveFromGlobusSanityCheck(self, action_package: dict) -> (bool, str):
        """Run a sanity check for the action "move_from_globus_collection"

        return: Will return true if the sanity check passes false otherwise

        Example:

        >>> action_package = {
        >>>    "source_host_name": "",
        >>>    "destination_collection_UUID": "",
        >>>    "items": [
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt"
        >>>               "destination": "file://file2.txt",
        >>>           }
        >>>    ]
        >>> }
        >>> assert self.__runMoveFromGlobusSanityCheck(action_package)
        """

        supported_source_path_types = ["globus relative"]
        supported_destination_path_types = ["file"]

        valid, msg = checkAllItemsHaveValidEndpoints(
            action_package["items"],
            supported_source_path_types,
            supported_destination_path_types,
        )

        if valid:
            for item in action_package["items"]:
                globus_sep_uri = globusURISeparator(item["source"], self.__default_endpoint)
                if not validUUID(globus_sep_uri[0]):
                    error_msg = f"Invalid uuid dectected in \
                                'move_from_globus_collection' item: {item} \nuuid: \
                                {globus_sep_uri[0]}"
                    return (False, error_msg)
                if not localEndpointExists(globus_sep_uri[0], self.__endpoints):
                    error_msg = f"Invalid source endpoint uuid dectected in \
                                'move_from_globus_collection' item: {item} \nuuid: \
                                {globus_sep_uri[0]}\nRecognized endpoints are {self.__endpoints}."
                    return (False, error_msg)

                file_sep_uri = fileURISeparator(item["destination"])
                file_path = file_sep_uri[0] + file_sep_uri[1]
                if not exists(file_path):
                    return False, f"Item does not exist {file_path}"


        return (valid, msg)

    def __checkAccessToGlobusCloud(self):
        """Will check if we can reach the internet and caches access to globus
        cloud if cannot reach it.
        """
        if externalNetworkConnectionDetected() is False:
            print("Unable to connect to external network access to globus cloud denied")
            self.__access_to_globus_cloud = False
            return

    ###################################################################################
    # Public Methods
    ###################################################################################
    def configure(self, config: dict):
        """When configuring should provide the endpoint id(s) located on
        the same machine where the Zambeze agent is running along with
        their paths on the posix system

        One should NOT define collections that are not local to where the python
        script are running. The colletion's posix endpoints must be viewable from
        the point of view of this script.

        config = {
          "local_endpoints": [
              { "uuid": "4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5", "path": "/scratch/", "type": "guest"},
              { "uuid": "JD3D597A-2D2B-1MP8-A53F-0Z89A04C68A5", "path": "/project/", "type": "mapped"}
          ],
          "authentication_flow": {
              "type": "'native' or 'client credential'"
              "secret": "blahblah"
          },
          "default_endpoint": "4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5"
          "client_id": "9c9fee8f-f686-4e28-a961-647af41fe021"
        }
        """
        self.__validConfig(config)

        if "client_id" in config:
            self.__client_id = config["client_id"]

        # Detect hostname
        self.__hostname = gethostname()
        self.__checkAccessToGlobusCloud()

        # Permissions to access mapped collections must be granted explicitly
        mapped_collections = getMappedCollections(config)
        self.__scopes = getGlobusScopes(mapped_collections)

        try:
            if self.__flow == "native":
                self.__nativeAuthFlow()
            elif self.__flow == "client credential":
                self.__clientCredentialAuthFlow(config)

            self.__access_to_globus_cloud = True
        except GlobusError:
            logging.exception(
                "Error detected while attempting to authenticate and"
                "communicate with the Globus API"
            )

        self.__validEndPoints(config)
        if "local_endpoints" in config:
            self.__endpoints = deepcopy(config["local_endpoints"])
            self.__default_endpoint = deepcopy(config["default_endpoint"])

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
            "Plugin globus when configured takes the following options.\n"
            "This is what should appear in the zambeze yaml config file.\n"
            "\n"
            " local_endpoints:\n"
            "   - uuid: '4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5'\n"
            "     path: '/scratch/'\n"
            "     type: 'mapped'\n"
            "   - uuid: 'JD3D597A-2D2B-1MP8-A53F-0Z89A04C68A5'\n"
            "     path: '/project/'\n"
            "     type: 'guest'\n"
            " default_endpoint: '4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5'\n"
            " authentication_flow:\n"
            "   type: 'native'\n"
            "   secret: 'my_secret'\n"
            " client_id: '9c9fee8f-f686-4e28-a961-647af41fe02'\n"
        )
        return message

    @property
    def configured(self) -> bool:
        return self.__configured

    @property
    def info(self) -> dict:
        information = {}
        information["client_id"] = self.__client_id
        information["local_endpoints"] = self.__endpoints

        supported_actions = []
        for action in self.__supported_actions:
            if self.__supported_actions[action]:
                supported_actions.append(action)

        
        information["default_endpoint"] = self.__default_endpoint
        information["actions"] = supported_actions
        information["authentication_flow"] = self.__flow
        information["hostname"] = self.__hostname
        information["configured"] = self.__configured
        return information

    def check(self, arguments: list[dict]) -> dict:
        """Checks the input argument for errors

        Cycle through the items in the argument and checks if this instance
        can execute them. This method should be called before process with
        the same argument.

        Example 1

        >>> arguments = [
        >>>   { "transfer":
        >>>       {
        >>>           "type": "synchronous",
        >>>           "items": [
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
        >>>                     "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file1.txt"
        >>>                 },
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt",
        >>>                     "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file2.txt"
        >>>                 }
        >>>           ]
        >>>       }
        >>>   }
        >>> ]

        Example 2

        >>> arguments = [
        >>>   { "move_to_globus_collection": {
        >>>       "items": [
        >>>           {
        >>>               "source": "file://file1.txt",
        >>>               "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file1.txt"
        >>>           },
        >>>           {
        >>>               "source": "file://file2.txt",
        >>>               "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file2.txt"
        >>>           }
        >>>       ]
        >>>   }
        >>> ]

        Example 3

        >>> arguments = [
        >>>   { "move_from_globus_collection": {
        >>>       "items": [
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt"
        >>>               "destination": "file://file2.txt",
        >>>           }
        >>>       ]
        >>>   }
        >>> ]
        """
        checks = {}
        # Here we are cycling a list of dicts
        for index in range(len(arguments)):
            print("Checking arguments")
            for action in arguments[index]:
                print(f"action is: {action}")
                # Check if the action is supported
                if self.__supported_actions[action] is False:
                    checks[action] = (False, "action is not supported.")
                    continue

                if action == "transfer":
                    # Any agent with the globus plugin can submit a job to globus if it
                    # has access to the globus cloud
                    checks[action] = self.__runTransferSanityCheck(
                        arguments[index][action]
                    )

                elif action == "move_to_globus_collection":
                    checks[action] = self.__runMoveToGlobusSanityCheck(
                        arguments[index][action]
                    )

                elif action == "move_from_globus_collection":
                    checks[action] = self.__runMoveFromGlobusSanityCheck(
                        arguments[index][action]
                    )
                elif action == "get_task_status":
                    checks[action] = self.__runGetTaskStatusSanityCheck(
                        arguments[index][action]
                    )
                else:
                    checks[action] = (False, "Unrecognized action keyword")
        return checks

    def process(self, arguments: list[dict]) -> dict:
        """Run the globus process

        Supported actions include running a transfer between two endpoints

        :param arguments: the actions that the globus plugin should execute
        :type arguments: list of dicts

        Example 1

        >>> arguments = [
        >>>   { "transfer":
        >>>       {
        >>>           "type": "synchronous",
        >>>           "items": [
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
        >>>                     "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file1.txt"
        >>>                 },
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt",
        >>>                     "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/dest/file2.txt"
        >>>                 }
        >>>           ]
        >>>       }
        >>>   }
        >>> ]

        Example 2

        >>> arguments = [
        >>>   { "move_to_globus_collection": {
        >>>       "items": [
        >>>           {
        >>>               "source": "file://file1.txt",
        >>>               "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file1.txt"
        >>>           },
        >>>           {
        >>>               "source": "file://file2.txt",
        >>>               "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file2.txt"
        >>>           }
        >>>       ]
        >>>   }
        >>> ]

        Example 3

        >>> arguments = [
        >>>   { "move_from_globus_collection": {
        >>>       "items": [
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt"
        >>>               "destination": "file://file2.txt",
        >>>           }
        >>>       ]
        >>>   }
        >>> ]
        """
        if not self.__configured:
            raise Exception("Cannot run globus plugin, must first be configured.")

        return_values = {}
        for action_obj in arguments:
            # Make sure that the action is supported
            for key in action_obj:

                if key not in self.__supported_actions:
                    raise Exception(f"{key} is not supported.")

                if key == "transfer":
                    return_values[key] = self.__runTransfer(action_obj[key])
                elif key == "move_to_globus_collection":
                    self.__runMoveToGlobusCollection(action_obj[key])
                elif key == "move_from_globus_collection":
                    self.__runMoveFromGlobusCollection(action_obj[key])
                elif key == "get_task_status":
                    return_values[key] = self.__runGetTaskStatus(action_obj[key])

        return return_values
