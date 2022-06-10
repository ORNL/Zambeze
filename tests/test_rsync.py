# Local imports
import zambeze.orchestration.plugin_modules.rsync as rsync

# Standard imports
import os
import pwd
import pytest
import socket


@pytest.mark.unit
def test_rsync_requiredEndpointKeysExist():
    """This tests an auxillary helper function

    The function is designed to make sure that the following
    keys are present in the python dict: "ip", "user" and "path".
    If they are present the function should return True if one of
    them is absent then should return False.
    """
    package = {"ip": "something", "user": "a user", "path": "a path to a file"}

    fields_exist = rsync.requiredEndpointKeysExist(package)
    assert fields_exist

    package2 = {"ip2": "something", "user": "a user", "path": "a path to a file"}

    fields_exist = rsync.requiredEndpointKeysExist(package2)
    assert fields_exist is False

    package3 = {"ip": "something", "user_s": "a user", "path": "a path to a file"}

    fields_exist = rsync.requiredEndpointKeysExist(package3)
    assert fields_exist is False

    package4 = {"ip": "something", "user": "a user", "pat": "a path to a file"}

    fields_exist = rsync.requiredEndpointKeysExist(package4)
    assert fields_exist is False


@pytest.mark.unit
def test_rsync_requiredSourceAndDestinationKeysExist():
    """Tests one of the assistant functions

    The test ensures that the correct keys are present. If they are present
    returns True if they aren't it returns False
    """
    package = {
        "source": {"ip": "something", "user": "a user", "path": "a path to a file"},
        "destination": {
            "ip": "something",
            "user": "a user",
            "path": "a path to a file",
        },
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist

    package = {
        "destination": {"ip": "something", "user": "a user", "path": "a path to a file"}
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist is False

    package = {
        "source": {"ip": "something", "user": "a user", "path": "a path to a file"}
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist is False


@pytest.mark.unit
def test_rsync_requiredSourceAndDestinationValuesValid():
    """Tests one of the assistant functions

    The test ensures that the values passed in are valid. If they are present
    returns True if they aren't it returns False. Either the "source" or
    "destination" endpoint must refer to the host machine.
    """

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    current_valid_path = os.getcwd()
    current_user = pwd.getpwuid(os.geteuid())[0]
    package = {
        "source": {"ip": "127.0.0.1", "user": "john", "path": "/home/john/folder1"},
        "destination": {
            "ip": local_ip,
            "user": current_user,
            "path": current_valid_path,
        },
    }

    host = "destination"

    fields_valid = rsync.requiredSourceAndDestinationValuesValid(package, host)
    assert fields_valid

    # Lets pass in an invalid ip address
    package = {
        "source": {"ip": "127.0..1", "user": "john", "path": "/home/john/folder1"},
        "destination": {
            "ip": local_ip,
            "user": current_user,
            "path": current_valid_path,
        },
    }
    fields_valid = rsync.requiredSourceAndDestinationValuesValid(package, host)
    assert fields_valid is False
