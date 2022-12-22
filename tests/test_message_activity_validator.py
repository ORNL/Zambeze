import pytest
import time
import uuid

from zambeze.orchestration.message.activity_message.message_activity_validator import (
    MessageActivityValidator,
)

# fmt: off
from zambeze.orchestration.message.activity_message.\
        message_activity_template_generator import createActivityTemplate
# fmt: on
from zambeze.orchestration.zambeze_types import ActivityType

###############################################################################
# Testing Action: Control
###############################################################################


@pytest.mark.unit
def test_message_activity_validator():
    """This check should fail because a dict is passed to a validator instead
    of an immutable message type."""
    activity_message = {
        "message_id": str(uuid.uuid4()),
        "submission_time": str(int(time.time())),
        "type": "ACTIVITY",
        "activity_id": str(uuid.uuid4()),
        "campaign_id": str(uuid.uuid4()),
        "credential": {},
        "body": {},
    }
    validator = MessageActivityValidator()
    result = validator.check(activity_message)
    assert result[0] is False


@pytest.mark.unit
def test_message_activity_validator_required_shell():
    """This test should be true all required fields are included

    The following attributes should exist
    message_id: "",
    type: "ACTIVITY",
    activity_id: "",
    agent_id: "",
    campaign_id: "",
    credential: {},
    submission_time: "",
    body: {},
    """
    validator = MessageActivityValidator()
    activity_message = createActivityTemplate(ActivityType.SHELL)
    activity_message.message_id = str(uuid.uuid4())
    activity_message.activity_id = str(uuid.uuid4())
    activity_message.agent_id = str(uuid.uuid4())
    activity_message.campaign_id = str(uuid.uuid4())
    activity_message.credential = {}
    activity_message.submission_time = str(int(time.time()))
    assert activity_message.body.type == "SHELL"

    result = validator.check(activity_message)
    assert result[0] is True


@pytest.mark.unit
def test_message_activity_validator_required_plugin():
    """This test should be true all required fields are included

    The following attributes should exist
    message_id: "",
    type: "ACTIVITY",
    activity_id: "",
    agent_id: "",
    campaign_id: "",
    credential: {},
    submission_time: "",
    body: {},
    """
    validator = MessageActivityValidator()
    activity_message = createActivityTemplate(ActivityType.PLUGIN)
    activity_message.message_id = str(uuid.uuid4())
    activity_message.activity_id = str(uuid.uuid4())
    activity_message.agent_id = str(uuid.uuid4())
    activity_message.campaign_id = str(uuid.uuid4())
    activity_message.credential = {}
    activity_message.submission_time = str(int(time.time()))
    assert activity_message.body.type == "PLUGIN"
    result = validator.check(activity_message)
    assert result[0] is True


@pytest.mark.unit
def test_message_activity_validator_required_and_optional_shell():
    """This test should be true all required fields are defined as well as all
    optional fields"""
    validator = MessageActivityValidator()
    activity_message = createActivityTemplate(ActivityType.SHELL)
    activity_message.message_id = str(uuid.uuid4())
    activity_message.activity_id = str(uuid.uuid4())
    activity_message.agent_id = str(uuid.uuid4())
    activity_message.campaign_id = str(uuid.uuid4())
    activity_message.credential = {}
    activity_message.submission_time = str(int(time.time()))
    assert activity_message.body.type == "SHELL"
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
