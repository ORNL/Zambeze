import pytest

from zambeze.orchestration.message.message_activity_validator import (
    MessageActivityValidator,
)


###############################################################################
# Testing Action: Control
###############################################################################
@pytest.mark.unit
def test_message_activity_validator1():
    """This check should fail missing required fields"""
    activity_message = {
        "message_id": "",
        "submission_time": "",
        "type": "",
        "activity_id": "",
    }
    validator = MessageActivityValidator()
    result = validator.check(activity_message)
    assert result[0] is False


@pytest.mark.unit
def test_message_activity_validator2():
    """This test should be true all required fields are included"""
    activity_message = {
        "message_id": "",
        "type": "",
        "activity_id": "",
        "agent_id": "",
        "campaign_id": "",
        "credential": {},
        "submission_time": "",
        "body": {},
    }
    validator = MessageActivityValidator()
    result = validator.check(activity_message)
    assert result[0] is True


@pytest.mark.unit
def test_message_activity_validator3():
    """This test should be true all required fields are included as well as all
    optional fields"""
    activity_message = {
        "message_id": "",
        "type": "",
        "activity_id": "",
        "agent_id": "",
        "campaign_id": "",
        "credential": {},
        "submission_time": "",
        "body": {},
        "needs": [],
    }
    validator = MessageActivityValidator()
    result = validator.check(activity_message)
    assert result[0] is True


@pytest.mark.unit
def test_message_activity_validator_required():
    """makes sure all known required keys are accounted for"""
    required_fields = [
        "message_id",
        "type",
        "activity_id",
        "agent_id",
        "campaign_id",
        "credential",
        "submission_time",
        "body",
    ]

    validator = MessageActivityValidator()
    assert len(required_fields) == len(validator.requiredKeys)

    for item in required_fields:
        assert item in validator.requiredKeys


@pytest.mark.unit
def test_message_activity_validator_supported():
    """Ensures supported keys at least contain all required keys"""
    all_fields = [
        "message_id",
        "type",
        "activity_id",
        "agent_id",
        "campaign_id",
        "credential",
        "submission_time",
        "body",
        "needs",
    ]

    validator = MessageActivityValidator()
    assert len(all_fields) >= len(validator.supportedKeys)

    for item in all_fields:
        assert item in validator.supportedKeys
