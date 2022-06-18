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
    for plugin in plugins.registered:
        if plugin == "shell":
            found_shell = True
        elif plugin == "rsync":
            found_rsync = True

    assert found_shell
    assert found_rsync


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
    assert info["rsync"]["supported actions"][0] == "transfer"

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    assert info["rsync"]["local ip"] == local_ip


@pytest.mark.unit
def test_rsync_plugin_check():
    plugins = Plugins()
    plugins.configure({"shell": {}})

    # Grab valid paths, usernames and ip addresses
    current_valid_path = os.getcwd()
    current_user = pwd.getpwuid(os.geteuid())[0]
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    arguments = {
        "rsync": [
            {
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
        ]
    }

    assert plugins.check(arguments)["rsync"]["transfer"]

    arguments_faulty_ip = copy.deepcopy(arguments)
    arguments_faulty_ip["rsync"][0]["transfer"]["destination"]["ip"] = "172.22."
    assert not plugins.check(arguments_faulty_ip)["rsync"]["transfer"]
    arguments_faulty_user = copy.deepcopy(arguments)
    arguments_faulty_user["rsync"][0]["transfer"]["source"][
        "user"
    ] = "user_that_does_not_exist"
    assert not plugins.check(arguments_faulty_user)["rsync"]["transfer"]


@pytest.mark.gitlab_runner
def test_rsync_plugin_run():
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
        "rsync": [
            {
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
        ]
    }

    print("Arguments: Initial transfer to remote machine")
    print(arguments)
    plugins.run(arguments)
    file_path_return = current_valid_path + "/demofile_return.txt"

    # Remove local copy of file if it already exists
    if os.path.exists(file_path_return):
        os.remove(file_path_return)

    arguments_return = {
        "rsync": [
            {
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
        ]
    }

    print("Arguments: Second transfer back to host machine")
    print(arguments_return)
    plugins.run(arguments_return)
    # This will verify that copying from a remote machine to the local
    # machine was a success
    assert os.path.exists(file_path_return)

    with open(file_path_return) as f:
        # Now we will verify that it is the same file that was sent
        lines = f.readlines()
        # Should be a single line
        random_int = int(lines[0])
        assert random_int == original_number

