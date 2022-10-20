import pytest

from zambeze.orchestration.message.message_status_validator \
        import MessageStatusValidator


###############################################################################
# Testing Action: Control
###############################################################################
@pytest.mark.unit
def test_message_status_validator():
    status_message = {
        "message_id": "",
        "submission_time": "",
        "type": "",
        "activity_id": "",
    }
    validator = MessageStatusValidator()
    result = validator.check(status_message)
    assert result[0] is False


