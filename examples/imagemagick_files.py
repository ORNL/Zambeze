"""
Example of creating a campaign with a shell activity to create an animated
GIF. The GIF is created from a series of images using the ImageMagick tool.
"""

import logging
from pathlib import Path
from zambeze import Campaign, ShellActivity


def main():
    """
    Run a shell activity campaign to generate an animated GIF.
    """

    # Setup and configure logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(fmt)

    logger.addHandler(ch)

    # Create the campaign
    campaign = Campaign("My ImageMagick Campaign", logger=logger)
    curr_dir = Path.cwd()

    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"local://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
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
        # env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    campaign.add_activity(activity)

    # Run the campaign to execute the shell activity
    campaign.dispatch()


if __name__ == "__main__":
    main()
