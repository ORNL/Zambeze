# Local imports
from zambeze.campaign.activities.shell import ShellActivity
from zambeze.utils.identity import valid_uuid

# Standard imports
import re
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
        message_id=str(uuid.uuid4()),
    )

    # Keep these.
    assert activity.type == "SHELL"
    assert activity.origin_agent_id is None  # Not packed until it reaches message_handler
    assert valid_uuid(activity.campaign_id)
    assert valid_uuid(activity.activity_id)

    # Pattern for a valid datetime object down to millisecond.
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$'

    # Use the assert statement to check if the timestamp_str matches the pattern
    assert re.match(pattern, activity.submission_time)
    assert activity.plugin_args["shell"] == "bash"
    assert activity.plugin_args["parameters"]["command"] == "convert"
    assert len(activity.arguments) == 6
    assert len(activity.files) == 10
    assert "PATH" in activity.env_vars


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

    # assert activity.agent_id is None
    assert activity.campaign_id is None
    assert activity.message_id is None
    assert valid_uuid(activity.activity_id)
    assert activity.command == "convert"
    assert len(activity.arguments) == 6
    assert "PATH" in activity.env_vars
