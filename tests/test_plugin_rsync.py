# Local imports
import zambeze.orchestration.plugin_modules.rsync.rsync as rsync

# Standard imports
import os
import pytest
import random
import socket


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
