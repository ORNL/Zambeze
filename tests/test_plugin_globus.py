# Local imports
import zambeze.orchestration.plugin_modules.globus.globus as globus

# Standard imports
import os
import pytest
import random
import time

GITLAB_RUNNER_UUIDs = ["f4e5e85c-3a35-455f-9d91-1ee3a0564935"]


# @pytest.mark.globus
# def test_globus_basic1():
#
#    required_env_variables = [
#        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
#        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
#    ]
#
#    for env_var in required_env_variables:
#        if env_var not in os.environ:
#            raise Exception(
#                "Globus test cannot be run if the env variable"
#                f" {env_var} is not defined and a local "
#                "globus-connect-server and endpoint have not been"
#                " set up."
#            )
#
#    globus_plugin = globus.Globus()
#
#    assert globus_plugin.name == "globus"
#    assert globus_plugin.configured is False
#
#    """Requires that the env variable is provided"""
#    configuration = {
#        "client_id": os.getenv(required_env_variables[0]),
#        "authentication_flow": {
#            "type": "client credential",
#            "secret": os.getenv(required_env_variables[1]),
#        },
#    }
#
#    globus_plugin.configure(configuration)
#
#    assert globus_plugin.configured
#
#    assert len(globus_plugin.supportedActions) == 2
#    # We assume that we at least have access to the globus cloud
#    assert "transfer" in globus_plugin.supportedActions
#
#
# @pytest.mark.globus
# def test_globus_basic2():
#
#    required_env_variables = [
#        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
#        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
#    ]
#
#    for env_var in required_env_variables:
#        if env_var not in os.environ:
#            raise Exception(
#                "Globus test cannot be run if the env variable"
#                f" {env_var} is not defined and a local "
#                "globus-connect-server and endpoint have not been"
#                " set up."
#            )
#
#    globus_plugin = globus.Globus()
#
#    """Requires that the env variable is provided
#
#    A valid globus collection must also exist on this machine
#    in order for the move to globus endpoint and move from
#    globus endpoint to local posix file system to work."""
#    configuration = {
#        "client_id": os.getenv(required_env_variables[0]),
#        "authentication_flow": {
#            "type": "client credential",
#            "secret": os.getenv(required_env_variables[1]),
#        },
#        "local_endpoints": [
#            {
#                "uuid": os.getenv(required_env_variables[2]),
#                "path": "/home/cades/Collections/default",
#                "type": "mapped",
#            }
#        ],
#        "default_endpoint": os.getenv(required_env_variables[2]),
#    }
#
#    globus_plugin.configure(configuration)
#
#    assert len(globus_plugin.supportedActions) == 4
#
#
# @pytest.mark.globus
# def test_globus_move_check():
#
#    required_env_variables = [
#        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
#        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
#    ]
#
#    for env_var in required_env_variables:
#        if env_var not in os.environ:
#            raise Exception(
#                "Globus test cannot be run if the env variable"
#                f" {env_var} is not defined and a local "
#                "globus-connect-server and endpoint have not been"
#                " set up."
#            )
#
#    configuration = {
#        "client_id": os.getenv(required_env_variables[0]),
#        "authentication_flow": {
#            "type": "client credential",
#            "secret": os.getenv(required_env_variables[1]),
#        },
#        "local_endpoints": [
#            {
#                "uuid": os.getenv(required_env_variables[2]),
#                "path": "/home/cades/Collections/default",
#                "type": "mapped",
#            }
#        ],
#        "default_endpoint": os.getenv(required_env_variables[2]),
#    }
#
#    globus_plugin = globus.Globus()
#    globus_plugin.configure(configuration)
#
#    # Create a file on the local posix system
#    file_name = "demofile_for_globus1.txt"
#    f = open(file_name, "w")
#    original_number = random.randint(0, 100000000000)
#    f.write(str(original_number))
#    f.close()
#
#    current_valid_path = os.getcwd()
#    file_path = current_valid_path + "/" + file_name
#
#    destination_path = "/"
#    sub_folder = ""
#    # This is so that we can run the test both as a runner and as user
#    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
#        sub_folder = "runner/"
#
#    package = [
#        {
#            "move_to_globus_collection": {
#                "items": [
#                    {
#                        "source": "file://" + file_path,
#                        "destination": "globus://"
#                        + os.getenv(required_env_variables[2])
#                        + destination_path
#                        + sub_folder,
#                    }
#                ]
#            }
#        }
#    ]
#
#    checked_actions = globus_plugin.check(package)
#    assert checked_actions["move_to_globus_collection"][0]
#
#
# @pytest.mark.globus
# def test_globus_transfer_check():
#
#    required_env_variables = [
#        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
#        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
#    ]
#
#    for env_var in required_env_variables:
#        if env_var not in os.environ:
#            raise Exception(
#                "Globus test cannot be run if the env variable"
#                f" {env_var} is not defined and a local "
#                "globus-connect-server and endpoint have not been"
#                " set up."
#            )
#
#    configuration = {
#        "client_id": os.getenv(required_env_variables[0]),
#        "authentication_flow": {
#            "type": "client credential",
#            "secret": os.getenv(required_env_variables[1]),
#        },
#        "local_endpoints": [
#            {
#                "uuid": os.getenv(required_env_variables[2]),
#                "path": "/home/cades/Collections/default",
#                "type": "mapped",
#            }
#        ],
#        "default_endpoint": os.getenv(required_env_variables[2]),
#    }
#
#    globus_plugin = globus.Globus()
#    globus_plugin.configure(configuration)
#
#    # Create a file on the local posix system
#    file_name = "demofile_for_globus1.txt"
#    f = open(file_name, "w")
#    original_number = random.randint(0, 100000000000)
#    f.write(str(original_number))
#    f.close()
#
#    current_valid_path = os.getcwd()
#    file_path = current_valid_path + "/" + file_name
#
#    destination_path = "/"
#    sub_folder = ""
#    # This is so that we can run the test both as a runner and as user
#    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
#        sub_folder = "runner/"
#
#    package = [
#        {
#            "move_to_globus_collection": {
#                "items": [
#                    {
#                        "source": "file://" + file_path,
#                        "destination": "globus://" + destination_path + sub_folder,
#                    }
#                ]
#            }
#        },
#        {
#            "transfer": {
#                "type": "synchronous",
#                "items": [
#                    {
#                        "source": "globus://"
#                        + os.getenv(required_env_variables[2])
#                        + os.sep
#                        + sub_folder
#                        + file_name,
#                        "destination": "globus://"
#                        + os.getenv(required_env_variables[3])
#                        + destination_path
#                        + sub_folder
#                        + file_name,
#                    }
#                ],
#            }
#        },
#    ]
#
#    output = globus_plugin.check(package)
#
#    for item in output:
#        assert output[item][0]
#
#
# @pytest.mark.globus
# def test_globus_process():
#
#    required_env_variables = [
#        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
#        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
#        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_COLLECTION_PATH",
#        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_GUEST_COLLECTION_PATH"
#    ]
#
#    for env_var in required_env_variables:
#        if env_var not in os.environ:
#            raise Exception(
#                "Globus test cannot be run if the env variable"
#                f" {env_var} is not defined and a local "
#                "globus-connect-server and endpoint have not been"
#                " set up."
#            )
#
#    path_to_endpoint = os.getenv(required_env_variables[4])
#    path_to_endpoint_shared = os.getenv(required_env_variables[5])
#
#    configuration = {
#        "client_id": os.getenv(required_env_variables[0]),
#        "authentication_flow": {
#            "type": "client credential",
#            "secret": os.getenv(required_env_variables[1]),
#        },
#        "local_endpoints": [
#            {
#                "uuid": os.getenv(required_env_variables[2]),
#                "path": path_to_endpoint,
#                "type": "mapped",
#            },
#            {
#                "uuid": os.getenv(required_env_variables[3]),
#                "path": path_to_endpoint_shared,
#                "type": "guest",
#            },
#        ],
#        "default_endpoint": os.getenv(required_env_variables[3]),
#    }
#
#    globus_plugin = globus.Globus()
#    globus_plugin.configure(configuration)
#
#    # Create a file on the local posix system
#    file_name = "demofile_for_globus1.txt"
#    f = open(file_name, "w")
#    original_number = random.randint(0, 100000000000)
#    f.write(str(original_number))
#    f.close()
#
#    current_valid_path = os.getcwd()
#    file_path = current_valid_path + "/" + file_name
#
#    relative_destination_file_path = "/"
#    sub_folder = ""
#    # This is so that we can run the test both as a runner and as user
#    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
#        sub_folder = "runner/"
#    # action items in the list should be executed in order
#    package = [
#        {
#            "move_to_globus_collection": {
#                "items": [
#                    {
#                        "source": "file://" + file_path,
#                        "destination": "globus://"
#                        + os.getenv(required_env_variables[2])
#                        + relative_destination_file_path
#                        + sub_folder,
#                    }
#                ]
#            }
#        },
#        {
#            "transfer": {
#                "type": "synchronous",
#                "items": [
#                    {
#                        "source": "globus://"
#                        + os.getenv(required_env_variables[2])
#                        + sub_folder
#                        + file_name,
#                        "destination": "globus://"
#                        + os.getenv(required_env_variables[3])
#                        + relative_destination_file_path
#                        + sub_folder
#                        + file_name,
#                    }
#                ],
#            }
#        },
#    ]
#
#    # This test is designed to move a file to the globus endpoint
#    # So before we get started we are going to make sure that a file
#    # does not already exist at that location
#    abs_path_destination = (
#        path_to_endpoint
#        + relative_destination_file_path
#        + sub_folder
#        + os.path.basename(file_path)
#    )
#    # After it gets transferred using globus it should end up moving to the sub_folder
#    abs_path_destination_shared = (
#        path_to_endpoint
#        + relative_destination_file_path
#        + "guest/"
#        + sub_folder
#        + os.path.basename(file_path)
#    )
#    if os.path.exists(abs_path_destination):
#        os.remove(abs_path_destination)
#    if os.path.exists(abs_path_destination_shared):
#        os.remove(abs_path_destination_shared)
#
#    checked_items = globus_plugin.check(package)
#    all_checks_pass = True
#    for item in checked_items:
#        if not checked_items[item][0]:
#            print("Something went wrong.")
#            print(checked_items[item][1])
#            all_checks_pass = False
#
#    if all_checks_pass:
#        globus_plugin.process(package)
#
#    # After processing we should verify that the file exists at the final location
#    assert os.path.exists(abs_path_destination_shared)
#
#
# @pytest.mark.globus
# def test_globus_process_from_esnet():
#    """NOTE
#
#    We cannot simply download to a collection, we have to download to
#    a folder that is owned by the user running the this test. I.e. if
#    the GitLab Runner is being used then we have to specify a folder that
#    the GitLab Runner can actually access from the POSIX side.
#    """
#    required_env_variables = [
#        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
#        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
#        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_COLLECTION_PATH",
#        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_GUEST_COLLECTION_PATH"
#    ]
#
#    for env_var in required_env_variables:
#        if env_var not in os.environ:
#            raise Exception(
#                "Globus test cannot be run if the env variable"
#                f" {env_var} is not defined and a local "
#                "globus-connect-server and endpoint have not been"
#                " set up."
#            )
#
#    path_to_endpoint = os.getenv(required_env_variables[4])
#    path_to_endpoint_shared = os.getenv(required_env_variables[5])
#
#    configuration = {
#        "client_id": os.getenv(required_env_variables[0]),
#        "authentication_flow": {
#            "type": "client credential",
#            "secret": os.getenv(required_env_variables[1]),
#        },
#        "local_endpoints": [
#            {
#                "uuid": os.getenv(required_env_variables[2]),
#                "path": path_to_endpoint,
#                "type": "mapped",
#            },
#            {
#                "uuid": os.getenv(required_env_variables[3]),
#                "path": path_to_endpoint_shared,
#                "type": "guest",
#            },
#        ],
#        "default_endpoint": os.getenv(required_env_variables[3]),
#    }
#
#    globus_plugin = globus.Globus()
#    globus_plugin.configure(configuration)
#
#    # action items in the list should be executed in order
#    ESNET_GLOBUS_ENDPOINT_UUID = "ece400da-0182-4777-91d6-27a1808f8371"
#
#    # This is so that we can run the test both as a runner and as user
#    sub_folder = ""
#    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
#        sub_folder = "/runner"
#
#    package = [
#        {
#            "transfer": {
#                "type": "synchronous",
#                "items": [
#                    {
#                        "source": "globus://" + ESNET_GLOBUS_ENDPOINT_UUID + "/1M.dat",
#                        "destination": "globus://"
#                        + os.getenv(required_env_variables[2])
#                        + sub_folder
#                        + "1M.dat",
#                    }
#                ],
#            }
#        }
#    ]
#
#    # This test is designed to move a file to the globus endpoint
#    # So before we get started we are going to make sure that a file
#    # does not already exist at that location
#    abs_path_destination = path_to_endpoint + sub_folder + "/1M.dat"
#
#    if os.path.exists(abs_path_destination):
#        os.remove(abs_path_destination)
#
#    checked_actions = globus_plugin.check(package)
#    for action in checked_actions:
#        assert action[0]
#
#    globus_plugin.process(package)
#
#    # After processing we should verify that the file exists at the final location
#    assert os.path.exists(abs_path_destination)
#
#
# @pytest.mark.globus
# def test_globus_process_async():
#
#    required_env_variables = [
#        "ZAMBEZE_CI_TEST_GLOBUS_CLIENT_ID",
#        "ZAMBEZE_CI_TEST_GLOBUS_APP_KEY",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
#        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
#        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_COLLECTION_PATH",
#        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_GUEST_COLLECTION_PATH"
#    ]
#
#    for env_var in required_env_variables:
#        if env_var not in os.environ:
#            raise Exception(
#                "Globus test cannot be run if the env variable"
#                f" {env_var} is not defined and a local "
#                "globus-connect-server and endpoint have not been"
#                " set up."
#            )
#
#    path_to_endpoint = os.getenv(required_env_variables[4])
#    path_to_endpoint_shared = os.getenv(required_env_variables[5])
#
#    configuration = {
#        "client_id": os.getenv(required_env_variables[0]),
#        "authentication_flow": {
#            "type": "client credential",
#            "secret": os.getenv(required_env_variables[1]),
#        },
#        "local_endpoints": [
#            {
#                "uuid": os.getenv(required_env_variables[2]),
#                "path": path_to_endpoint,
#                "type": "mapped",
#            },
#            {
#                "uuid": os.getenv(required_env_variables[3]),
#                "path": path_to_endpoint_shared,
#                "type": "guest",
#            },
#        ],
#        "default_endpoint": os.getenv(required_env_variables[3]),
#    }
#
#    globus_plugin = globus.Globus()
#    globus_plugin.configure(configuration)
#
#    # Create a file on the local posix system
#    file_name = "demofile_for_globus1.txt"
#    f = open(file_name, "w")
#    original_number = random.randint(0, 100000000000)
#    f.write(str(original_number))
#    f.close()
#
#    current_valid_path = os.getcwd()
#    file_path = current_valid_path + "/" + file_name
#
#    relative_destination_file_path = "/"
#    sub_folder = ""
#    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
#        sub_folder = "runner/"
#    # action items in the list should be executed in order
#    package = [
#        {
#            "move_to_globus_collection": {
#                "items": [
#                    {
#                        "source": "file://" + file_path,
#                        "destination": "globus://"
#                        + os.getenv(required_env_variables[2])
#                        + relative_destination_file_path
#                        + sub_folder,
#                    }
#                ]
#            }
#        },
#        {
#            "transfer": {
#                "type": "asynchronous",
#                "items": [
#                    {
#                        "source": "globus://"
#                        + os.getenv(required_env_variables[2])
#                        + sub_folder
#                        + file_name,
#                        "destination": "globus://"
#                        + os.getenv(required_env_variables[3])
#                        + relative_destination_file_path
#                        + sub_folder
#                        + file_name,
#                    }
#                ],
#            }
#        },
#    ]
#
#    abs_path_destination = path_to_endpoint + sub_folder + file_name
#
#    abs_path_destination = (
#        path_to_endpoint
#        + relative_destination_file_path
#        + sub_folder
#        + os.path.basename(file_path)
#    )
#
#    abs_path_destination_shared = (
#        path_to_endpoint
#        + relative_destination_file_path
#        + "guest/"
#        + sub_folder
#        + os.path.basename(file_path)
#    )
#
#    # Remove files from previous runs that might exist on the mapped and guest
#    # collections
#    if os.path.exists(abs_path_destination):
#        os.remove(abs_path_destination)
#    if os.path.exists(abs_path_destination_shared):
#        os.remove(abs_path_destination_shared)
#
#    checked_actions = globus_plugin.check(package)
#    for action in checked_actions:
#        assert action[0]
#
#    result = globus_plugin.process(package)
#
#    result = globus_plugin.process([result["transfer"]["callback"]])
#    while result["get_task_status"]["result"]["status"] != "SUCCEEDED":
#        print("waiting...")
#        time.sleep(1)
#        result = globus_plugin.process([result["get_task_status"]["callback"]])
#
#    print("complete")
#    print(result["get_task_status"])
#    # After processing we should verify that the file exists at the final location
#    assert os.path.exists(abs_path_destination_shared)


@pytest.mark.globus_manual
def test_globus_process_manual():

    required_env_variables = [
        "ZAMBEZE_CI_TEST_GLOBUS_NATIVE_CLIENT_ID",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_UUID",
        "ZAMBEZE_CI_TEST_GLOBUS_COLLECTION_SHARED_UUID",
        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_COLLECTION_PATH",
        "ZAMBEZE_CI_TEST_POSIX_GLOBUS_GUEST_COLLECTION_PATH",
    ]

    for env_var in required_env_variables:
        if env_var not in os.environ:
            raise Exception(
                "Globus test cannot be run if the env variable"
                f" {env_var} is not defined and a local "
                "globus-connect-server and endpoint have not been"
                " set up."
            )

    path_to_endpoint = os.getenv(required_env_variables[3])
    path_to_endpoint_shared = os.getenv(required_env_variables[4])

    configuration = {
        "client_id": os.getenv(required_env_variables[0]),
        "authentication_flow": {"type": "native"},
        "local_endpoints": [
            {
                "uuid": os.getenv(required_env_variables[1]),
                "path": path_to_endpoint,
                "type": "mapped",
            },
            {
                "uuid": os.getenv(required_env_variables[2]),
                "path": path_to_endpoint_shared,
                "type": "guest",
            },
        ],
        "default_endpoint": os.getenv(required_env_variables[2]),
    }

    print(configuration)

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

    relative_destination_file_path = "/"
    sub_folder = ""
    # This is so that we can run the test both as a runner and as user
    if os.getenv(required_env_variables[0]) in GITLAB_RUNNER_UUIDs:
        sub_folder = "runner/"
    # action items in the list should be executed in order
    package = [
        {
            "move_to_globus_collection": {
                "items": [
                    {
                        "source": "file://" + file_path,
                        "destination": "globus://"
                        + os.getenv(required_env_variables[1])
                        + relative_destination_file_path
                        + sub_folder,
                    }
                ]
            }
        },
        {
            "transfer": {
                "type": "synchronous",
                "items": [
                    {
                        "source": "globus://"
                        + os.getenv(required_env_variables[1])
                        + sub_folder
                        + file_name,
                        "destination": "globus://"
                        + os.getenv(required_env_variables[2])
                        + relative_destination_file_path
                        + sub_folder
                        + file_name,
                    }
                ],
            }
        },
    ]

    # This test is designed to move a file to the globus endpoint
    # So before we get started we are going to make sure that a file
    # does not already exist at that location
    abs_path_destination = (
        path_to_endpoint
        + relative_destination_file_path
        + sub_folder
        + os.path.basename(file_path)
    )
    # After it gets transferred using globus it should end up moving to the sub_folder
    abs_path_destination_shared = (
        path_to_endpoint
        + relative_destination_file_path
        + "guest/"
        + sub_folder
        + os.path.basename(file_path)
    )
    if os.path.exists(abs_path_destination):
        os.remove(abs_path_destination)
    if os.path.exists(abs_path_destination_shared):
        os.remove(abs_path_destination_shared)

    checked_items = globus_plugin.check(package)
    all_checks_pass = True
    print(checked_items)
    for item in checked_items:
        for action in item.keys():
            print(item[action])
            if not item[action][0]:
                all_checks_pass = False

    if all_checks_pass:
        globus_plugin.process(package)

    # After processing we should verify that the file exists at the final location
    print(abs_path_destination_shared)
    assert os.path.exists(abs_path_destination_shared)
