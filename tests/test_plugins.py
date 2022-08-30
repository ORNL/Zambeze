# Local imports
from zambeze.orchestration.plugins import Plugins

# Standard imports
import copy
import os
import pwd
import pytest

import random
import socket


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
    plugins.configure({"shell": {}})

    # Grab valid paths, usernames and ip addresses
    current_valid_path = os.getcwd()
    current_user = pwd.getpwuid(os.geteuid())[0]
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    arguments = {
        "transfer": {
            "source": {
                "ip": local_ip,
                "user": current_user,
                "path": current_valid_path,
            },
            "destination": {
                "ip": "172.22.1.69",
                "user": "cades",
                "path": "/home/cades/josh-testing",
            },
            "arguments": ["-a"],
        }
    }

    checked_actions = plugins.check("rsync", arguments)
    assert checked_actions["rsync"]["transfer"]

    arguments_faulty_ip = copy.deepcopy(arguments)
    arguments_faulty_ip["transfer"]["destination"]["ip"] = "172.22."
    checked_actions = plugins.check("rsync", arguments_faulty_ip)
    assert not checked_actions["rsync"]["transfer"]

    arguments_faulty_user = copy.deepcopy(arguments)
    arguments_faulty_user["transfer"]["source"]["user"] = "user_that_does_not_exist"
    checked_actions = plugins.check("rsync", arguments_faulty_user)
    assert not checked_actions["rsync"]["transfer"]


@pytest.mark.gitlab_runner
def test_rsync_plugin_run():
    """This test is designed to test the rsync plugin plugin

    A few special points, there are a few environmental variables that
    must be defiend to run this test successfully:

    ZAMBEZE_CI_TEST_RSYNC_SSH_KEY

    This represents the path to the private ssh key that the test has
    access to. For the test to work the public key must have already
    been copied over to the other machine used in the test with ip
    address "172.22.1.69" and added to that machines authorized_keys
    file

    If you want to run the test interactively you can log into the
    machine at ip address 172.22.1.68 and run

    python3 -m pytest -m gitlab_runner
    """
    plugins = Plugins()
    path_to_ssh_key = os.getenv("ZAMBEZE_CI_TEST_RSYNC_SSH_KEY")
    plugins.configure({"rsync": {"private_ssh_key": path_to_ssh_key}})

    file_name = "demofile.txt"
    f = open(file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    # Grab valid paths, usernames and ip addresses
    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    current_user = pwd.getpwuid(os.geteuid())[0]
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    arguments = {
        "transfer": {
            "source": {"ip": local_ip, "user": current_user, "path": file_path},
            "destination": {
                "ip": "172.22.1.69",
                "user": "cades",
                "path": "/home/cades/josh-testing",
            },
            "arguments": ["-a"],
        }
    }

    print("Arguments: Initial transfer to remote machine")
    print(arguments)
    assert plugins.check("rsync", arguments)
    plugins.run("rsync", arguments)

    file_path_return = current_valid_path + "/demofile_return.txt"

    # Remove local copy of file if it already exists
    if os.path.exists(file_path_return):
        os.remove(file_path_return)

    arguments_return = {
        "transfer": {
            "destination": {
                "ip": local_ip,
                "user": current_user,
                "path": file_path_return,
            },
            "source": {
                "ip": "172.22.1.69",
                "user": "cades",
                "path": "/home/cades/josh-testing" + "/" + file_name,
            },
            "arguments": ["-a"],
        }
    }

    print("Arguments: Second transfer back to host machine")
    print(arguments_return)
    checked_actions = plugins.check("rsync", arguments_return)
    assert checked_actions["rsync"]["transfer"]
    plugins.run("rsync", arguments_return)
    # This will verify that copying from a remote machine to the local
    # machine was a success
    assert os.path.exists(file_path_return)

    with open(file_path_return) as f:
        # Now we will verify that it is the same file that was sent
        lines = f.readlines()
        # Should be a single line
        random_int = int(lines[0])
        assert random_int == original_number
