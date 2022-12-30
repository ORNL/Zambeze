# Local imports
from zambeze.campaign.activities.shell import ShellActivity
from zambeze.orchestration.zambeze_types import MessageType
from zambeze.orchestration.identity import validUUID

# Standard imports
import pytest
import logging
import pathlib

from dataclasses import asdict


@pytest.mark.unit
def test_shell_activity_type():

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
        env_vars={"PATH", "$PATH:/opt/homebrew/bin"},
    )

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
