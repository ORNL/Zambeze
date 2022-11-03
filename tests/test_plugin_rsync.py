# Local imports
import zambeze.orchestration.plugin_modules.rsync.rsync as rsync

# Standard imports
import os
import pwd
import pytest
import random
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
    assert fields_exist[0]

    package2 = {"ip2": "something", "user": "a user", "path": "a path to a file"}

    fields_exist = rsync.requiredEndpointKeysExist(package2)
    assert fields_exist[0] is False

    package3 = {"ip": "something", "user_s": "a user", "path": "a path to a file"}

    fields_exist = rsync.requiredEndpointKeysExist(package3)
    assert fields_exist[0] is False

    package4 = {"ip": "something", "user": "a user", "pat": "a path to a file"}

    fields_exist = rsync.requiredEndpointKeysExist(package4)
    assert fields_exist[0] is False


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
    assert fields_exist[0]

    package = {
        "destination": {"ip": "something", "user": "a user", "path": "a path to a file"}
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist[0] is False

    package = {
        "source": {"ip": "something", "user": "a user", "path": "a path to a file"}
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist[0] is False


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
    assert fields_valid[0]

    # Lets pass in an invalid ip address
    package = {
        "source": {"ip": "127.0..1", "user": "john", "path": "/home/john/folder1"},
        "destination": {
            "ip": local_ip,
            "user": current_user,
            "path": current_valid_path,
        },
    }
    # This method does not check the ip address only that the fields are present
    fields_valid = rsync.requiredSourceAndDestinationValuesValid(package, host)
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
    package = {
        "source": {"ip": "127.0.0.1", "user": "john", "path": "/home/john/folder1"},
        "destination": {
            "ip": local_ip,
            "user": current_user,
            "path": current_valid_path,
        },
    }

    host = "destination"

    fields_valid = rsync.validateRequiredSourceAndDestinationValuesValid(package, host)
    assert fields_valid[0]

    # Lets pass in an invalid ip address
    package = {
        "source": {"ip": "127.0..1", "user": "john", "path": "/home/john/folder1"},
        "destination": {
            "ip": local_ip,
            "user": current_user,
            "path": current_valid_path,
        },
    }
    # This method does not check the ip address only that the fields are present
    fields_valid = rsync.validateRequiredSourceAndDestinationValuesValid(package, host)
    assert fields_valid[0] is False


@pytest.mark.unit
def test_rsync_messageTemplate():

    instance = rsync.Rsync()
    rsync_template = instance.messageTemplate()

    assert "plugin" in rsync_template
    assert rsync_template["plugin"] == instance.name
    assert "cmd" in rsync_template
    assert "transfer" in rsync_template["cmd"][0]
    assert "source" in rsync_template["cmd"][0]["transfer"]
    assert "destination" in rsync_template["cmd"][0]["transfer"]


@pytest.mark.unit
def test_rsync_messageTemplate_and_validate():

    instance = rsync.Rsync()
    rsync_template = instance.messageTemplate()
    checks = instance.validateMessage(rsync_template["cmd"])
    assert len(checks) == 1
    assert checks[0]["transfer"] 


@pytest.mark.unit
def test_rsync():
    instance = rsync.Rsync()

    assert instance.name == "rsync"

    assert not instance.configured

    file_name = "dummy_ssh"
    f = open(file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    assert len(instance.supportedActions) == 0

    config = {"private_ssh_key": file_path}

    instance.configure(config)
    assert instance.configured

    assert len(instance.supportedActions) == 1
    assert "transfer" in instance.supportedActions

    assert instance.info["configured"]
    assert instance.info["supported_actions"][0] == "transfer"

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    assert instance.info["local_ip"] == local_ip
