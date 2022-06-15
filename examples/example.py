#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import time

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
campaign = Campaign("My ImageMagick Campaign", logger=logger)

# define an activity
activity = ShellActivity(
    name="ImageMagick",
    files=[f"file://{i:02d}.jpg" for i in range(1, 11)],
    command="convert",
    arguments=["-delay", "20", "-loop", "0", "*.jpg", "a.gif"],
    logger=logger,
)
campaign.add_activity(activity)

# run the campaign
time.sleep(1)
campaign.dispatch()
