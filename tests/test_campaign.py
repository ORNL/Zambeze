# Local imports
from zambeze import ShellActivity
from zambeze import Campaign
from zambeze.utils.identity import valid_uuid

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
        arguments=f"-delay 20 -loop 0 {curr_dir}/../tests/campaigns/imagesequence/*.jpg a.gif",
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "$PATH:/opt/homebrew/bin"},
    )

    assert activity.campaign_id is None

    campaign = Campaign("My test", activities=[activity], logger=logger)

    # Check that the campaign id is correctly added to teh activity
    campaign.add_activity(activity)
    assert valid_uuid(campaign.activities[0].campaign_id)
    assert campaign.activities[0].campaign_id == campaign.campaign_id
