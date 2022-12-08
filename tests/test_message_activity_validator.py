import pytest

from zambeze.orchestration.message.activity_message.message_activity_validator import (
    MessageActivityValidator,
    createActivityTemplate,
)


###############################################################################
# Testing Action: Control
###############################################################################
@pytest.mark.unit
def test_message_activity_validator1():
    """This check should fail because it is a dict"""
    activity_message = {
        "message_id": "",
        "submission_time": "",
        "type": "",
        "activity_id": "",
        "campaign_id": "",
        "credential": {},
        "submission_time": "",
        "body": {},
    }
    validator = MessageActivityValidator()
    result = validator.check(activity_message)
    assert result[0] is False


@pytest.mark.unit
def test_message_activity_validator2():
    """This test should be true all required fields are included

    The following attributes should exist
    message_id: "",
    type: "",
    activity_id: "",
    agent_id: "",
    campaign_id: "",
    credential: {},
    submission_time: "",
    body: {},
    """
    validator = MessageActivityValidator()
    activity_message = createActivityTemplate()
    activity_message.message_id = ""
    activity_message.type = ""
    activity_message.activity_id = ""
    activity_message.agent_id = ""
    activity_message.campaign_id = ""
    activity_message.credential = {}
    activity_message.submission_time = ""
    activity_message.body = {}

    result = validator.check(activity_message)
    assert result[0] is True


@pytest.mark.unit
def test_message_activity_validator3():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    validator = MessageActivityValidator()
    activity_message = createActivityTemplate()
    activity_message.message_id = ""
    activity_message.type = ""
    activity_message.activity_id = ""
    activity_message.agent_id = ""
    activity_message.campaign_id = ""
    activity_message.credential = {}
    activity_message.submission_time = ""
    activity_message.body = {}
    activity_message.needs = []
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
