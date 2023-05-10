# Local imports
from zambeze.orchestration.message.status_message.message_status import MessageStatus

from zambeze.orchestration.zambeze_types import MessageType
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, name="test_message_status")


@pytest.mark.unit
def test_message_status_type():
    msg_status = MessageStatus({}, logger)
    assert msg_status.type == MessageType.STATUS


def test_message_status_message():
    msg_status = MessageStatus({"body": "testing"}, logger)
    assert msg_status.data["body"] == "testing"


def test_message_status_immutability():
    """Demonstrate immutability of message once created"""
    msg_status = MessageStatus({"body": "testing"}, logger)
    failed = False
    try:
        msg_status.data["new_key"] == "should fail"
    except Exception:
        failed = True
        pass

    assert failed is True
