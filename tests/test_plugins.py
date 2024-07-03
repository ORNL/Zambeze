# Local imports
from zambeze.orchestration.plugins import Plugins
from zambeze.campaign.activities.shell import ShellActivity
from zambeze.campaign.activities.abstract_activity import Activity

# Standard imports
import os
import pytest

import logging
import uuid

logger = logging.getLogger(__name__)


@pytest.mark.unit
def test_registered_plugins():
    """Test checks that you can get a list of all the registered plugins"""
    plugins = Plugins()
    found_shell = False
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
        name="Simple echo", files=[], command="echo", arguments="hello-zambeze"
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
    assert len(check["shell"]) == 2
    # Ensure we pass because all are True.
    assert all(value for d in check["shell"] for value in d.values())


@pytest.mark.unit
def test_shell_plugin_run():
    plugins = Plugins()
    plugins.configure({"shell": {}})

    file_name = "shell_file2.txt"
    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    # factory = MessageFactory(logger=logger)
    # msg_template = factory.create_template(
    #     MessageType.ACTIVITY, ActivityType.SHELL, {"shell": "bash"}
    # )

    activity = ShellActivity(
        name="Simple echo", files=[], command="touch", arguments=file_path
    )

    activity.message_id = str(uuid.uuid4())
    activity.activity_id = str(uuid.uuid4())
    activity.agent_id = str(uuid.uuid4())
    activity.campaign_id = str(uuid.uuid4())

    checked_actions = plugins.check(msg=activity)

    # First, make sure there is no file.
    if os.path.exists(file_path):
        os.remove(file_path)
    assert not os.path.exists(file_path)

    # Second, make sure we can run the plugin.
    # This will become more complicated when there is more to validate.
    assert len(checked_actions["shell"]) == 2
    # Ensure we pass because all are True.
    assert all(value for d in checked_actions["shell"] for value in d.values())

    # Third, run the plugin.
    plugins.run(activity)

    # Fourth, check that file exists.
    assert os.path.exists(file_path)

    # Fifth, remove it and make sure it stays removed.
    os.remove(file_path)
    assert not os.path.exists(file_path)
