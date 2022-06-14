# Local imports
import zambeze.orchestration.plugin_modules.globus as globus

# Standard imports
import os
import pwd
import pytest
import random
import socket

@pytest.mark.globus
def test_globus_basic1():
    globus_plugin = globus.Globus()

    assert globus_plugin.name == "globus"
    assert globus_plugin.configured == False

    """Requires that the env variable is provided"""
    configuration = {
        "globus_app_id": "435D07FA-8B10-4E04-B005-054C68BE3F14",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY")
        }
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
        "globus_app_id": "435D07FA-8B10-4E04-B005-054C68BE3F14",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY")
        },
        "collections": [
            {
                "UUID": "57281195-1495-4995-a777-52bd5d16ee7e",
                "path": "/home/cades/Collections/default"
            }
        ]
    }

    globus_plugin.configure(configuration)

    assert len(globus_plugin.supportedActions) == 3

@pytest.mark.globus
def test_globus_move_check():
    configuration = {
        "globus_app_id": "435D07FA-8B10-4E04-B005-054C68BE3F14",
        "authentication flow": {
            "type": "client credential",
            "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY")
        },
        "collections": [
            {
                "UUID": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"),
                "path": "/home/cades/Collections/default"
            }
        ]
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

    package = {
        "move_to_globus_collection": {
            "destination_collection_UUID": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID"),
            "source_host_name": socket.gethostname(),
            "items": [
                {
                    "source": {
                        "type": "posix absolute",
                        "path": file_path
                        },
                    "destination": {
                        "type": "globus relative",
                        "path": "/"
                        }
                }
            ]
        }
    }

    assert globus_plugin.check(package)
