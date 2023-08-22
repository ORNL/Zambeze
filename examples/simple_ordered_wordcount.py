#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import os

from zambeze import Campaign, ShellActivity


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
    campaign = Campaign("My Simple Ordered Wordcount Campaign", logger=logger)

    # define an activity
    curr_dir = os.path.dirname(__file__)
    activity_1 = ShellActivity(
        name="Simple Ordered Wordcount (Oz)",
        files=[f"{curr_dir}/wordcount.py"],
        command="python3",
        arguments=[
            f"{curr_dir}/wordcount.py",
            "--textfile",
            f"{curr_dir}/wizard_of_oz_book.txt",
            "--name",
            "oz"
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    activity_2 = ShellActivity(
        name="Simple Ordered Wordcount (Gatsby)",
        files=[f"{curr_dir}/wordcount.py"],
        command="python3",
        arguments=[
            f"{curr_dir}/wordcount.py",
            "--textfile",
            f"{curr_dir}/gatsby_book.txt",
            "--name",
            "gatsby"
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    activity_3 = ShellActivity(
        name="Merge wordcounts",
        files=[f"{curr_dir}/oz_counts.json", f"{curr_dir}/gatsby_counts.json"],
        command="python3",
        arguments=[
            f"{curr_dir}/merge_counts.py",
            f"{curr_dir}/wizard_of_oz_book.txt"
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    campaign.add_activity(activity_1)
    campaign.add_activity(activity_2)
    campaign.add_activity(activity_3)

    # run the campaign
    campaign.dispatch()


if __name__ == "__main__":
    main()
