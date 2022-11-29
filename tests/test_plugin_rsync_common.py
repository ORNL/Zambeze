# Local imports
from zambeze.orchestration.plugin_modules.rsync.rsync_common import (
    requiredSourceAndDestinationValuesValid,
    validateRequiredSourceAndDestinationValuesValid,
)
from zambeze.orchestration.plugin_modules.common_dataclasses import RsyncItem, Endpoints

# Standard imports
import os
import pwd
import pytest
import socket


# @pytest.mark.unit
# def test_rsync_requiredEndpointKeysExist():
#    """This tests an auxillary helper function
#
#    The function is designed to make sure that the following
#    keys are present in the python dict: "ip", "user" and "path".
#    If they are present the function should return True if one of
#    them is absent then should return False.
#    """
#    package = RsyncItem("something", "a user", "a path to file"),
##    package = {"ip": "something", "user": "a user", "path": "a path to a file"}
#
#    fields_exist = requiredEndpointKeysExist(package)
#    assert fields_exist[0]
#
#    package2 = {"ip2": "something", "user": "a user", "path": "a path to a file"}
#
#    fields_exist = requiredEndpointKeysExist(package2)
#    assert fields_exist[0] is False
#
#    package3 = {"ip": "something", "user_s": "a user", "path": "a path to a file"}
#
#    fields_exist = requiredEndpointKeysExist(package3)
#    assert fields_exist[0] is False
#
#    package4 = {"ip": "something", "user": "a user", "pat": "a path to a file"}
#
#    fields_exist = requiredEndpointKeysExist(package4)
#    assert fields_exist[0] is False


# @pytest.mark.unit
# def test_rsync_requiredSourceAndDestinationKeysExist():
#    """Tests one of the assistant functions
#
#    The test ensures that the correct keys are present. If they are present
#    returns True if they aren't it returns False
#    """
#    package = Endpoints(
#            RsyncItem("something", "a user", "a path to fill"),
#            RsyncItem("something", "a user", "a path to fill")
#            )
#    package = {
#        "source": {"ip": "something", "user": "a user", "path": "a path to a file"},
#        "destination": {
#            "ip": "something",
#            "user": "a user",
#            "path": "a path to a file",
#        },
#    }
#
#    fields_exist = requiredSourceAndDestinationKeysExist(package)
#    assert fields_exist[0]
#
#    package = Endpoints(
#            RsyncItem("something", "a user", "a path to fill"),
#            RsyncItem("something", "a user", "a path to fill")
#            )
# package = {
# "destination": {"ip": "something", "user": "a user", "path": "a path to a file"}
# }
#
#    fields_exist = requiredSourceAndDestinationKeysExist(package)
#    assert fields_exist[0] is False
#
#    package = Endpoints(
#            RsyncItem("something", "a user", "a path to fill"),
#            RsyncItem("something", "a user", "a path to fill")
#            )
# package = {
# "source": {"ip": "something", "user": "a user", "path": "a path to a file"}
# }
#
#    fields_exist = requiredSourceAndDestinationKeysExist(package)
#    assert fields_exist[0] is False


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

    package = Endpoints(
        RsyncItem("127.0.0.1", "/home/john/folder1", "john"),
        RsyncItem(local_ip, current_valid_path, current_user),
    )
    #    package = {
    #        "source": {"ip": "127.0.0.1", "user": "john", "path": "/home/john/folder1"},
    #        "destination": {
    #            "ip": local_ip,
    #            "user": current_user,
    #            "path": current_valid_path,
    #        },
    #    }

    host = "destination"

    fields_valid = requiredSourceAndDestinationValuesValid(package, host)
    print(fields_valid)
    assert fields_valid[0]

    # Lets pass in an invalid ip address
    package = Endpoints(
        RsyncItem("127.0..1", "/home/john/folder1", "john"),
        RsyncItem(local_ip, current_valid_path, current_user),
    )
    #    package = {
    #        "source": {"ip": "127.0..1", "user": "john", "path": "/home/john/folder1"},
    #        "destination": {
    #            "ip": local_ip,
    #            "user": current_user,
    #            "path": current_valid_path,
    #        },
    #    }
    # This method does not check the ip address only that the fields are present
    fields_valid = requiredSourceAndDestinationValuesValid(package, host)
    assert fields_valid[0] is True


@pytest.mark.unit
def test_rsync_validateRequiredSourceAndDestinationValuesValid():
    """Tests one of the assistant functions

    The test ensures that the values passed in are valid. If they are present
    returns True if they aren't it returns False. Either the "source" or
    "destination" endpoint must refer to the host machine.
    """

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    current_valid_path = os.getcwd()
    current_user = pwd.getpwuid(os.geteuid())[0]

    package = Endpoints(
        RsyncItem("127.0.0.1", "/home/john/folder1", "john"),
        RsyncItem(local_ip, current_valid_path, current_user),
    )

    #    package = {
    #        "source": {"ip": "127.0.0.1", "user": "john", "path": "/home/john/folder1"},
    #        "destination": {
    #            "ip": local_ip,
    #            "user": current_user,
    #            "path": current_valid_path,
    #        },
    #    }

    fields_valid = validateRequiredSourceAndDestinationValuesValid(package)
    assert fields_valid[0]

    # Lets pass in an invalid ip address
    package = Endpoints(
        RsyncItem("127.0..1", "/home/john/folder1", "john"),
        RsyncItem(local_ip, current_valid_path, current_user),
    )
    #    package = {
    #        "source": {"ip": "127.0..1", "user": "john", "path": "/home/john/folder1"},
    #        "destination": {
    #            "ip": local_ip,
    #            "user": current_user,
    #            "path": current_valid_path,
    #        },
    #    }
    # This method does not check the ip address only that the fields are present
    fields_valid = validateRequiredSourceAndDestinationValuesValid(package)
    assert fields_valid[0] is False
