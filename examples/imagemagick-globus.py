#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import pathlib

from zambeze import Campaign, ShellActivity

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
campaign = Campaign("My ImageMagick-Globus Campaign", logger=logger)

# define an activity
curr_dir = pathlib.Path().resolve()
activity = ShellActivity(
    name="Globus-ImageMagick",
    files=[
        "globus://ef1a9560-7ca1-11e5-992c-22000b96db58"
        f"/gpfs/alpine/stf019/proj-shared/zambeze/test-images/{i:02d}.jpg"
        for i in range(1, 11)
    ],
    command="convert",
    arguments=[
        "-delay",
        "20",
        "-loop",
        "0",
        "/tmp/*.jpg",
        "a.gif",
    ],
    logger=logger,
    # Uncomment if running on M1 Mac.
    env_vars=[("PATH", "$PATH:/opt/homebrew/bin")],
)
campaign.add_activity(activity)

# run the campaign
campaign.dispatch()
