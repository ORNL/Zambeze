# Local imports
from zambeze.log_manager import (
    LogManager,
)

from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.plugins import Plugins
from zambeze.orchestration.zambeze_types import MessageType, ActivityType

# Standard imports
import logging
import os
import pytest
import random
import subprocess
import time
import uuid

@pytest.mark.unit
def test_log_manager1():
    log_manager = LogManager(logging.DEBUG)

    assert log_manager.name == "zambeze-logger"
    assert "/.zambeze/logs" in log_manager.path


@pytest.mark.unit
def test_log_manager2():

    current_valid_path = os.getcwd()
    log_file_path = current_valid_path + os.sep + "test2.log"
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    log_manager = LogManager(logging.DEBUG, name="log_test2", log_path=log_file_path)

    assert log_manager.name == "log_test2"
    assert log_file_path == log_manager.path

    debug_msg = "Debug Message"
    info_msg = "Info Message"
    warn_msg = "Warn Message"
    error_msg = "Error Message"
    critical_msg = "Critical Message"

    log_manager.debug(debug_msg)
    log_manager.info(info_msg)
    log_manager.warning(warn_msg)
    log_manager.error(error_msg)
    log_manager.critical(critical_msg)

    with open(log_file_path) as f:
        file_data = f.read()
        assert debug_msg in file_data
        assert info_msg in file_data
        assert warn_msg in file_data
        assert critical_msg in file_data


@pytest.mark.unit
def test_log_manager3():

    current_valid_path = os.getcwd()
    log_file_path = current_valid_path + os.sep + "test3.log"
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    log_manager = LogManager(logging.DEBUG, name="log_test3", log_path=log_file_path)

    shell_exec = subprocess.Popen(
                    ["echo 'Serenity'"],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1)

    log_manager.watch([shell_exec])

    shell_exec.wait()

    with open(log_file_path) as f:
        file_data = f.read()
        assert "Serenity" in file_data


@pytest.mark.unit
def test_log_manager4():

    current_valid_path = os.getcwd()
    log_file_path = current_valid_path + os.sep + "test4.log"
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    log_manager = LogManager(logging.DEBUG, name="log_test4", log_path=log_file_path)

    processes = []

    shell_exec1 = subprocess.Popen(
                    ["/bin/bash -c 'for i in {1..2000}; do echo Count_$i; done;'"],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    )
    processes.append(shell_exec1)

    shell_exec2 = subprocess.Popen(
                    ["/bin/bash -c 'for i in {2001..4000}; do echo Count_$i; done'"],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    )
    processes.append(shell_exec2)

    log_manager.watch(processes)

    shell_exec1.wait()
    shell_exec2.wait()

    with open(log_file_path) as f:
        num_lines = sum(1 for line in f)
        # Should have at least 12000 lines
        # Might have extra because of spaces
        assert num_lines >= 4000
    
    with open(log_file_path) as f:
        # Should contain an item Count_1, Count_2 ... Count_12000 somewhere in
        # the file
        file_data = f.read()
        for i in range(1, 4000):
            print(f"Checking Count_{i}")
            assert f"Count_{i}" in file_data


# This test is making sure that the logger is capturing output from a subprocess
@pytest.mark.internal_integration
def test_shell_plugin_run_with_log():
    current_valid_path = os.getcwd()
    log_file_path = current_valid_path + os.sep + "test5.log"

    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    log_manager = LogManager(logging.DEBUG, name="log_test5", log_path=log_file_path)
    plugins = Plugins(log_manager)
    plugins.configure({"shell": {}})

    original_number = random.randint(0, 100000000000)

    factory = MessageFactory(log_manager)
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
    msg_template[1].body.parameters.args = ["This-is-my-number $RAN"]
    msg_template[1].body.parameters.env_vars = {"RAN": str(original_number)}

    msg = factory.create(msg_template)
    checked_actions = plugins.check(msg)
    assert checked_actions["shell"][0]["bash"][0]
    plugins.run(msg)

    assert os.path.exists(log_file_path)
    with open(log_file_path) as f:
        # Now we will verify that it is the same file that was sent
        file_data = f.read()
        # Should be a single line
        message = "This-is-my-number " + str(original_number)
        assert message in file_data



