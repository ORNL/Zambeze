# Local imports
from zambeze.orchestration.message.message_activity \
        import MessageActivity

from zambeze.orchestration.zambeze_types import MessageType

# Standard imports
import pytest


@pytest.mark.unit
def test_message_activity_type():
    msg_activity = MessageActivity({})
    assert msg_activity.type == MessageType.ACTIVITY


def test_message_activity_message():
    msg_activity = MessageActivity({"body": "testing"})
    assert msg_activity.message["body"] == "testing"


def test_message_activity_immutability():
    """Demonstrate immutability of message once created"""
    msg_activity = MessageActivity({"body": "testing"})
    failed = False
    try:
        msg_activity.message["new_key"] == "should fail"
    except Exception:
        failed = True
        pass

    assert failed is True
