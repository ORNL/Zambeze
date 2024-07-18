"""
Copyright (c) 2022 Oak Ridge National Laboratory.

This program is free software: you can redistribute it and/or modify
it under the terms of the MIT License.
"""

import logging
from zambeze import Campaign, ShellActivity, TransferActivity

FRONTIER_ID = "36d521b3-c182-4071-b7d5-91db5d380d42"
DEFIANT_ID = "e92d23a3-5d3d-4b4a-9239-f9db08d6a8c4"


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
    campaign = Campaign("My AtomAI Campaign", logger=logger, force_login=False)

    # define an activity
    files = [f"globus://{FRONTIER_ID}/ccs/home/tskluzac/atomai_examples/data/training_data.npy"]
    # files = [dir_path + f"{i:02d}.jpg" for i in range(1, 11)]

    activity = ShellActivity(
        name="AtomAI runner",
        files=files,
        command="source",
        arguments=["activate",
                   "atomai_frontier_310",
                   "&&",
                   "python",
                   "/ccs/home/tskluzac/atomai_zambeze_summit/atomai_runner.py"],
        # pin="FRONTIER",
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    # print(activity.files)
    #
    # transfer = TransferActivity(
    #     name="Transfer end result Tyler's personal (non-work) computer",
    #     source_target=f"globus://{work_EP_ID}/Users/6o1/Desktop/tmp_zambeze/a.gif",
    #     dest_directory=f"globus://{EP_ID}/Users/tylerskluzacek/z_results",
    #     override_existing=False,
    # )
    #
    # print(transfer.activity_type)

    campaign.add_activity(activity)
    # campaign.add_activity(transfer)

    # run the campaign
    campaign.dispatch()


if __name__ == "__main__":
    main()
