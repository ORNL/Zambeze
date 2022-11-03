import pytest

from zambeze.orchestration.message.message_status_validator \
        import MessageStatusValidator


###############################################################################
# Testing Action: Control
###############################################################################
@pytest.mark.unit
def test_message_status_validator1():
    """This check should fail missing required fields"""
    status_message = {
        "message_id": "",
        "submission_time": "",
        "type": "",
        "activity_id": "",
    }
    validator = MessageStatusValidator()
    result = validator.check(status_message)
    assert result[0] is False


@pytest.mark.unit
def test_message_status_validator2():
    """This test should be true all required fields are included"""
    status_message = {
        "message_id": "",
        "submission_time": "",
        "type": "",
        "activity_id": "",
        "target_id": "",
        "campaign_id": "",
        "agent_id": "",
        "body": {}
    }
    validator = MessageStatusValidator()
    result = validator.check(status_message)
    assert result[0] is True


@pytest.mark.unit
def test_message_status_validator_required():
    """makes sure all known required keys are accounted for"""
    required_fields = [
        "message_id",
        "submission_time",
        "type",
        "activity_id",
        "target_id",
        "campaign_id",
        "agent_id",
        "body"]

    validator = MessageStatusValidator()
    assert len(required_fields) == len(validator.requiredKeys)

    for item in required_fields:
        assert item in validator.requiredKeys


@pytest.mark.unit
def test_message_status_validator_supported():
    """Ensures supported keys at least contain all required keys"""
    required_fields = [
        "message_id",
        "submission_time",
        "type",
        "activity_id",
        "target_id",
        "campaign_id",
        "agent_id",
        "body"]

    validator = MessageStatusValidator()
    assert len(required_fields) >= len(validator.supportedKeys)

    for item in required_fields:
        assert item in validator.supportedKeys


