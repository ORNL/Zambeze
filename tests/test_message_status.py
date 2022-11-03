# Local imports
from zambeze.orchestration.message.message_status \
        import MessageStatus

from zambeze.orchestration.zambeze_types import MessageType

# Standard imports
import pytest


@pytest.mark.unit
def test_message_status_type():
    msg_status = MessageStatus({})
    assert msg_status.type == MessageType.STATUS


def test_message_status_message():
    msg_status = MessageStatus({"body": "testing"})
    assert msg_status.message["body"] == "testing"


def test_message_status_immutability():
    """Demonstrate immutability of message once created"""
    msg_status = MessageStatus({"body": "testing"})
    failed = False
    try:
        msg_status.message["new_key"] == "should fail"
    except Exception:
        failed = True
        pass

    assert failed is True
