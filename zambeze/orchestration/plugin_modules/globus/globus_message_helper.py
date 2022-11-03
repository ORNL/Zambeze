# Local imports
from ..abstract_plugin_message_helper import PluginMessageHelper
from .globus_common import (
    checkTransferEndpoint,
    checkAllItemsHaveValidEndpoints,
    globusURISeparator,
    SUPPORTED_ACTIONS
)
from ...identity import validUUID

# Standard imports
from typing import Optional

import logging


class GlobusMessageHelper(PluginMessageHelper):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("globus", logger=logger)
        self.__known_actions = SUPPORTED_ACTIONS.keys()

    def __runTransferValidationCheck(self, action_package: dict) -> (bool, str):
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

        required_keys = ["type", "items"]
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

    def __runMoveToGlobusValidationCheck(self, action_package: dict) -> (bool, str):
        supported_source_path_types = ["file"]
        supported_destination_path_types = ["globus"]

        valid, msg = checkAllItemsHaveValidEndpoints(
            action_package["items"],
            supported_source_path_types,
            supported_destination_path_types,
        )

        if valid:
            for item in action_package["items"]:
                globus_sep_uri = globusURISeparator(
                    item["destination"]
                )
                if globus_sep_uri[0] is not None:
                    if not validUUID(globus_sep_uri[0]):
                        error_msg = f"Invalid uuid dectected in \
                                    'move_from_globus_collection' item: {item} \nuuid: \
                                    {globus_sep_uri[0]}"
                        return (False, error_msg)

        return (valid, msg)

    def __runMoveFromGlobusValidationCheck(self, action_package: dict) -> (bool, str):
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

        supported_source_path_types = ["globus"]
        supported_destination_path_types = ["file"]

        valid, msg = checkAllItemsHaveValidEndpoints(
            action_package["items"],
            supported_source_path_types,
            supported_destination_path_types,
        )

        if valid:
            for item in action_package["items"]:
                globus_sep_uri = globusURISeparator(
                    item["source"], self.__default_endpoint
                )
                if not validUUID(globus_sep_uri[0]):
                    error_msg = f"Invalid uuid dectected in \
                                'move_from_globus_collection' item: {item} \nuuid: \
                                {globus_sep_uri[0]}"
                    return (False, error_msg)

        return (valid, msg)

    def __runGetTaskStatusValidationCheck(self, action_package: dict) -> (bool, str):
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

    def _validateAction(self, action: str, checks: list, arguments: dict):
        # Check if the action is supported
        if action not in self.__known_actions:
            checks.append({action: (False, "action is unknown.")})
            return checks

        if action == "transfer":
            # Any agent with the globus plugin can submit a job to globus if it
            # has access to the globus cloud
            checks.append(
                {action: self.__runTransferValidationCheck(arguments[action])}
            )

        elif action == "move_to_globus_collection":
            checks.append(
                {action: self.__runMoveToGlobusValidationCheck(arguments[action])}
            )

        elif action == "move_from_globus_collection":
            checks.append(
                {action: self.__runMoveFromGlobusValidationCheck(arguments[action])}
            )
        elif action == "get_task_status":
            checks.append(
                {action: self.__runGetTaskStatusValidationCheck(arguments[action])}
            )
        else:
            checks.append({action: (False, "Unrecognized action keyword")})

        checks.append({action: (True, "")})
        return checks

    def validateAction(self, arguments: dict, action) -> list:
        """Checks the input argument for errors

        Cycle through the items in the argument and checks if this instance
        can execute them. This method should be called before process with
        the same argument. Note this only validates a single action not a list
        of actions

        Example 1

        >>> arguments = {
        >>> "transfer":
        >>>    {
        >>>        "type": "synchronous",
        >>>        "items": [
        >>>              {
        >>>                  "source": "globus://XXXXXXXX...X-XXXXXXXX/file1.txt",
        >>>                  "destination": "globus://YYY...YYYYYYYY/dest/file1.txt"
        >>>              },
        >>>              {
        >>>                  "source": "globus://XXXXXXXX-...XXXXXXXXXXXX/file2.txt",
        >>>                  "destination": "globus://YYYY...YYYYYYYY/dest/file2.txt"
        >>>              }
        >>>        ]
        >>>    }
        >>> }
        """
        checks = []
        return self._validateAction(action, checks, arguments)

    def validateMessage(self, arguments: list[dict]) -> list:
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
                checks = self._validateAction(action, checks, arguments[index])
        return checks

    def messageTemplate(self, args=None) -> dict:

        if args is None or args == "transfer":
            return {
                "transfer": {
                    "type": "synchronous",
                    "items": [
                        {
                            "source": "globus://XXXXXXXX...X-XXXXXXXX/file1.txt",
                            "destination": "globus://YYY...YYYYYYYY/dest/file1.txt",
                        },
                        {
                            "source": "globus://XXXXXXXX-...XXXXXXXXXXXX/file2.txt",
                            "destination": "globus://YYYY...YYYYYYYY/dest/file2.txt",
                        },
                    ],
                }
            }
        elif args == "move_to_globus_collection":
            return {
                "move_to_globus_collection": {
                    "items": [
                        {
                            "source": "file://file1.txt",
                            "destination": "globus://YYYYY...YY-YYYYYYYYYYYY/file1.txt",
                        },
                        {
                            "source": "file://file2.txt",
                            "destination": "globus://YYYYY...Y-YYYYYYYYYYYY/file2.txt",
                        },
                    ]
                }
            }
        elif args == "move_from_globus_collection":
            return {
                "move_from_globus_collection": {
                    "items": [
                        {
                            "source": "globus://XXXXXXXX-XX...XXXXXXXXXX/file1.txt",
                            "destination": "file://file1.txt",
                        },
                        {
                            "source": "globus://XXXXXXXX-XX...XXXXXXXXXXX/file2.txt",
                            "destination": "file://file2.txt",
                        },
                    ]
                }
            }
        else:
            raise Exception(
                "Unrecognized argument provided, cannot generate " "messageTemplate"
            )