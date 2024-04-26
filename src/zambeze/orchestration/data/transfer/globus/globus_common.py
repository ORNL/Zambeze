# Local imports
from zambeze.utils.identity import valid_uuid

# Standard imports
from os.path import exists

SUPPORTED_ACTIONS = {
    "transfer": False,
    "move_to_globus_collection": False,
    "move_from_globus_collection": False,
    "get_task_status": False,
}


def local_endpoint_exists(globus_uuid: str, endpoint_list: list[dict]) -> bool:
    for item in endpoint_list:
        if item["uuid"].lower() == globus_uuid.lower():
            return True
    return False


def local_endpoint_config_check(config: dict) -> None:
    # Check that the UUIDs are correct
    if "local_endpoints" in config:
        for local_endpoint in config["local_endpoints"]:
            if not valid_uuid(local_endpoint["uuid"]):
                raise Exception(
                    f"Invalid uuid detected in plugin: {local_endpoint['uuid']}"
                )
            if not exists(local_endpoint["path"]):
                # Check that the collection path is correct and exists on the local
                # POSIX filesystem
                raise Exception(
                    f"Invalid path detected in plugin: {local_endpoint['path']}"
                )

        if "default_endpoint" not in config:
            raise Exception(
                "'default_endpoint' key value missing from config"
                " config must have 'default_endpoint' specified if"
                " local_endpoints are configured."
            )

        if not valid_uuid(config["default_endpoint"]):
            raise Exception(
                "Invalid uuid detected in plugin for default endpoint: "
                f" {config['default_endpoint']}"
            )

        # Make sure that default_endpoint is one of the endpoints that has
        # been configured

        if not local_endpoint_exists(
            config["default_endpoint"], config["local_endpoints"]
        ):
            error_msg = f"Invalid default endpoint {config['default_endpoint']}"
            error_msg = error_msg + " not one of the 'local_endpoints'"
            error_msg = error_msg + " check your "
            error_msg = error_msg + " agent.yaml file. Local endpoints are:"
            error_msg = error_msg + f"\n{config['local_endpoints']}"
            raise Exception(error_msg)


def check_transfer_endpoint(action_package: dict) -> tuple[bool, str]:
    """Makes sure each item to be transferred has the correct format

    :param action_package: the package that contains instructions for
    transferring files.
    :type action_package: dict

    :Example:

    "items": [
        {
             "source": "globus://XXXXXXXX-...-XXXXXXXXXXXX/file1/txt"
             "destination": "globus://YYYYYYYY-...-YYYYYYYYYYYY/dest/file1/txt"
        },
        {
             "source": "globus://XXXXXXXX-...-XXXXXXXXXXXX/file2/txt"
             "destination": "globus://YYYYYYYY-...-YYYYYYYYYYYY/dest/file2/txt"
        }
    ]
    """
    for item in action_package["items"]:
        if "source" not in item:
            return False, "'source' missing from 'items' in 'transfer'"
        else:
            valid, msg = check_endpoint(item["source"], ["globus"])
            if not valid:
                return False, "Error in source\n" + msg

        if "destination" not in item:
            return False, "'destination' missing from 'items' in 'transfer'"
        else:
            valid, msg = check_endpoint(item["destination"], ["globus"])
            if not valid:
                return False, "Error in destination\n" + msg
    return True, ""


def get_mapped_collections(config: dict) -> list[str]:
    """Returns a list of the UUIDs that are mapped collections

    :param config: Indicates where on the local filesystem the Globus collection
    is located.
    :type config: dict

    :Example:

    config = {
        "local_endpoints": [
            { "UUID": "XXXX...XXXX", "path": "/here/file", "type": "guest"},
            { "UUID": "YYYY...YYYY", "path": "/there/file2", "type": "mapped"}
        ]
    }
    mapped_coll = get_mapped_collections(config)
    print(mapped_coll)
    # Single entry would be printed in this case
    # ["YYYY...YYYY"]
    """
    mapped_collections = []
    if "local_endpoints" in config:
        for local_endpoint in config["local_endpoints"]:
            if local_endpoint["type"] == "mapped":
                mapped_collections.append(local_endpoint["uuid"])

    return mapped_collections


def is_36char(item: str):
    return len(item) == 36


def get_globus_scopes(mapped_collections: list[str]) -> str:
    """Get the globus scopes needed to access the mapped collections

    :param mapped_collections: This should contain the UUIDs of only mapped
        collections
    :type mapped_collections: list[str]

    For globus mapped collections, explicit scope has to be requested to
    access the collection.

    :Example: First example empty mapped collection list

    mapped_coll = [""]
    scopes = get_globus_scopes(mapped_coll)
    print(scopes)
    # Will print general scopes
    # urn:globus:auth:scope:transfer.api.globus.org:all

    :Example: Second example

    mapped_coll = ["XXXX...XXXX", "YYYY...YYYY"]
    scopes = get_globus_scopes(mapped_coll)
    print(scopes)
    # Will print general scopes
    # urn:globus:auth:scope:transfer.api.globus.org:all[*https://auth.globus.org/scopes/XXXX...XXXX/data_access *https://auth.globus.org/scopes/YYYY...YYYY/data_access] # noqa: E501
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


def check_endpoint(item: str, supported_types: list[str]) -> tuple[bool, str]:
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

    item = "globus:://XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
    valid, msg = check_endpoint(item)
    assert valid
    """
    # Only "globus relative" path type supported
    for supported_type in supported_types:
        if item.startswith(supported_type + "://"):
            return True, ""

    return (
        False,
        f"Missing {item} not in supported types \
                {supported_types} uri should start with i.e. globus://",
    )


def check_all_items_have_valid_endpoints(
    items: list[dict],
    supported_source_path_types: list[str],
    supported_destination_path_types: list[str],
) -> tuple[bool, str]:
    """Check that all items that are too be moved are schematically correct

    :return: Returns true if the schema of the items is valid and false otherwise
    :rtype: bool

    :Example: Input

    Provided a list of items to be moved

    "items": [
          {
              "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file1.txt",
              "destination": "globus://YYYYYYYY-...-YYYYYYYYYYYY/dest/file1.txt"
          },
          {
              "source": "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file2.txt",
              "destination": "globus://YYYYYYYY-...-YYYYYYYYYYYY/dest/file2.txt"
          }
    ]

    "Example: Input 2

    "items": [
        {
            "source": "file://file1.txt",
            "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file1.txt"
        },
        {
            "source": "file://file2.txt",
            "destination": "globus://YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/file2.txt"
        }
    ]


    supported_source_path_types = ["file"]
    supported_destination_path_types = ["globus"]
    assert check_all_items_have_valid_endpoints(
        items,
        supported_source_path_types,
        supported_destination_path_types)
    """
    for item in items:
        if "source" not in item:
            return False, "Item is missing source key"
        if "destination" not in item:
            return False, "Item is missing destination key"

        valid, msg = check_endpoint(item["source"], supported_source_path_types)
        if not valid:
            return False, "Invalid source\n" + msg

        valid, msg = check_endpoint(
            item["destination"], supported_destination_path_types
        )
        if not valid:
            return False, "Invalid destination\n" + msg

    return True, ""
