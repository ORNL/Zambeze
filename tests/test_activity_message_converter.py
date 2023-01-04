# Local imports

from zambeze.orchestration.message.abstract_message import AbstractMessage
from zambeze.orchestration.message.message_factory import MessageFactory

from zambeze.orchestration.zambeze_types import MessageType, ActivityType
from zambeze.orchestration.plugins import Plugins

from zambeze.orchestration.activity_message_converter import (
    ActivityMessageConverter
)

# Standard imports
import pytest
import time
import uuid


@pytest.mark.unit
def test_activity_message_converter_rsync():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    plugins = Plugins()
    msg_factory = MessageFactory(plugins)
    activity_tuple = msg_factory.createTemplate(
        MessageType.ACTIVITY,
        ActivityType.TRANSFER,
        {"plugin": "rsync", "action": "transfer"},
    )
    print(activity_tuple)

    agent_id = str(uuid.uuid4())
    activity_tuple[1].agent_id = agent_id
    activity_tuple[1].campaign_id = str(uuid.uuid4())
    activity_tuple[1].credential = {}
    activity_tuple[1].submission_time = str(int(time.time()))
    activity_tuple[1].\
        body.parameters.items[0].source = "rsync://file.txt"
    activity_tuple[1].\
        body.parameters.items[0].destination = "rsync://file2.txt"
    activity_tuple[1].needs = []

    """Should generate an immutable Activity message, it will also verify that
    the correct fields have been included."""
    transfer_activity_msg = msg_factory.create(activity_tuple)

    # Create a new plugin activity from the transfer activity
    converter = ActivityMessageConverter(agent_id)
    convert_to = ActivityType.PLUGIN
    new_plugin_msg: AbstractMessage = converter.convert(
            transfer_activity_msg, convert_to)

    assert new_plugin_msg.type == MessageType.ACTIVITY
    assert new_plugin_msg.body.plugin == "rsync"
    assert new_plugin_msg.agent_id == agent_id
    assert new_plugin_msg.body.campaign_id == transfer_activity_msg.body.campaign_id
    assert new_plugin_msg.message_id != transfer_activity_msg.message_id
    assert len(new_plugin_msg.message_id) > 0

    print("New Plugin msg")
    print(new_plugin_msg)
