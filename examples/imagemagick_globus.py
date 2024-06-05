"""
Copyright (c) 2022 Oak Ridge National Laboratory.

This program is free software: you can redistribute it and/or modify
it under the terms of the MIT License.
"""

import logging
from zambeze import Campaign, ShellActivity, TransferActivity

EP_ID = "1c115272-a3f2-11e9-b594-0e56e8fd6d5a"  # my personal mb-pro.
work_EP_ID = "c9f30df8-4688-11ee-a072-eb83daae1adf"  # my work mb-pro


def main():
    # logging (for debugging purposes)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[Zambeze Agent] [%(levelname)s] %(asctime)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # create campaign
    campaign = Campaign("My ImageMagick Campaign", logger=logger, force_login=False)

    # define an activity
    dir_path = (
        f"globus://{EP_ID}/Users/tylerskluzacek/zambeze/tests/campaigns/imagesequence/"
    )
    files = [dir_path + f"{i:02d}.jpg" for i in range(1, 11)]

    print(files)

    activity = ShellActivity(
        name="ImageMagick",
        files=files,
        command="convert",
        arguments=["-delay", "20", "-loop", "0", "*.jpg", "a.gif"],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    print(activity.files)

    transfer = TransferActivity(
        name="Transfer end result Tyler's personal (non-work) computer",
        source_target=f"globus://{work_EP_ID}/Users/tylerskluzacek/Desktop/tmp_zambeze/a.gif",
        dest_directory=f"globus://{EP_ID}/Users/tylerskluzacek/z_results",
        override_existing=False,
    )

    print(transfer.activity_type)

    # campaign.add_activity(activity)
    campaign.add_activity(transfer)

    # run the campaign
    campaign.dispatch()


if __name__ == "__main__":
    main()
