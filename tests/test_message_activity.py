# Local imports
from zambeze.orchestration.message.activity_message.message_activity import (
    MessageActivity,
)

from zambeze.orchestration.zambeze_types import MessageType
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, "test_message_activity")


@pytest.mark.unit
def test_message_activity_type():
    msg_activity = MessageActivity({}, logger)
    assert msg_activity.type == MessageType.ACTIVITY


def test_message_activity_message():
    msg_activity = MessageActivity({"body": "testing"}, logger)
    assert msg_activity.data["body"] == "testing"


def test_message_activity_immutability():
    """Demonstrate immutability of message once created"""
    msg_activity = MessageActivity({"body": "testing"}, logger)
    failed = False
    try:
        msg_activity.data["new_key"] == "should fail"
    except Exception:
        failed = True
        pass

    assert failed is True
