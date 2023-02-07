# Local imports
from zambeze.orchestration.plugins import Plugins
from zambeze.orchestration.plugins_message_template_engine import (
    PluginsMessageTemplateEngine,
)
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType
from zambeze.orchestration.network import getIP

# Standard imports
import copy
import os
import pwd
import pytest
import re

import logging
import random
import socket
import time
import uuid

logger = logging.getLogger(__name__)


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


@pytest.mark.unit
def test_shell_plugin_check():
    plugins = Plugins()
    plugins.configure({"shell": {}})

    file_name = "shell_file.txt1"
    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name
    original_number = random.randint(0, 100000000000)

    factory = MessageFactory(logger=logger)
    msg_template = factory.create_template(
        MessageType.ACTIVITY, ActivityType.SHELL, {"shell": "bash"}
    )

    msg_template[1].message_id = str(uuid.uuid4())
    msg_template[1].activity_id = str(uuid.uuid4())
    msg_template[1].agent_id = str(uuid.uuid4())
    msg_template[1].campaign_id = str(uuid.uuid4())
    msg_template[1].credential = {}
    msg_template[1].submission_time = str(int(time.time()))
    # This section will get replaced with a single rsync uri in the future
    msg_template[1].body.parameters.program = "echo"
    msg_template[1].body.parameters.args = ["$RAN", ">", file_path]
    msg_template[1].body.parameters.env_vars = {"RAN": str(original_number)}

    msg = factory.create(msg_template)
    checked_actions = plugins.check(msg)
    print(checked_actions)
    assert checked_actions["shell"][0]["bash"][0]


@pytest.mark.unit
def test_shell_plugin_run():
    plugins = Plugins()
    plugins.configure({"shell": {}})

    file_name = "shell_file2.txt"
    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name
    original_number = random.randint(0, 100000000000)

    factory = MessageFactory(logger=logger)
    msg_template = factory.create_template(
        MessageType.ACTIVITY, ActivityType.SHELL, {"shell": "bash"}
    )

    msg_template[1].message_id = str(uuid.uuid4())
    msg_template[1].activity_id = str(uuid.uuid4())
    msg_template[1].agent_id = str(uuid.uuid4())
    msg_template[1].campaign_id = str(uuid.uuid4())
    msg_template[1].credential = {}
    msg_template[1].submission_time = str(int(time.time()))
    # This section will get replaced with a single rsync uri in the future
    msg_template[1].body.parameters.program = "echo"
    msg_template[1].body.parameters.args = ["$RAN", ">", file_path]
    msg_template[1].body.parameters.env_vars = {"RAN": str(original_number)}

    msg = factory.create(msg_template)
    checked_actions = plugins.check(msg)
    assert checked_actions["shell"][0]["bash"][0]
    plugins.run(msg)

    assert os.path.exists(file_path)
    with open(file_path) as f:
        # Now we will verify that it is the same file that was sent
        lines = f.readlines()
        # Should be a single line
        assert lines[0].strip() == str(original_number)


@pytest.mark.integration
def test_rsync_plugin_check():
    plugins = Plugins()
    plugins.configure({"shell": {}, "rsync": {}})

    # Grab valid paths, usernames and ip addresses
    current_valid_path = os.getcwd()
    current_user = pwd.getpwuid(os.geteuid())[0]
    print(os.environ)
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    neighbor_vm = os.getenv("ZAMBEZE_CI_TEST_RSYNC_IP")
    neighbor_vm_ip = getIP(neighbor_vm)

    rsync_user = os.getenv("ZAMBEZE_CI_TEST_RSYNC_USER")
    factory = MessageFactory(logger=logger)
    msg_template = factory.create_template(
        MessageType.ACTIVITY,
        ActivityType.PLUGIN,
        {"plugin": "rsync", "action": "transfer"},
    )

    msg_template[1].message_id = str(uuid.uuid4())
    msg_template[1].activity_id = str(uuid.uuid4())
    msg_template[1].agent_id = str(uuid.uuid4())
    msg_template[1].campaign_id = str(uuid.uuid4())
    msg_template[1].credential = {}
    msg_template[1].submission_time = str(int(time.time()))
    # This section will get replaced with a single rsync uri in the future
    msg_template[1].body.parameters.transfer.items[0].source.ip = local_ip
    msg_template[1].body.parameters.transfer.items[0].source.user = current_user
    msg_template[1].body.parameters.transfer.items[0].source.path = current_valid_path
    msg_template[1].body.parameters.transfer.items[0].destination.ip = neighbor_vm_ip
    msg_template[1].body.parameters.transfer.items[0].destination.user = rsync_user
    msg_template[1].body.parameters.transfer.items[0].destination.path = "/tmp"

    msg = factory.create(msg_template)
    checked_actions = plugins.check(msg)
    assert checked_actions["rsync"][0]["transfer"][0]

    msg_faulty_ip = copy.deepcopy(msg_template)
    msg_faulty_ip[1].body.parameters.transfer.items[0].destination.ip = "172.22."
    should_fail = False
    try:
        msg = factory.create(msg_faulty_ip)
    except Exception:
        should_fail = True

    assert should_fail

    msg_faulty_user = copy.deepcopy(msg_template)
    msg_faulty_user[1].body.parameters.transfer.items[
        0
    ].source.user = "user_that_does_not_exist"
    msg = factory.create(msg_faulty_user)
    checked_actions = plugins.check(msg)
    assert not checked_actions["rsync"][0]["transfer"][0]


@pytest.mark.integration
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

    python3 -m pytest -m integration
    """
    plugins = Plugins()

    print(os.environ)
    neighbor_vm = os.getenv("ZAMBEZE_CI_TEST_RSYNC_IP")
    neighbor_vm_ip = getIP(neighbor_vm)
    path_to_ssh_key = os.getenv("ZAMBEZE_CI_TEST_RSYNC_SSH_KEY")
    rsync_user = os.getenv("ZAMBEZE_CI_TEST_RSYNC_USER")
    plugins.configure({"rsync": {"private_ssh_key": path_to_ssh_key}})

    # Attaching a timestamp to avoid concurrent runs overwriting files
    file_name = "demofile-" + str(time.time_ns()) + ".txt"
    f = open(file_name, "w")
    random.seed(time.time())
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()
    # Grab valid paths, usernames and ip addresses
    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    current_user = pwd.getpwuid(os.geteuid())[0]
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    factory = MessageFactory(logger=logger)
    msg_template = factory.create_template(
        MessageType.ACTIVITY,
        ActivityType.PLUGIN,
        {"plugin": "rsync", "action": "transfer"},
    )

    msg_template[1].message_id = str(uuid.uuid4())
    msg_template[1].activity_id = str(uuid.uuid4())
    msg_template[1].agent_id = str(uuid.uuid4())
    msg_template[1].campaign_id = str(uuid.uuid4())
    msg_template[1].credential = {}
    msg_template[1].submission_time = str(int(time.time()))
    # In the future this will be simplified and be replced with a single
    # rsync uri
    msg_template[1].body.parameters.transfer.items[0].source.ip = local_ip
    msg_template[1].body.parameters.transfer.items[0].source.user = current_user
    msg_template[1].body.parameters.transfer.items[0].source.path = file_path
    msg_template[1].body.parameters.transfer.items[0].destination.ip = neighbor_vm_ip
    msg_template[1].body.parameters.transfer.items[0].destination.user = rsync_user
    msg_template[1].body.parameters.transfer.items[0].destination.path = "/tmp"

    msg = factory.create(msg_template)
    checks = plugins.check(msg)
    assert checks["rsync"][0]["transfer"][0]
    plugins.run(msg)

    file_name_return = "demofile_return-" + str(time.time_ns()) + ".txt"
    file_path_return = current_valid_path + "/" + file_name_return

    # Remove local copy of file if it already exists
    if os.path.exists(file_path_return):
        os.remove(file_path_return)

    template_engine = PluginsMessageTemplateEngine()
    msg_template_return = template_engine.generate("rsync", "transfer")

    msg_template_return = factory.create_template(
        MessageType.ACTIVITY,
        ActivityType.PLUGIN,
        {"plugin": "rsync", "action": "transfer"},
    )

    msg_template_return[1].message_id = str(uuid.uuid4())
    msg_template_return[1].activity_id = str(uuid.uuid4())
    msg_template_return[1].agent_id = str(uuid.uuid4())
    msg_template_return[1].campaign_id = str(uuid.uuid4())
    msg_template_return[1].credential = {}
    msg_template_return[1].submission_time = str(int(time.time()))
    msg_template_return[1].body.parameters.transfer.items[0].source.ip = neighbor_vm_ip
    msg_template_return[1].body.parameters.transfer.items[0].source.user = rsync_user
    msg_template_return[1].body.parameters.transfer.items[0].source.path = (
        "/tmp/" + file_name
    )
    msg_template_return[1].body.parameters.transfer.items[0].destination.ip = local_ip
    msg_template_return[1].body.parameters.transfer.items[
        0
    ].destination.user = current_user
    msg_template_return[1].body.parameters.transfer.items[
        0
    ].destination.path = file_path_return

    msg = factory.create(msg_template_return)
    checked_actions = plugins.check(msg)
    assert checked_actions["rsync"][0]["transfer"][0]
    attempts = 0
    # Loop is needed because sometimes the initial transfer takes a while to
    # finalize, this loop will make the test more robust.
    while True:
        plugins.run(msg)
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
