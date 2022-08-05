# Local imports
import zambeze.orchestration.plugin_modules.globus as globus

# Standard imports
import os
import pytest
import random
import socket
import time

GITLAB_RUNNER_UUIDs = ["f4e5e85c-3a35-455f-9d91-1ee3a0564935"]


@pytest.mark.unit
def test_getMappedCollections():
    config = {
        "collections": [
            {
                "UUID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                "path": "/here/file",
                "type": "guest",
            },
            {
                "UUID": "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
                "path": "/there/file2",
                "type": "mapped",
            },
        ]
    }

    mapped_coll_UUIDs = globus.getMappedCollections(config)

    assert len(mapped_coll_UUIDs) == 1
    assert mapped_coll_UUIDs[0] == "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY"


@pytest.mark.unit
def test_getGlobusScopes():
    mapped_collections = []
    scopes = globus.getGlobusScopes(mapped_collections)
    assert scopes == "urn:globus:auth:scope:transfer.api.globus.org:all"

    # These are invalid entries so they will be ignored
    mapped_collections = ["", "XXXX"]
    scopes = globus.getGlobusScopes(mapped_collections)
    assert scopes == "urn:globus:auth:scope:transfer.api.globus.org:all"

    # Though the middle entry is not really a valid UUID it is 36 chars so
    # it should be passed as a valid scope
    mapped_collections = [
        "",
        "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
        "XXXX",
        "ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ",
    ]

    scopes = globus.getGlobusScopes(mapped_collections)

    correct_scopes = "urn:globus:auth:scope:transfer.api.globus.org:all\
[*https://auth.globus.org/scopes/\
YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/data_access\
 *https://auth.globus.org/scopes/\
ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ/data_access]"

    assert scopes == correct_scopes


@pytest.mark.unit
def test_checkAllItemsHaveValidEndpoints():
    file_name = "demofile_checkAllItemsHaveValidEndpoints.txt"
    f = open(file_name, "w")
    f.write("Testing for valid source file for test_checkAllItemsHaveValidEndpoints")
    f.close()

    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    file_name2 = "demofile2_checkAllItemsHaveValidEndpoints.txt"
    f = open(file_name2, "w")
    f.write("Testing for valid source file for test_checkAllItemsHaveValidEndpoints")
    f.close()

    file_path2 = current_valid_path + "/" + file_name2

    items = [
        {
            "source": {"type": "posix absolute", "path": file_path},
            "destination": {"type": "globus relative", "path": "/"},
        },
        {
            "source": {"type": "posix absolute", "path": file_path2},
            "destination": {
                "type": "globus relative",
                "path": "/sub_folder/file2.jpeg",
            },
        },
    ]

    supported_source_path_types = ["posix absolute", "posix user home"]
    supported_destination_path_types = ["globus relative"]

    output = globus.checkAllItemsHaveValidEndpoints(
        items, supported_source_path_types, supported_destination_path_types
    )
    assert output[0]

    items2 = [
        {
            "source": {"type": "globus relative", "path": "/home/cades/file.txt"},
            "destination": {"type": "globus relative", "path": "/"},
        }
    ]

    # This should be false because in this case "globus relative" is not in the
    # supported_source_path_types
    output = globus.checkAllItemsHaveValidEndpoints(
        items2, supported_source_path_types, supported_destination_path_types
    )
    assert not output[0]

    items3 = [
        {
            "source": {"type": "posix absolute", "path": "/home/cades/file.txt"},
            "destination": {"type": "globus relative"},
        }
    ]

    # This should be false because in this case "destination" is missing a
    # "path"
    output = globus.checkAllItemsHaveValidEndpoints(
        items3, supported_source_path_types, supported_destination_path_types
    )
    assert not output[0]


@pytest.mark.globus
def test_globus_basic1():

    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    globus_plugin = globus.Globus()

    assert globus_plugin.name == "globus"
    assert globus_plugin.configured is False

    """Requires that the env variable is provided"""
    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {
            "type": "client credential",
            "secret": os.getenv(required_env_variables[1]),
        },
    }

    globus_plugin.configure(configuration)

    assert globus_plugin.configured

    assert len(globus_plugin.supportedActions) == 2
    # We assume that we at least have access to the globus cloud
    assert "transfer" in globus_plugin.supportedActions


@pytest.mark.globus
def test_globus_basic2():

    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    globus_plugin = globus.Globus()

    """Requires that the env variable is provided

    A valid globus collection must also exist on this machine
    in order for the move to globus endpoint and move from
    globus endpoint to local posix file system to work."""
    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {
            "type": "client credential",
            "secret": os.getenv(required_env_variables[1]),
        },
        "collections": [
            {
                "UUID": os.getenv(required_env_variables[2]),
                "path": "/home/cades/Collections/default",
                "type": "mapped",
            }
        ],
    }

    globus_plugin.configure(configuration)

    assert len(globus_plugin.supportedActions) == 4


@pytest.mark.globus
def test_globus_move_check():

    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {
            "type": "client credential",
            "secret": os.getenv(required_env_variables[1]),
        },
        "collections": [
            {
                "UUID": os.getenv(required_env_variables[2]),
                "path": "/home/cades/Collections/default",
                "type": "mapped",
            }
        ],
    }

    globus_plugin = globus.Globus()
    globus_plugin.configure(configuration)

    # Create a file on the local posix system
    file_name = "demofile_for_globus1.txt"
    f = open(file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    destination_path = "/"
    sub_folder = ""
    # This is so that we can run the test both as a runner and as user
    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
        sub_folder = "runner/"

    package = [
        {
            "move_to_globus_collection": {
                "destination_collection_UUID": os.getenv(required_env_variables[2]),
                "source_host_name": socket.gethostname(),
                "items": [
                    {
                        "source": {"type": "posix absolute", "path": file_path},
                        "destination": {
                            "type": "globus relative",
                            "path": destination_path + sub_folder,
                        },
                    }
                ],
            }
        }
    ]

    checked_actions = globus_plugin.check(package)
    assert checked_actions["move_to_globus_collection"][0]


@pytest.mark.globus
def test_globus_transfer_check():

    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {
            "type": "client credential",
            "secret": os.getenv(required_env_variables[1]),
        },
        "collections": [
            {
                "UUID": os.getenv(required_env_variables[2]),
                "path": "/home/cades/Collections/default",
                "type": "mapped",
            }
        ],
    }

    globus_plugin = globus.Globus()
    globus_plugin.configure(configuration)

    # Create a file on the local posix system
    file_name = "demofile_for_globus1.txt"
    f = open(file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    destination_path = "/"
    sub_folder = ""
    # This is so that we can run the test both as a runner and as user
    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
        sub_folder = "runner/"

    package = [
        {
            "move_to_globus_collection": {
                "destination_collection_UUID": os.getenv(required_env_variables[2]),
                "source_host_name": socket.gethostname(),
                "items": [
                    {
                        "source": {"type": "posix absolute", "path": file_path},
                        "destination": {
                            "type": "globus relative",
                            "path": destination_path + sub_folder,
                        },
                    }
                ],
            }
        },
        {
            "transfer": {
                "source_collection_UUID": os.getenv(required_env_variables[2]),
                "destination_collection_UUID": os.getenv(required_env_variables[3]),
                "type": "synchronous",
                "items": [
                    {
                        "source": {
                            "type": "globus relative",
                            "path": "/" + sub_folder + file_name,
                        },
                        "destination": {
                            "type": "globus relative",
                            "path": destination_path + sub_folder + file_name,
                        },
                    }
                ],
            }
        },
    ]

    output = globus_plugin.check(package)

    for item in output:
        assert output[item][0]


@pytest.mark.globus
def test_globus_process():

    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    path_to_endpoint = "/home/cades/Collections/default"
    path_to_endpoint_shared = "/home/cades/Collections/default/shared"

    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {
            "type": "client credential",
            "secret": os.getenv(required_env_variables[1]),
        },
        "collections": [
            {
                "UUID": os.getenv(required_env_variables[2]),
                "path": path_to_endpoint,
                "type": "mapped",
            },
            {
                "UUID": os.getenv(required_env_variables[3]),
                "path": path_to_endpoint_shared,
                "type": "guest",
            },
        ],
    }

    globus_plugin = globus.Globus()
    globus_plugin.configure(configuration)

    # Create a file on the local posix system
    file_name = "demofile_for_globus1.txt"
    f = open(file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    relative_destination_file_path = "/"
    sub_folder = ""
    # This is so that we can run the test both as a runner and as user
    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
        sub_folder = "runner/"
    # action items in the list should be executed in order
    package = [
        {
            "move_to_globus_collection": {
                "destination_collection_UUID": os.getenv(required_env_variables[2]),
                "source_host_name": socket.gethostname(),
                "items": [
                    {
                        "source": {"type": "posix absolute", "path": file_path},
                        "destination": {
                            "type": "globus relative",
                            "path": relative_destination_file_path + sub_folder,
                        },
                    }
                ],
            }
        },
        {
            "transfer": {
                "source_collection_UUID": os.getenv(required_env_variables[2]),
                "destination_collection_UUID": os.getenv(required_env_variables[3]),
                "type": "synchronous",
                "items": [
                    {
                        "source": {
                            "type": "globus relative",
                            "path": "/" + sub_folder + file_name,
                        },
                        "destination": {
                            "type": "globus relative",
                            "path": relative_destination_file_path
                            + sub_folder
                            + file_name,
                        },
                    }
                ],
            }
        },
    ]

    # This test is designed to move a file to the globus endpoint
    # So before we get started we are going to make sure that a file
    # does not already exist at that location
    abs_path_destination = (
        path_to_endpoint
        + relative_destination_file_path
        + sub_folder
        + os.path.basename(file_path)
    )
    # After it gets transferred using globus it should end up moving to the sub_folder
    abs_path_destination_shared = (
        path_to_endpoint
        + relative_destination_file_path
        + "shared/"
        + sub_folder
        + os.path.basename(file_path)
    )
    if os.path.exists(abs_path_destination):
        os.remove(abs_path_destination)
    if os.path.exists(abs_path_destination_shared):
        os.remove(abs_path_destination_shared)

    checked_items = globus_plugin.check(package)
    all_checks_pass = True
    for item in checked_items:
        if not checked_items[item][0]:
            print("Something went wrong.")
            print(checked_items[item][1])
            all_checks_pass = False

    if all_checks_pass:
        globus_plugin.process(package)

    # After processing we should verify that the file exists at the final location
    assert os.path.exists(abs_path_destination_shared)


@pytest.mark.globus
def test_globus_process_from_esnet():
    """NOTE

    We cannot simply download to a collection, we have to download to
    a folder that is owned by the user running the this test. I.e. if
    the GitLab Runner is being used then we have to specify a folder that
    the GitLab Runner can actually access from the POSIX side.
    """
    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    path_to_endpoint = "/home/cades/Collections/default"
    path_to_endpoint_shared = "/home/cades/Collections/default/shared"

    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {
            "type": "client credential",
            "secret": os.getenv(required_env_variables[1]),
        },
        "collections": [
            {
                "UUID": os.getenv(required_env_variables[2]),
                "path": path_to_endpoint,
                "type": "mapped",
            },
            {
                "UUID": os.getenv(required_env_variables[3]),
                "path": path_to_endpoint_shared,
                "type": "guest",
            },
        ],
    }

    globus_plugin = globus.Globus()
    globus_plugin.configure(configuration)

    # action items in the list should be executed in order
    ESNET_GLOBUS_ENDPOINT_UUID = "ece400da-0182-4777-91d6-27a1808f8371"

    # This is so that we can run the test both as a runner and as user
    sub_folder = ""
    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
        sub_folder = "/runner"

    package = [
        {
            "transfer": {
                "source_collection_UUID": ESNET_GLOBUS_ENDPOINT_UUID,
                "destination_collection_UUID": os.getenv(required_env_variables[2]),
                "type": "synchronous",
                "items": [
                    {
                        "source": {"type": "globus relative", "path": "/1M.dat"},
                        "destination": {
                            "type": "globus relative",
                            "path": sub_folder + "/1M.dat",
                        },
                    }
                ],
            }
        }
    ]

    # This test is designed to move a file to the globus endpoint
    # So before we get started we are going to make sure that a file
    # does not already exist at that location
    abs_path_destination = (
        path_to_endpoint
        + sub_folder
        + '/1M.dat'
    )

    if os.path.exists(abs_path_destination):
        os.remove(abs_path_destination)

    if globus_plugin.check(package):
        result = globus_plugin.process(package)

    # After processing we should verify that the file exists at the final location
    assert os.path.exists(abs_path_destination)


def test_globus_process_async():

    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    path_to_endpoint = "/home/cades/Collections/default"
    path_to_endpoint_shared = "/home/cades/Collections/default/shared"

    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {
            "type": "client credential",
            "secret": os.getenv(required_env_variables[1]),
        },
        "collections": [
            {
                "UUID": os.getenv(required_env_variables[2]),
                "path": path_to_endpoint,
                "type": "mapped",
            },
            {
                "UUID": os.getenv(required_env_variables[3]),
                "path": path_to_endpoint_shared,
                "type": "guest",
            },
        ],
    }

    globus_plugin = globus.Globus()
    globus_plugin.configure(configuration)

    # Create a file on the local posix system
    file_name = "demofile_for_globus1.txt"
    f = open(file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    relative_destination_file_path = "/"
    sub_folder = ""
    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
        sub_folder = "runner/"
    # action items in the list should be executed in order
    package = [
        {
            "move_to_globus_collection": {
                "destination_collection_UUID": os.getenv(required_env_variables[2]),
                "source_host_name": socket.gethostname(),
                "items": [
                    {
                        "source": {"type": "posix absolute", "path": file_path},
                        "destination": {
                            "type": "globus relative",
                            "path": relative_destination_file_path + sub_folder,
                        },
                    }
                ],
            }
        },
        {
            "transfer": {
                "source_collection_UUID": os.getenv(required_env_variables[2]),
                "destination_collection_UUID": os.getenv(required_env_variables[3]),
                "type": "asynchronous",
                "items": [
                    {
                        "source": {
                            "type": "globus relative",
                            "path": "/" + sub_folder + file_name,
                        },
                        "destination": {
                            "type": "globus relative",
                            "path": relative_destination_file_path
                            + sub_folder
                            + file_name,
                        },
                    }
                ],
            }
        },
    ]

    abs_path_destination = path_to_endpoint + sub_folder + file_name

    if os.path.exists(abs_path_destination):
        os.remove(abs_path_destination)

    output = globus_plugin.check(package)
    if output["transfer"][0]:
        globus_plugin.process(package)
    else:
        print("Check failed no transfer was conducted.")
        print(output["transfer"][1])

    # After processing we should verify that the file exists at the final location
    assert os.path.exists(abs_path_destination)
    abs_path_destination = (
        path_to_endpoint
        + relative_destination_file_path
        + sub_folder
        + os.path.basename(file_path)
    )
    # After it gets transferred using globus it should end up moving to the subfolder
    abs_path_destination_shared = (
        path_to_endpoint
        + relative_destination_file_path
        + "shared/"
        + sub_folder
        + os.path.basename(file_path)
    )
    if os.path.exists(abs_path_destination):
        os.remove(abs_path_destination)
    if os.path.exists(abs_path_destination_shared):
        os.remove(abs_path_destination_shared)

    if globus_plugin.check(package):
        result = globus_plugin.process(package)

        result = globus_plugin.process([result["transfer"]["callback"]])
        while result["get_task_status"]["result"]["status"] != "SUCCEEDED":
            print("waiting...")
            time.sleep(1)
            result = globus_plugin.process([result["get_task_status"]["callback"]])

        print("complete")
        print(result["get_task_status"])
    # After processing we should verify that the file exists at the final location
    assert os.path.exists(abs_path_destination_shared)
