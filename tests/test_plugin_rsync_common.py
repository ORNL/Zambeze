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

    host = "destination"

    fields_valid = requiredSourceAndDestinationValuesValid(package, host)
    print(fields_valid)
    assert fields_valid[0]

    # Lets pass in an invalid ip address
    package = Endpoints(
        RsyncItem("127.0..1", "/home/john/folder1", "john"),
        RsyncItem(local_ip, current_valid_path, current_user),
    )

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

    fields_valid = validateRequiredSourceAndDestinationValuesValid(package)
    assert fields_valid[0]

    # Lets pass in an invalid ip address
    package = Endpoints(
        RsyncItem("127.0..1", "/home/john/folder1", "john"),
        RsyncItem(local_ip, current_valid_path, current_user),
    )

    # This method does not check the ip address only that the fields are present
    fields_valid = validateRequiredSourceAndDestinationValuesValid(package)
    assert fields_valid[0] is False
