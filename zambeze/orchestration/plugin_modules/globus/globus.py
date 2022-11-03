# Local imports
from ..abstract_plugin import Plugin
from .globus_common import (
    localEndpointExists,
    globusURISeparator,
    fileURISeparator,
    getMappedCollections,
    getGlobusScopes,
    SUPPORTED_ACTIONS
)
from .globus_message_helper import GlobusMessageHelper
from ...network import externalNetworkConnectionDetected

# Third party imports
from globus_sdk import GlobusError
import globus_sdk

# Standard imports
from copy import deepcopy
import os
from os.path import basename
from os.path import exists
from os.path import isdir
from os.path import isfile
from socket import gethostname
from typing import Optional

import json
import logging
import pickle
import shutil


class Globus(Plugin):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.__name = "globus"
        super().__init__(self.__name, logger=logger)
        # Client id is specific to Zambeze project it was created by registering
        # at developers.globus.org
        self.__access_to_globus_cloud = False
        # This is the default for Zambeze
        self.__client_id = None
        self.__endpoints = []
        self.__configured = False
        self.__flow = "client credential"
        self.__hostname = None
        self.__default_endpoint = None
        self.__supported_actions = SUPPORTED_ACTIONS
        self._message_helper = GlobusMessageHelper(logger)
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
        >>>       {
        >>>         "uuid": "4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5",
        >>>         "path": "/scratch/",
        >>>         "type": "guest"
        >>>       },
        >>>       {
        >>>         "uuid": "JD3D597A-2D2B-1MP8-A53F-0Z89A04C68A5",
        >>>         "path": "/project/",
        >>>         "type": "mapped"}
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

    def __validEndPoints(self, config: dict):
        """This method can only be run after the authentication flow has been run

        :param config: This is the configuration information read in from the
        agent.yaml file when the agent is started up.
        :type config: dict

        :raises Exception: If the collection/endpoint uuid is invalid
        """
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
                        raise Exception(
                            f"Invalid collection id {uid}. Collection is unknown."
                        )
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

        home_dir = os.path.expanduser("~")
        if not exists(home_dir + "/.zambeze"):
            os.mkdir(home_dir + "/.zambeze")

        token_file = home_dir + "/.zambeze/globus.tokens"
        if exists(token_file):
            infile = open(token_file, "rb")
            self.__authorizer = pickle.load(infile)
            infile.close()
        else:
            client = globus_sdk.NativeAppAuthClient(self.__client_id)

            client.oauth2_start_flow(
                requested_scopes=self.__scopes, refresh_tokens=True
            )
            authorize_url = client.oauth2_get_authorize_url()
            print(f"Please go to this URL and login:\n\n{authorize_url}\n")

            auth_code = input(
                "Please enter the code you get after login here: "
            ).strip()
            token_response = client.oauth2_exchange_code_for_tokens(auth_code)

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

            outfile = open(token_file, "wb")
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
        >>>                     "source": "globus://XXXXXXXX-...XXXXXXXXXXXX/file1.txt",
        >>>                     "destination": "globus://YYYY...YYYYYYY/dest/file1.txt"
        >>>                 },
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-...XXXXXXXXXXX/file2.txt",
        >>>                     "destination": "globus://YYYY...YYYYYYYY/dest/file2.txt"
        >>>                 }
        >>>     ]
        >>> }

        If the type is asynchrouns a runTransfer will return a callback action
        that can be executed to check the status of the generated task
        """

        for item in transfer["items"]:
            source_globus_uri = globusURISeparator(
                item["source"], self.__default_endpoint
            )
            dest_globus_uri = globusURISeparator(
                item["destination"], self.__default_endpoint
            )

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

            self._logger.info("Packet to be transferred by Globus.")
            self._logger.info(json.dumps(dict(tdata), indent=4))
            transfer_result = {}
            if "synchronous" == transfer["type"].lower():
                transfer_result = self.__tc.submit_transfer(tdata)
                self._logger.info(transfer_result)
                task_id = transfer_result["task_id"]
                while not self.__tc.task_wait(task_id, timeout=60):
                    self._logger.info(
                        "Another minute went by without {0} terminating".format(task_id)
                    )
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
        return next(
            (
                endpoint["path"]
                for endpoint in self.__endpoints
                if endpoint["uuid"] == globus_uuid
            ),
            None,
        )

    def __runMoveToGlobusCollection(self, action_package: dict):
        """Method is designed to move a local file to a Globus collection

        Example:

        "action_package" dict must have the following format

        >>> action_package = {
        >>>     "items": [
        >>>           {
        >>>               "source": "file://file1.txt",
        >>>               "destination": "globus://YYYYYYYY-...-YYYYYYYYYYYY/file1.txt"
        >>>           },
        >>>           {
        >>>               "source": "file://file2.txt",
        >>>               "destination": "globus://YYYYYYYY-...YYYYYYYYYYYY/file2.txt"
        >>>           }
        >>>     ]
        >>> }
        """
        for item in action_package["items"]:
            source_sep_file_uri = fileURISeparator(item["source"])
            source_path = source_sep_file_uri[0] + source_sep_file_uri[1]

            destination_sep_globus_uri = globusURISeparator(
                item["destination"], self.__default_endpoint
            )
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
        >>>               "source": "globus://YYYYYYY...-YYYYYYYYYYYY/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://YYYYYYY...YYYYYYYYYYY/file2.txt"
        >>>               "destination": "file://file2.txt",
        >>>           }
        >>>     ]
        >>> }
        """
        for item in action_package["items"]:
            destination_sep_file_uri = fileURISeparator(item["destination"])
            destination_path = destination_sep_file_uri[0]
            destination_file_name = destination_sep_file_uri[1]

            source_sep_globus_uri = globusURISeparator(
                item["source"], self.__default_endpoint
            )
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
        >>>             "source": "globus://XXXXXXXX-XX...X-XXXXXXXXXXXX/file1.txt",
        >>>             "destination": "globus://YYYYYY...-YYYYYYYYYYYY/dest/file1.txt"
        >>>         },
        >>>         {
        >>>             "source": "globus://XXXXXXXX-...XXX-XXXXXXXXXXXX/file2.txt",
        >>>             "destination": "globus://YYYY...Y-YYYYYYYYYYYY/dest/file2.txt"
        >>>         }
        >>>     ]
        >>> }
        """

        # Any agent with the globus plugin can submit a job to globus if it
        # has access to the globus cloud
        if not self.__access_to_globus_cloud:
            return False, "No access to Globus Service to conduct 'transfer'."

        return True, ""

    def __runMoveToGlobusSanityCheck(self, action_package: dict) -> (bool, str):
        for item in action_package["items"]:
            globus_sep_uri = globusURISeparator(
                item["destination"], self.__default_endpoint
            )
            if not localEndpointExists(globus_sep_uri[0], self.__endpoints):
                error_msg = f"Invalid source endpoint uuid dectected in \
                            'move_from_globus_collection' item: {item} \nuuid: \
                            {globus_sep_uri[0]}\nRecognized endpoints \
                            are {self.__endpoints}."
                return (False, error_msg)

            file_sep_uri = fileURISeparator(item["source"])
            file_path = file_sep_uri[0] + file_sep_uri[1]
            if not exists(file_path):
                return False, f"Item does not exist {file_path}"

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
        >>>               "source": "globus://XXXXXXXX-...X-XXXXXXXXXXXX/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://XXXXXXXX-X...XXX-XXXXXXXXXXXX/file2.txt"
        >>>               "destination": "file://file2.txt",
        >>>           }
        >>>    ]
        >>> }
        >>> assert self.__runMoveFromGlobusSanityCheck(action_package)
        """
        for item in action_package["items"]:
            globus_sep_uri = globusURISeparator(item["source"], self.__default_endpoint)
            if not localEndpointExists(globus_sep_uri[0], self.__endpoints):
                error_msg = f"Invalid source endpoint uuid dectected in \
                            'move_from_globus_collection' item: {item} \nuuid: \
                            {globus_sep_uri[0]}\nRecognized endpoints \
                            are {self.__endpoints}."
                return (False, error_msg)

            posix_path_to_endpoint = self.__getPOSIXpathToEndpoint(globus_sep_uri[0])
            file_path = posix_path_to_endpoint + globus_sep_uri[1] + globus_sep_uri[2]
            if not exists(file_path):
                return False, f"Item does not exist {file_path}"

        return (True, "")

    def __checkAccessToGlobusCloud(self):
        """Will check if we can reach the internet and caches access to globus
        cloud if cannot reach it.
        """
        if externalNetworkConnectionDetected() is False:
            self._logger.debug(
                "Unable to connect to external network access to globus cloud denied"
            )
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
              {
                "uuid": "4DED5CB6-EF22-4DC6-A53F-0A97A04CD8B5",
                "path": "/scratch/",
                "type": "guest"
              },
              {
                "uuid": "JD3D597A-2D2B-1MP8-A53F-0Z89A04C68A5",
                "path": "/project/",
                "type": "mapped"}
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

        self._logger.debug(json.dumps(config, indent=4))
        if "authentication_flow" in config:
            if "client_id" in config:
                self.__client_id = config["client_id"]

        print("Client id is ")
        print(self.__client_id)

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
        except GlobusError as e:
            logging.exception(
                "Error detected while attempting to authenticate and"
                "communicate with the Globus API"
            )
            raise e

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

    def check(self, arguments: list[dict]) -> list[dict]:
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
        >>>                     "source": "globus://XXXXXXXX...X-XXXXXXXX/file1.txt",
        >>>                     "destination": "globus://YYY...YYYYYYYY/dest/file1.txt"
        >>>                 },
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-...XXXXXXXXXXXX/file2.txt",
        >>>                     "destination": "globus://YYYY...YYYYYYYY/dest/file2.txt"
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
        >>>               "destination": "globus://YYYYY...YY-YYYYYYYYYYYY/file1.txt"
        >>>           },
        >>>           {
        >>>               "source": "file://file2.txt",
        >>>               "destination": "globus://YYYYY...Y-YYYYYYYYYYYY/file2.txt"
        >>>           }
        >>>       ]
        >>>   }
        >>> ]

        Example 3

        >>> arguments = [
        >>>   { "move_from_globus_collection": {
        >>>       "items": [
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XX...XXXXXXXXXX/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://XXXXXXXX-XX...XXXXXXXXXXX/file2.txt"
        >>>               "destination": "file://file2.txt",
        >>>           }
        >>>       ]
        >>>   }
        >>> ]
        """
        checks = []
        # Here we are cycling a list of dicts
        for index in range(len(arguments)):
            for action in arguments[index]:

                schema_checks = self._message_helper.validateAction(
                    arguments[index], action
                )

                if len(schema_checks) > 0:
                    if schema_checks[0][action][0] is False:
                        checks.extend(schema_checks)
                        continue

                # Check if the action is supported
                if self.__supported_actions[action] is False:
                    checks.append({action: (False, "action is not supported.")})
                    continue

                if action == "transfer":
                    # Any agent with the globus plugin can submit a job to globus if it
                    # has access to the globus cloud
                    checks.append(
                        {
                            action: self.__runTransferSanityCheck(
                                arguments[index][action]
                            )
                        }
                    )

                elif action == "move_to_globus_collection":
                    checks.append(
                        {
                            action: self.__runMoveToGlobusSanityCheck(
                                arguments[index][action]
                            )
                        }
                    )

                elif action == "move_from_globus_collection":
                    checks.append(
                        {
                            action: self.__runMoveFromGlobusSanityCheck(
                                arguments[index][action]
                            )
                        }
                    )
                elif action == "get_task_status":
                    checks.append({action: (True, "")})
                else:
                    checks.append({action: (False, "Unrecognized action keyword")})
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
        >>>                     "source": "globus://XXXXXXXX-XXX...XXXX/file1.txt",
        >>>                     "destination": "globus://YYYYYYY...YYYY/dest/file1.txt"
        >>>                 },
        >>>                 {
        >>>                     "source": "globus://XXXXXXXX-XXX...XXXX/file2.txt",
        >>>                     "destination": "globus://YYYYYYY...YYYYY/dest/file2.txt"
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
        >>>               "destination": "globus://YYYYYYYY...YYYYYYYYYY/file1.txt"
        >>>           },
        >>>           {
        >>>               "source": "file://file2.txt",
        >>>               "destination": "globus://YYYYYYYY...-YYYYYYYYYYYY/file2.txt"
        >>>           }
        >>>       ]
        >>>   }
        >>> ]

        Example 3

        >>> arguments = [
        >>>   { "move_from_globus_collection": {
        >>>       "items": [
        >>>           {
        >>>               "source": "globus://XXXXX...XXXXXXXXXXX/file1.txt"
        >>>               "destination": "file://file1.txt",
        >>>           },
        >>>           {
        >>>               "source": "globus://XXXXX...XXX-XXXXXXXXXXXX/file2.txt"
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
