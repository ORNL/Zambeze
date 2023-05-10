# Local imports
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType
from zambeze.log_manager import LogManager

# Standard imports
import pytest
import time
import uuid
import logging

logger = LogManager(logging.DEBUG, name="test_message_factory")

@pytest.mark.unit
def test_factory_fail():
    msg_factory = MessageFactory(logger)

    """Following should generate all the required and optional fields for
    creating a status message, The returned tuple with have the
    following form:

    :Example of Tuple:

    (
        MessageType.STATUS,
        {
            "message_id": "",
            "submission_time": "",
            "type": "",
            "activity_id": "",
            "target_id": "",
            "campaign_id": "",
            "agent_id": "",
            "body": {}
        }
    )
    """
    status_tuple = msg_factory.create_template(MessageType.STATUS)
    """At this point the template can be used to fill in the items required
    to exceute the message after it is sent"""
    print(status_tuple)
    status_tuple[1].message_id = 1
    status_tuple[1].submission_time = str(int(time.time()))

    """This field should force failure"""
    status_tuple[1].unsupported_field = "should make fail"

    """Should generate an immutable Status message, it will also verify that
    the correct fields have been included."""
    failed = False
    try:
        msg_factory.create(status_tuple)
    except Exception:
        failed = True

    assert failed is True


@pytest.mark.unit
def test_factory_activity_template_plugin_globus():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    msg_factory = MessageFactory(logger)
    activity_template = msg_factory.create_template(
        MessageType.ACTIVITY,
        ActivityType.PLUGIN,
        args={"plugin": "globus", "action": "transfer"},
    )[1]
    print(activity_template)
    no_fail = True
    try:
        activity_template.message_id = str(uuid.uuid4())
        activity_template.activity_id = str(uuid.uuid4())
        activity_template.agent_id = str(uuid.uuid4())
        activity_template.campaign_id = str(uuid.uuid4())
        activity_template.credential = {}
        activity_template.submission_time = str(int(time.time()))
        assert activity_template.body.parameters.transfer.type == "synchronous"
        assert activity_template.body.type == "PLUGIN"
        assert activity_template.body.plugin == "globus"
        activity_template.body.parameters.transfer.items[0].source = ""
        activity_template.body.parameters.transfer.items[0].destination = ""
        activity_template.needs = []
    except Exception as e:
        print(e)
        no_fail = False
    assert no_fail


@pytest.mark.unit
def test_factory_activity_template_plugin_rsync():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    msg_factory = MessageFactory(logger)
    activity_template = msg_factory.create_template(
        MessageType.ACTIVITY,
        ActivityType.PLUGIN,
        {"plugin": "rsync", "action": "transfer"},
    )[1]
    print(activity_template)
    no_fail = True
    try:
        activity_template.message_id = str(uuid.uuid4())
        activity_template.activity_id = str(uuid.uuid4())
        activity_template.agent_id = str(uuid.uuid4())
        activity_template.campaign_id = str(uuid.uuid4())
        activity_template.credential = {}
        activity_template.submission_time = str(int(time.time()))
        assert activity_template.body.parameters.transfer.type == "synchronous"
        assert activity_template.body.type == "PLUGIN"
        assert activity_template.body.plugin == "rsync"
        activity_template.body.parameters.transfer.items[0].source.path = ""
        activity_template.body.parameters.transfer.items[0].source.user = ""
        activity_template.body.parameters.transfer.items[0].destination.path = ""
        activity_template.body.parameters.transfer.items[0].destination.user = ""
        activity_template.needs = []
    except Exception as e:
        print(e)
        no_fail = False
    assert no_fail


@pytest.mark.unit
def test_factory_activity_template_shell():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    msg_factory = MessageFactory(logger)
    activity_template = msg_factory.create_template(
        MessageType.ACTIVITY, ActivityType.SHELL, args={"shell": "bash"}
    )[1]
    print(activity_template)
    no_fail = True
    try:
        activity_template.message_id = str(uuid.uuid4())
        activity_template.activity_id = str(uuid.uuid4())
        activity_template.agent_id = str(uuid.uuid4())
        activity_template.campaign_id = str(uuid.uuid4())
        activity_template.credential = {}
        activity_template.submission_time = str(int(time.time()))
        assert activity_template.body.type == "SHELL"
        assert activity_template.body.shell == "bash"

    except Exception as e:
        print(e)
        no_fail = False
    assert no_fail


@pytest.mark.unit
def test_factory_success_status():
    msg_factory = MessageFactory(logger)

    """Following should generate all the required and optional fields for
    creating a status message, The returned tuple with have the
    following form:

    :Example of Tuple:

    (
        MessageType.STATUS,
        {
            "message_id": "",
            "submission_time": "",
            "type": "",
            "activity_id": "",
            "target_id": "",
            "campaign_id": "",
            "agent_id": "",
            "body": {}
        }
    )
    """
    status_tuple = msg_factory.create_template(MessageType.STATUS)
    """At this point the template can be used to fill in the items required
    to exceute the message after it is sent"""
    status_tuple[1].message_id = str(uuid.uuid4())
    status_tuple[1].submission_time = str(int(time.time()))
    status_tuple[1].activity_id = str(uuid.uuid4())
    status_tuple[1].target_id = str(uuid.uuid4())
    status_tuple[1].campaign_id = str(uuid.uuid4())
    status_tuple[1].agent_id = str(uuid.uuid4())
    status_tuple[1].body = {}

    """Should generate an immutable Status message, it will also verify that
    the correct fields have been included."""
    status_msg = msg_factory.create(status_tuple)

    assert status_msg.type == MessageType.STATUS


@pytest.mark.unit
def test_factory_create_plugin_rsync():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    msg_factory = MessageFactory(logger)
    activity_tuple = msg_factory.create_template(
        MessageType.ACTIVITY,
        ActivityType.PLUGIN,
        {"plugin": "rsync", "action": "transfer"},
    )
    print(activity_tuple)

    activity_tuple[1].message_id = str(uuid.uuid4())
    activity_tuple[1].activity_id = str(uuid.uuid4())
    activity_tuple[1].agent_id = str(uuid.uuid4())
    activity_tuple[1].campaign_id = str(uuid.uuid4())
    activity_tuple[1].credential = {}
    activity_tuple[1].submission_time = str(int(time.time()))
    activity_tuple[1].body.parameters.transfer.items[0].source.path = ""
    activity_tuple[1].body.parameters.transfer.items[0].source.user = ""
    activity_tuple[1].body.parameters.transfer.items[0].source.ip = "127.0.0.1"
    activity_tuple[1].body.parameters.transfer.items[0].destination.path = ""
    activity_tuple[1].body.parameters.transfer.items[0].destination.user = ""
    activity_tuple[1].body.parameters.transfer.items[0].destination.ip = "127.0.0.1"
    activity_tuple[1].needs = []

    """Should generate an immutable Activity message, it will also verify that
    the correct fields have been included."""
    status_msg = msg_factory.create(activity_tuple)

    assert status_msg.type == MessageType.ACTIVITY
