# Local imports
from zambeze.orchestration.message.message_factory import MessageFactory

from zambeze.orchestration.zambeze_types import MessageType
from zambeze.orchestration.plugins import Plugins

# Standard imports
import pytest
import time


@pytest.mark.unit
def test_factory_fail():
    plugins = Plugins()
    msg_factory = MessageFactory(plugins)

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
    status_tuple = msg_factory.createTemplate(MessageType.STATUS)
    """At this point the template can be used to fill in the items required
    to exceute the message after it is sent"""
    print(status_tuple)
    status_tuple[1].message_id = 1
    status_tuple[1].ubmission_time = time.time()

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
def test_factory_activity_template():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    plugins = Plugins()
    msg_factory = MessageFactory(plugins)
    activity_template = msg_factory.createTemplate(
        MessageType.ACTIVITY, "globus", "transfer"
    )[1]
    print(activity_template)
    no_fail = True
    try:
        activity_template.message_id = ""
        activity_template.type = ""
        activity_template.activity_id = ""
        activity_template.agent_id = ""
        activity_template.campaign_id = ""
        activity_template.credential = {}
        activity_template.submission_time = ""
        assert activity_template.body.transfer.type == "synchronous"
        activity_template.body.transfer.items[0].source = ""
        activity_template.body.transfer.items[0].destination = ""
        activity_template.needs = []
    except Exception as e:
        print(e)
        no_fail = False
    assert no_fail


@pytest.mark.unit
def test_factory_success():
    plugins = Plugins()
    msg_factory = MessageFactory(plugins)

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
    status_tuple = msg_factory.createTemplate(MessageType.STATUS)
    """At this point the template can be used to fill in the items required
    to exceute the message after it is sent"""
    status_tuple[1].message_id = 1
    status_tuple[1].submission_time = time.time()
    status_tuple[1].type = ""
    status_tuple[1].activity_id = ""
    status_tuple[1].target_id = ""
    status_tuple[1].campaign_id = ""
    status_tuple[1].agent_id = ""
    status_tuple[1].body = {}

    """Should generate an immutable Status message, it will also verify that
    the correct fields have been included."""
    status_msg = msg_factory.create(status_tuple)

    assert status_msg.type == MessageType.STATUS
