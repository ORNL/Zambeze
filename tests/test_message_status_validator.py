import pytest

from zambeze.orchestration.message.status_message.message_status_validator import (
    MessageStatusValidator,
)
from zambeze.orchestration.message.status_message.message_status_template_generator import (
    createStatusTemplate, )


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
    """This test should be false all required fields are included but they
    are not defined.

    Should contain the following attributes

    message_id: "",
    submission_time: "",
    activity_id: "",
    type: "",
    target_id: "",
    campaign_id: "",
    agent_id: "",
    body: {}
    """
    validator = MessageStatusValidator()
    status_message = createStatusTemplate()
    result = validator.check(status_message)
    assert result[0] is False


@pytest.mark.unit
def test_message_status_validator3():
    """This test should be true all required fields are included and they
    are defined.

    Should contain the following attributes

    message_id: "",
    submission_time: "",
    type: "",
    activity_id: "",
    target_id: "",
    campaign_id: "",
    agent_id: "",
    body: {}
    """
    validator = MessageStatusValidator()
    status_message = createStatusTemplate()
    status_message.message_id = "1"
    status_message.submission_time = "131"
    status_message.type = ""
    status_message.activity_id = ""
    status_message.target_id = ""
    status_message.campaign_id = ""
    status_message.agent_id = ""
    status_message.body = {}

    result = validator.check(status_message)
    assert result[0] is True


@pytest.mark.unit
def test_message_template():
    """This test should fail all required fields are included and they
    are defined, but we are attempting to add an attribute that is not supported

    Should contain the following attributes

    message_id: "",
    submission_time: "",
    type: "",
    activity_id: "",
    target_id: "",
    campaign_id: "",
    agent_id: "",
    body: {}
    """
    status_message = createStatusTemplate()
    status_message.message_id = "1"
    status_message.submission_time = "131"
    status_message.type = ""
    status_message.activity_id = ""
    status_message.target_id = ""
    status_message.campaign_id = ""
    status_message.agent_id = ""
    status_message.body = {}

    failed = False
    try:
        status_message["extra"] = ""
    except Exception:
        failed = True
        pass

    assert failed


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
        "body",
    ]

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
        "body",
    ]

    validator = MessageStatusValidator()
    assert len(required_fields) >= len(validator.supportedKeys)

    for item in required_fields:
        assert item in validator.supportedKeys
