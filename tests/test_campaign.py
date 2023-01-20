# Local imports
from zambeze.campaign.activities.shell import ShellActivity
from zambeze.campaign.campaign import Campaign
from zambeze.orchestration.identity import valid_uuid

# Standard imports
import pytest
import logging
import pathlib


@pytest.mark.unit
def test_campaign():

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

    assert activity.campaign_id is None

    campaign = Campaign("My test", logger=logger)

    # Check that the campaign id is correctly added to teh activity
    campaign.add_activity(activity)
    assert valid_uuid(campaign.activities[0].campaign_id)
    assert campaign.activities[0].campaign_id == campaign.campaign_id
