# Local imports
from zambeze.orchestration.services import Services

# Standard imports
import copy
import os
import pwd
import pytest
import random
import socket


@pytest.mark.unit
def test_registered_services():
    """Test simply checks that you can get a list of all the registered services
    """
    services = Services()
    found_shell = False
    found_rsync = False
    for service in services.registered:
        if service == "shell":
            found_shell = True
        elif service == "rsync":
            found_rsync = True

    assert found_shell
    assert found_rsync


@pytest.mark.unit
def test_check_configured_services():

    services = Services()

    assert len(services.configured) == 0

    configuration = {"shell": {}}

    services.configure(configuration)

    assert len(services.configured) > 0


@pytest.mark.unit
def test_rsync_service():
    services = Services()
    assert "rsync" not in services.configured
    # Only rsync should be configured
    services.configure({}, ["rsync"])
    assert "rsync" in services.configured
    assert len(services.configured) == 1


@pytest.mark.unit
def test_rsync_service_info():
    services = Services()
    # Only rsync should be configured
    services.configure({}, ["rsync"])

    info = services.info

    assert info["rsync"]["configured"]
    assert info["rsync"]["supported actions"][0] == "transfer"

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    assert info["rsync"]["local ip"] == local_ip


@pytest.mark.unit
def test_rsync_service_check():
    services = Services()
    services.configure({})

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

    assert services.check(arguments)["rsync"]["transfer"]

    arguments_faulty_ip = copy.deepcopy(arguments)
    arguments_faulty_ip["rsync"][0]["transfer"]["destination"]["ip"] = "172.22."
    assert not services.check(arguments_faulty_ip)["rsync"]["transfer"]
    arguments_faulty_user = copy.deepcopy(arguments)
    arguments_faulty_user["rsync"][0]["transfer"]["source"][
        "user"
    ] = "user_that_does_not_exist"
    assert not services.check(arguments_faulty_user)["rsync"]["transfer"]


@pytest.mark.gitlab_runner
def test_rsync_service_run():
    services = Services()
    path_to_ssh_key = os.getenv("ZAMBEZE_CI_TEST_RSYNC_SSH_KEY")
    services.configure(
        {"rsync": {"private_ssh_key": path_to_ssh_key}}
    )

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

    services.run(arguments)
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

    services.run(arguments_return)
    # This will verify that copying from a remote machine to the local
    # machine was a success
    assert os.path.exists(file_path_return)

    with open(file_path_return) as f:
        # Now we will verify that it is the same file that was sent
        lines = f.readlines()
        # Should be a single line
        random_int = int(lines[0])
        assert random_int == original_number
