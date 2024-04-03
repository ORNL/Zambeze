# Local imports
from zambeze.orchestration.plugins import Plugins
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType
from zambeze.campaign.activities.shell import ShellActivity
from zambeze.campaign.activities.abstract_activity import Activity

# Standard imports
import os
import pytest

import logging
import random
import time
import uuid

logger = logging.getLogger(__name__)


@pytest.mark.unit
def test_registered_plugins():
    """Test checks that you can get a list of all the registered plugins"""
    plugins = Plugins()
    found_shell = False
    found_rsync = False
    for plugin in plugins.registered:
        if plugin == "shell":
            found_shell = True

    assert found_shell


@pytest.mark.unit
def test_check_configured_plugins():
    plugins = Plugins()

    assert len(plugins.configured) == 0

    configuration = {"shell": {}}
    plugins.configure(configuration)

    assert len(plugins.configured) > 0


@pytest.mark.unit
def test_shell_plugin_check():
    plugins = Plugins()
    plugins.configure({"shell": {}})

    activity = ShellActivity(
        name="Simple echo",
        files=[],
        command="echo",
        arguments=[
            "hello-zambeze"
        ]
    )

    activity.message_id = str(uuid.uuid4())
    activity.activity_id = str(uuid.uuid4())
    activity.agent_id = str(uuid.uuid4())
    activity.campaign_id = str(uuid.uuid4())

    # 1. Confirm that we have the right types (checks of plugins.py)
    assert isinstance(activity, Activity)
    assert isinstance(activity, ShellActivity)
    check = plugins.check(msg=activity)

    # This will become more complicated when there is more to validate.
    assert len(check['shell']) == 2
    # Ensure we pass because all are True.
    assert all(value for d in check['shell'] for value in d.values())


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
