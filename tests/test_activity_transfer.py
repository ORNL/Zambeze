# Local imports
from zambeze.campaign.activities.abstract_activity import (
    AttributeType,
    ActivityStatus
)
from zambeze.campaign.activities.transfer import TransferActivity
from zambeze.orchestration.zambeze_types import MessageType
from zambeze.orchestration.identity import validUUID

# Standard imports
import pytest
import logging
import pathlib
import uuid


@pytest.mark.unit
def test_transfer_activity_generate_message():

    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    source = f"rsync://{curr_dir}/../tests/campaigns/imagesequence/1.jpg"
    destination = "rsync://~/file.jpg"
    activity = TransferActivity(
        name="Rsync Transfer",
        items=[
            {
                "source": source,
                "destination": destination
            }
        ],
        logger=logger,
        campaign_id=str(uuid.uuid4()),
        agent_id=str(uuid.uuid4()),
    )

    assert activity.status == ActivityStatus.CREATED

    msg = activity.generate_message()
    assert msg.type == MessageType.ACTIVITY
    assert validUUID(msg.data.agent_id)
    assert validUUID(msg.data.campaign_id)
    assert validUUID(msg.data.message_id)
    assert validUUID(msg.data.activity_id)
    assert len(msg.data.submission_time) > 0
    assert int(msg.data.submission_time) > 0
    assert msg.data.body.type == "TRANSFER"
    assert msg.data.body.parameters.items[0].source == source
    assert msg.data.body.parameters.items[0].destination == destination


@pytest.mark.unit
def test_transfer_activity_generate_message2():
    """Do not include the following:

    campaign_id

    Should fail because before generating the message the campaign_id should
    have been assigned before generating message.
    """

    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    source = f"rsync://{curr_dir}/../tests/campaigns/imagesequence/1.jpg"
    destination = "rsync://~/file.jpg"
    activity = TransferActivity(
        name="Rsync Transfer",
        items=[
            {
                "source": source,
                "destination": destination
            }
        ],
        logger=logger,
        agent_id=str(uuid.uuid4()),
    )

    assert activity.status == ActivityStatus.CREATED

    error_no_campaign_id = False
    try:
        activity.generate_message()
    except Exception:
        error_no_campaign_id = True

    assert error_no_campaign_id


@pytest.mark.unit
def test_transfer_activity_generate_message3():
    """Do not include the following:

    agent_id

    Should fail because before generating the message the agent_id should
    have been assigned before generating message.
    """

    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    source = f"rsync://{curr_dir}/../tests/campaigns/imagesequence/1.jpg"
    destination = "rsync://~/file.jpg"
    activity = TransferActivity(
        name="Rsync Transfer",
        items=[
            {
                "source": source,
                "destination": destination
            }
        ],
        logger=logger,
        campaign_id=str(uuid.uuid4()),
    )

    assert activity.status == ActivityStatus.CREATED

    error_no_agent_id = False
    try:
        activity.generate_message()
    except Exception:
        error_no_agent_id = True

    assert error_no_agent_id


@pytest.mark.unit
def test_transfer_activity_set():
    """Should pass"""
    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    source = f"rsync://{curr_dir}/../tests/campaigns/imagesequence/1.jpg"
    destination = "rsync://~/file.jpg"
    activity = TransferActivity(
        name="Rsync Transfer",
        items=[
            {
                "source": source,
                "destination": destination
            }
        ],
        logger=logger,
        agent_id=str(uuid.uuid4()),
        campaign_id=str(uuid.uuid4()),
    )

    new_source = "rsync://file1.txt"
    new_dest = "rsync://file2.txt"
    activity.set(AttributeType.TRANSFER_ITEMS, {
            "source": new_source,
            "destination": new_dest
        }
    )

    print("Activity after set")
    msg = activity.generate_message()
    assert msg.type == MessageType.ACTIVITY
    assert int(msg.data.submission_time) > 0
    assert msg.data.body.type == "TRANSFER"
    assert len(msg.data.body.parameters.items) == 1
    assert msg.data.body.parameters.items[0].source == new_source
    assert msg.data.body.parameters.items[0].destination == new_dest



