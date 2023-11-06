# Local imports
from ..abstract_plugin_message_validator import PluginMessageValidator
from .globus_common import (
    check_transfer_endpoint,
    check_all_items_have_valid_endpoints,
    SUPPORTED_ACTIONS,
)
from .globus_uri_separator import GlobusURISeparator
from ...identity import valid_uuid

# Standard imports
from typing import Optional, overload
import logging


class GlobusMessageValidator(PluginMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("globus", logger=logger)
        self.__known_actions = SUPPORTED_ACTIONS.keys()
        self.__globus_uri_separator = GlobusURISeparator()

    def __run_transfer_validation_check(self, action_package: dict) -> tuple[bool, str]:
        """Checks to ensure that the action_package has the right format and
        checks for errors.

        :Example:

        {
            "type": "synchronous",
            "items": [
                {
                   "source": "globus://XXXXXXXX-XX...X-XXXXXXXXXXXX/file1.txt",
                    "destination": "globus://YYYYYY...-YYYYYYYYYYYY/dest/file1.txt"
                },
                {
                    "source": "globus://XXXXXXXX-...XXX-XXXXXXXXXXXX/file2.txt",
                    "destination": "globus://YYYY...Y-YYYYYYYYYYYY/dest/file2.txt"
                }
            ]
        }
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

        return check_transfer_endpoint(action_package)

    def __run_move_to_globus_validation_check(
        self, action_package: dict
    ) -> tuple[bool, str]:
        supported_source_path_types = ["file"]
        supported_destination_path_types = ["globus"]

        valid, msg = check_all_items_have_valid_endpoints(
            action_package["items"],
            supported_source_path_types,
            supported_destination_path_types,
        )

        if valid:
            for item in action_package["items"]:
                globus_sep_uri = self.__globus_uri_separator.separate(
                    item["destination"]
                )
                if globus_sep_uri["uuid"] is not None:
                    if not valid_uuid(globus_sep_uri["uuid"]):
                        error_msg = "Invalid uuid detected in "
                        error_msg += "'move_from_globus_collection' item: "
                        error_msg += f"{item} \nuuid: "
                        error_msg += f"{globus_sep_uri['uuid']}"
                        return (False, error_msg)

        return (valid, msg)

    def __run_move_from_globus_validation_check(
        self, action_package: dict
    ) -> tuple[bool, str]:
        """Run a sanity check for the action "move_from_globus_collection"

        return: Will return true if the sanity check passes false otherwise

        Example:

        action_package = {
           "source_host_name": "",
           "destination_collection_UUID": "",
           "items": [
                  {
                      "source": "globus://XXXXXXXX-...X-XXXXXXXXXXXX/file1.txt"
                      "destination": "file://file1.txt",
                  },
                  {
                      "source": "globus://XXXXXXXX-X...XXX-XXXXXXXXXXXX/file2.txt"
                      "destination": "file://file2.txt",
                  }
           ]
        }
        assert self.__run_move_from_globus_sanity_check(action_package)
        """

        supported_source_path_types = ["globus"]
        supported_destination_path_types = ["file"]

        valid, msg = check_all_items_have_valid_endpoints(
            action_package["items"],
            supported_source_path_types,
            supported_destination_path_types,
        )

        if valid:
            for item in action_package["items"]:
                globus_sep_uri = self.__globus_uri_separator.separate(item["source"])
                if not valid_uuid(globus_sep_uri["uuid"]):
                    error_msg = "Invalid uuid detected in "
                    error_msg += f"'move_from_globus_collection' item: {item} "
                    error_msg += f"\nuuid: {globus_sep_uri['uuid']}"
                    return (False, error_msg)

        return (valid, msg)

    def __run_get_task_status_validation_check(
        self, action_package: dict
    ) -> tuple[bool, str]:
        """Checks that the get_task_status action is correctly configured

        :Example:

        action_package = {
            "task_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
        }
        """
        if "task_id" not in action_package:
            return (False, "Missing 'task_id' in get_task_status action")

        if not valid_uuid(action_package["task_id"]):
            return (
                False,
                f"Invalid 'task_id' detected in 'get_task_status': \
            {action_package['task_id']}",
            )
        return (True, "")

    def _validate_action(self, action: str, checks: list, arguments: dict):
        # Check if the action is supported
        if action not in self.__known_actions:
            checks.append({action: (False, "action is unknown.")})
            return checks

        if action == "transfer":
            # Any agent with the globus plugin can submit a job to globus if it
            # has access to the globus cloud
            checks.append(
                {action: self.__run_transfer_validation_check(arguments[action])}
            )

        elif action == "move_to_globus_collection":
            checks.append(
                {action: self.__run_move_to_globus_validation_check(arguments[action])}
            )

        elif action == "move_from_globus_collection":
            checks.append(
                {action: self.__run_move_from_globus_validation_check(arguments[action])}
            )
        elif action == "get_task_status":
            checks.append(
                {action: self.__run_get_task_status_validation_check(arguments[action])}
            )
        else:
            checks.append({action: (False, "Unrecognized action keyword")})

        checks.append({action: (True, "")})
        return checks

    def validate_action(self, arguments: dict, action) -> list:
        """Checks the input argument for errors

        Cycle through the items in the argument and checks if this instance
        can execute them. This method should be called before process with
        the same argument. Note this only validates a single action not a list
        of actions

        Example 1

        arguments = {
        "transfer":
           {
               "type": "synchronous",
               "items": [
                     {
                         "source": "globus://XXXXXXXX...X-XXXXXXXX/file1.txt",
                         "destination": "globus://YYY...YYYYYYYY/dest/file1.txt"
                     },
                     {
                         "source": "globus://XXXXXXXX-...XXXXXXXXXXXX/file2.txt",
                         "destination": "globus://YYYY...YYYYYYYY/dest/file2.txt"
                     }
               ]
           }
        }
        """
        checks = []
        return self._validate_action(action, checks, arguments)

    @overload
    def validate_message(self, arguments: list[dict]) -> list:
        ...

    def validate_message(self, arguments) -> list:
        """Checks the input argument for errors

        Cycle through the items in the argument and checks if this instance
        can execute them. This method should be called before process with
        the same argument.

        Example 1

        arguments = [
          { "transfer":
              {
                  "type": "synchronous",
                  "items": [
                        {
                            "source": "globus://XXXXXXXX...X-XXXXXXXX/file1.txt",
                            "destination": "globus://YYY...YYYYYYYY/dest/file1.txt"
                        },
                        {
                            "source": "globus://XXXXXXXX-...XXXXXXXXXXXX/file2.txt",
                            "destination": "globus://YYYY...YYYYYYYY/dest/file2.txt"
                        }
                  ]
              }
          }
        ]

        Example 2

        arguments = [
          { "move_to_globus_collection": {
              "items": [
                  {
                      "source": "file://file1.txt",
                      "destination": "globus://YYYYY...YY-YYYYYYYYYYYY/file1.txt"
                  },
                  {
                      "source": "file://file2.txt",
                      "destination": "globus://YYYYY...Y-YYYYYYYYYYYY/file2.txt"
                  }
              ]
          }
        ]

        Example 3

        arguments = [
          { "move_from_globus_collection": {
              "items": [
                  {
                      "source": "globus://XXXXXXXX-XX...XXXXXXXXXX/file1.txt"
                      "destination": "file://file1.txt",
                  },
                  {
                      "source": "globus://XXXXXXXX-XX...XXXXXXXXXXX/file2.txt"
                      "destination": "file://file2.txt",
                  }
              ]
          }
        ]
        """
        checks = []
        # Here we are cycling a list of dicts
        for index in range(len(arguments)):
            for action in arguments[index]:
                checks = self._validate_action(action, checks, arguments[index])
        return checks
