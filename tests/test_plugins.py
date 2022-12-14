# Local imports
from zambeze.orchestration.plugins import Plugins
from zambeze.orchestration.plugins_message_template_engine import (
    PluginsMessageTemplateEngine
)
from zambeze.orchestration.plugins_message_validator import PluginsMessageValidator
from zambeze.orchestration.message.message_factory import MessageFactory

# Standard imports
import copy
import os
import pwd
import pytest

import random
import socket
import time


@pytest.mark.unit
def test_registered_plugins():
    """Test checks that you can get a list of all the registered plugins"""
    plugins = Plugins()
    found_shell = False
    found_rsync = False
    found_globus = False
    for plugin in plugins.registered:
        if plugin == "shell":
            found_shell = True
        elif plugin == "rsync":
            found_rsync = True
        elif plugin == "globus":
            found_globus = True

    assert found_shell
    assert found_rsync
    assert found_globus


@pytest.mark.unit
def test_check_configured_plugins():

    plugins = Plugins()

    assert len(plugins.configured) == 0

    configuration = {"shell": {}}
    #            "globus": {
    #                "authentication flow": {
    #                    "type": "client credential",
    #                    "secret": os.getenv("ZAMBEZE_CI_TEST_GLOBUS_APP_KEY")
    #                    }
    #                }
    #            }
    #
    plugins.configure(configuration)

    assert len(plugins.configured) > 0


@pytest.mark.unit
def test_rsync_plugin():
    plugins = Plugins()
    assert "rsync" not in plugins.configured
    # Only rsync should be configured
    plugins.configure({"rsync": {}})
    assert "rsync" in plugins.configured
    assert len(plugins.configured) == 1


@pytest.mark.unit
def test_rsync_plugin_info():
    plugins = Plugins()
    # Only rsync should be configured
    plugins.configure({"rsync": {}})

    info = plugins.info

    assert info["rsync"]["configured"]
    assert info["rsync"]["supported_actions"][0] == "transfer"

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    assert info["rsync"]["local_ip"] == local_ip


@pytest.mark.gitlab_runner
def test_rsync_plugin_check():
    plugins = Plugins()
    plugins.configure({"shell": {}, "rsync": {}})
    # ,
    # "rsync": {}})

    # Grab valid paths, usernames and ip addresses
    current_valid_path = os.getcwd()
    current_user = pwd.getpwuid(os.geteuid())[0]
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    neighbor_vm_ip = os.getenv("ZAMBEZE_CI_TEST_RSYNC_IP")

    template_engine = PluginsMessageTemplateEngine()
    msg_template = template_engine.generate("rsync", "transfer")

    msg_template.transfer.items[0].source.ip = local_ip
    msg_template.transfer.items[0].source.user = current_user
    msg_template.transfer.items[0].source.path = current_valid_path
    msg_template.transfer.items[0].destination.ip = neighbor_vm_ip
    msg_template.transfer.items[0].destination.user = "cades"
    msg_template.transfer.items[0].destination.path = "/tmp"
    #    arguments = {
    #        "transfer": {
    #            "source": {
    #                "ip": local_ip,
    #                "user": current_user,
    #                "path": current_valid_path,
    #            },
    #            "destination": {"ip": neighbor_vm_ip, "user": "cades", "path": "/tmp"},
    #            "arguments": ["-a"],
    #        }
    #    }

    checked_actions = plugins.check(msg_template)
    print(checked_actions)
    assert checked_actions["rsync"][0]["transfer"][0]
    msg_faulty_ip = copy.deepcopy(msg_template)
    msg_faulty_ip.transfer.destination.ip = "172.22."
    checked_actions = plugins.check(msg_faulty_ip)
    print(checked_actions)
    assert not checked_actions["rsync"][0]["transfer"][0]

    msg_faulty_user = copy.deepcopy(msg_template)
    msg_faulty_user.transfer.source.user = "user_that_does_not_exist"
    checked_actions = plugins.check("rsync", msg_faulty_user)
    print(checked_actions)
    assert not checked_actions["rsync"][0]["transfer"][0]


@pytest.mark.gitlab_runner
def test_rsync_plugin_run():
    """This test is designed to test the rsync plugin plugin

    A few special points, there are a few environmental variables that
    must be defined to run this test successfully:

    ZAMBEZE_CI_TEST_RSYNC_SSH_KEY

    This represents the path to the private ssh key that the test has
    access to. For the test to work the public key must have already
    been copied over to the other machine.

    ZAMBEZE_CI_TEST_RSYNC_IP

    This env variable contains the ip address of the machine that rsync
    is being tested with. The public rsa key must have already been
    added to that machines authorized_keys.

    Once those env variables are defined the tests can be run with.

    python3 -m pytest -m gitlab_runner
    """
    plugins = Plugins()

    neighbor_vm_ip = os.getenv("ZAMBEZE_CI_TEST_RSYNC_IP")
    path_to_ssh_key = os.getenv("ZAMBEZE_CI_TEST_RSYNC_SSH_KEY")
    plugins.configure({"rsync": {"private_ssh_key": path_to_ssh_key}})

    # Attaching a timestamp to avoid concurrent runs overwriting files
    file_name = "demofile-" + str(time.time_ns()) + ".txt"
    f = open(file_name, "w")
    random.seed(time.time())
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()
    print(f"\nOriginal number is {original_number}")
    # Grab valid paths, usernames and ip addresses
    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    current_user = pwd.getpwuid(os.geteuid())[0]
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    template_engine = PluginsMessageTemplateEngine()
    msg_template = template_engine.generate("rsync", "transfer")

    msg_template.transfer.items[0].source.ip = local_ip
    msg_template.transfer.items[0].source.user = current_user
    msg_template.transfer.items[0].source.path = file_path
    msg_template.transfer.items[0].destination.ip = neighbor_vm_ip
    msg_template.transfer.items[0].destination.user = "cades"
    msg_template.transfer.items[0].destination.path = "/tmp"

    #    arguments = {
    #        "transfer": {
    #            "source": {"ip": local_ip, "user": current_user, "path": file_path},
    #            "destination": {"ip": neighbor_vm_ip, "user": "cades", "path": "/tmp"},
    #            "arguments": ["-a"],
    #        }
    #    }

    print("Arguments: Initial transfer to remote machine")
    print(msg_template)
    checks = plugins.check(msg_template)
    assert checks["rsync"][0]["transfer"][0]
    plugins.run(msg_template)

    file_name_return = "demofile_return-" + str(time.time_ns()) + ".txt"
    file_path_return = current_valid_path + "/" + file_name_return

    # Remove local copy of file if it already exists
    if os.path.exists(file_path_return):
        os.remove(file_path_return)

    template_engine = PluginsMessageTemplateEngine()
    msg_template_return = template_engine.generate("rsync", "transfer")

    msg_template_return.transfer.items[0].source.ip = local_ip
    msg_template_return.transfer.items[0].source.user = current_user
    msg_template_return.transfer.items[0].source.path = file_path_return
    msg_template_return.transfer.items[0].destination.ip = neighbor_vm_ip
    msg_template_return.transfer.items[0].destination.user = "cades"
    msg_template_return.transfer.items[0].destination.path = "/tmp/" + file_name

    #    arguments_return = {
    #        "transfer": {
    #            "destination": {
    #                "ip": local_ip,
    #                "user": current_user,
    #                "path": file_path_return,
    #            },
    #            "source": {
    #                "ip": neighbor_vm_ip,
    #                "user": "cades",
    #                "path": "/tmp" + "/" + file_name,
    #            },
    #            "arguments": ["-a"],
    #        }
    #    }

    print("Arguments: Second transfer back to host machine")
    print(msg_template_return)
    checked_actions = plugins.check(msg_template_return)
    assert checked_actions["rsync"][0]["transfer"][0]
    attempts = 0
    # Loop is needed because sometimes the initial transfer takes a while to
    # finalize, this loop will make the test more robust.
    while True:
        plugins.run(msg_template_return)
        # This will verify that copying from a remote machine to the local
        # machine was a success
        assert os.path.exists(file_path_return)

        with open(file_path_return) as f:
            # Now we will verify that it is the same file that was sent
            lines = f.readlines()
            # Should be a single line
            random_int = int(lines[0])

        if random_int == original_number:
            break
        if attempts == 10:
            break
        attempts += 1
        time.sleep(1)
    assert random_int == original_number
