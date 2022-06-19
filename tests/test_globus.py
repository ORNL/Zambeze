# Local imports
import zambeze.orchestration.plugin_modules.globus as globus

# Standard imports
import os
import pytest
import random
import socket


@pytest.mark.globus
def test_globus_basic1():
    globus_plugin = globus.Globus()

    assert globus_plugin.name == "globus"
    assert globus_plugin.configured is False

    """Requires that the env variable is provided"""
    configuration = {
        "client id": "ea43a708-b182-4f22-b5a1-019cc56876d1",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY"),
        },
    }

    globus_plugin.configure(configuration)

    assert globus_plugin.configured

    assert len(globus_plugin.supportedActions) == 1
    # We assume that we at least have access to the globus cloud
    assert "transfer" in globus_plugin.supportedActions


@pytest.mark.globus
def test_globus_basic2():
    globus_plugin = globus.Globus()

    """Requires that the env variable is provided

    A valid globus collection must also exist on this machine
    in order for the move to globus endpoint and move from
    globus endpoint to local posix file system to work."""
    configuration = {
        "client id": "ea43a708-b182-4f22-b5a1-019cc56876d1",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY"),
        },
        "collections": [
            {
                "UUID": "57281195-1495-4995-a777-52bd5d16ee7e",
                "path": "/home/cades/Collections/default",
                "type": "mapped",
            }
        ],
    }

    globus_plugin.configure(configuration)

    assert len(globus_plugin.supportedActions) == 3


@pytest.mark.globus
def test_globus_move_check():
    configuration = {
        "client id": "ea43a708-b182-4f22-b5a1-019cc56876d1",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY"),
        },
        "collections": [
            {
                "UUID": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"),
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

    package = [
        {
            "move_to_globus_collection": {
                "destination_collection_UUID": os.getenv(
                    "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"
                ),
                "source_host_name": socket.gethostname(),
                "items": [
                    {
                        "source": {"type": "posix absolute", "path": file_path},
                        "destination": {"type": "globus relative", "path": "/"},
                    }
                ],
            }
        }
    ]

    assert globus_plugin.check(package)


@pytest.mark.globus
def test_globus_transfer_check():
    configuration = {
        "client id": "ea43a708-b182-4f22-b5a1-019cc56876d1",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY"),
        },
        "collections": [
            {
                "UUID": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"),
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

    package = [
        {
            "move_to_globus_collection": {
                "destination_collection_UUID": os.getenv(
                    "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"
                ),
                "source_host_name": socket.gethostname(),
                "items": [
                    {
                        "source": {"type": "posix absolute", "path": file_path},
                        "destination": {"type": "globus relative", "path": "/"},
                    }
                ],
            }
        },
        {
            "transfer": {
                "source_collection_UUID": os.getenv(
                    "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"
                ),
                "destination_collection_UUID": os.getenv(
                    "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID"
                ),
                "type": "synchronous",
                "items": [
                    {
                        "source": {"type": "globus relative", "path": "/" + file_name},
                        "destination": {
                            "type": "globus relative",
                            "path": "/" + file_name,
                        },
                    }
                ],
            }
        },
    ]
    assert globus_plugin.check(package)


@pytest.mark.globus
def test_globus_process():

    path_to_endpoint = "/home/cades/Collections/default"
    path_to_endpoint_shared = "/home/cades/Collections/default/shared"

    configuration = {
        "client id": "ea43a708-b182-4f22-b5a1-019cc56876d1",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY"),
        },
        "collections": [
            {
                "UUID": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"),
                "path": path_to_endpoint,
                "type": "mapped",
            },
            {
                "UUID": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID"),
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

    # action items in the list should be executed in order
    package = [
        {
            "move_to_globus_collection": {
                "destination_collection_UUID": os.getenv(
                    "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"
                ),
                "source_host_name": socket.gethostname(),
                "items": [
                    {
                        "source": {"type": "posix absolute", "path": file_path},
                        "destination": {
                            "type": "globus relative",
                            "path": relative_destination_file_path,
                        },
                    }
                ],
            }
        },
        {
            "transfer": {
                "source_collection_UUID": os.getenv(
                    "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"
                ),
                "destination_collection_UUID": os.getenv(
                    "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID"
                ),
                "type": "synchronous",
                "items": [
                    {
                        "source": {"type": "globus relative", "path": "/" + file_name},
                        "destination": {
                            "type": "globus relative",
                            "path": "/" + file_name,
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
        path_to_endpoint + relative_destination_file_path + os.path.basename(file_path)
    )
    # After it gets transferred using globus it should end up moving to the subfolder
    abs_path_destination_shared = (
        path_to_endpoint
        + relative_destination_file_path
        + "shared/"
        + os.path.basename(file_path)
    )
    if os.path.exists(abs_path_destination):
        os.remove(abs_path_destination)
    if os.path.exists(abs_path_destination_shared):
        os.remove(abs_path_destination_shared)

    if globus_plugin.check(package):
        globus_plugin.process(package)

    # After processing we should verify that the file exists at the final location
    assert os.path.exists(abs_path_destination_shared)
