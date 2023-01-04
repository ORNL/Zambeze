# Local imports
from zambeze.campaign.activities.abstract_activity import (
    AttributeType,
    ActivityStatus
)
from zambeze.campaign.activities.shell import ShellActivity
from zambeze.orchestration.zambeze_types import MessageType
from zambeze.orchestration.identity import validUUID

# Standard imports
import pytest
import logging
import pathlib
import uuid


@pytest.mark.unit
def test_shell_activity_generate_message():

    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"file://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
            for i in range(1, 11)
        ],
        command="convert",
        arguments=[
            "-delay",
            "20",
            "-loop",
            "0",
            f"{curr_dir}/../tests/campaigns/imagesequence/*.jpg",
            "a.gif",
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "$PATH:/opt/homebrew/bin"},
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
    assert msg.data.body.type == "SHELL"
    assert msg.data.body.shell == "bash"
    assert len(msg.data.body.files) > 0
    assert msg.data.body.parameters.program == "convert"
    assert len(msg.data.body.parameters.args) == 6
    assert "PATH" in msg.data.body.parameters.env_vars


@pytest.mark.unit
def test_shell_activity_set():

    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"file://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
            for i in range(1, 11)
        ],
        command="convert",
        arguments=[
            "-delay",
            "20",
            "-loop",
            "0",
            f"{curr_dir}/../tests/campaigns/imagesequence/*.jpg",
            "a.gif",
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "$PATH:/opt/homebrew/bin"},
        campaign_id=str(uuid.uuid4()),
        agent_id=str(uuid.uuid4()),
    )

    activity.set(AttributeType.FILES, ["file://test.txt"])
    activity.set(AttributeType.COMMAND, "echo")
    activity.set(AttributeType.ARGUMENTS, ["Hello"])

    msg = activity.generate_message()
    assert msg.type == MessageType.ACTIVITY
    assert int(msg.data.submission_time) > 0
    assert msg.data.body.type == "SHELL"
    assert msg.data.body.shell == "bash"
    assert len(msg.data.body.files) == 1
    assert msg.data.body.parameters.program == "echo"
    assert len(msg.data.body.parameters.args) == 1


@pytest.mark.unit
def test_shell_activity_set2():
    """Should fail because shell_activity does not support TRANSFER_ITEMS"""

    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"file://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
            for i in range(1, 11)
        ],
        command="convert",
        arguments=[
            "-delay",
            "20",
            "-loop",
            "0",
            f"{curr_dir}/../tests/campaigns/imagesequence/*.jpg",
            "a.gif",
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "$PATH:/opt/homebrew/bin"},
        campaign_id=str(uuid.uuid4()),
        agent_id=str(uuid.uuid4()),
    )

    throw_error = False
    try:
        activity.set(
            AttributeType.TRANSFER_ITEMS, {
                "source": "file1.txt",
                "destination": "path/file1.txt"
            }
        )
    except Exception:
        throw_error = True

    assert throw_error


@pytest.mark.unit
def test_shell_activity_attributes():
    # Don't specify agent_id and campaign_id
    logger = logging.getLogger(__name__)
    curr_dir = pathlib.Path().resolve()
    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"file://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
            for i in range(1, 11)
        ],
        command="convert",
        arguments=[
            "-delay",
            "20",
            "-loop",
            "0",
            f"{curr_dir}/../tests/campaigns/imagesequence/*.jpg",
            "a.gif",
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "$PATH:/opt/homebrew/bin"},
    )

    assert activity.agent_id is None
    assert activity.campaign_id is None
    assert activity.message_id is None
    assert validUUID(activity.activity_id)
    assert activity.command == "convert"
    assert len(activity.arguments) == 6
    assert "PATH" in activity.env_vars
