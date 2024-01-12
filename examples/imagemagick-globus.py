#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
import os

from zambeze import Campaign, ShellActivity, TransferActivity


# FRONTIER_EP_ID = "36d521b3-c182-4071-b7d5-91db5d380d42"
# Current error:
# 'PermissionDenied', 'Error validating login to endpoint \'OLCF DTN (Globus 5) (36d521b3-c182-4071-b7d5-91db5d380d42)\', Error (login)\nEndpoint: OLCF DTN (Globus 5) (36d521b3-c182-4071-b7d5-91db5d380d42)\nServer: 160.91.195.131:443\nMessage: Login Failed\n---\nDetails: 530-Login incorrect. : GlobusError: v=1 c=LOGIN_DENIED\\r\\n530-GridFTP-Message: None of your identities are from domains allowed by resource policies\\r\\n530-GridFTP-JSON-Result: {"DATA_TYPE": "result#1.0.0", "code": "permission_denied", "detail": {"DATA_TYPE": "not_from_allowed_domain#1.0.0", "allowed_domains": ["sso.ccs.ornl.gov", "clients.auth.globus.org"]}, "has_next_page": false, "http_response_code": 403, "message": "None of your identities are from domains allowed by resource policies"}\\r\\n530 End.\\r\\n\n', 'BrF75sUUY')

EP_ID = "1c115272-a3f2-11e9-b594-0e56e8fd6d5a"  # my personal mb-pro.

work_EP_ID = "c9f30df8-4688-11ee-a072-eb83daae1adf"

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
    curr_dir = os.path.dirname(__file__)
    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"globus://{EP_ID}/Users/tylerskluzacek/zambeze/tests/campaigns/imagesequence/{i:02d}.jpg"
            for i in range(1, 11)
        ],
        command="convert",
        arguments=[
            "-delay",
            "20",
            "-loop",
            "0",
            f"*.jpg",
            "a.gif",
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars={"PATH": "${PATH}:/opt/homebrew/bin"},
    )

    transfer = TransferActivity(
        name="Transfer end result Tyler's personal (non-work) computer",
        source_file=f"globus://{work_EP_ID}/Users/tylerskluzacek/Desktop/tmp_zambeze/a.gif",
        dest_directory=f"globus://{EP_ID}/Users/tylerskluzacek/z_results",
        override_existing=False
    )

    campaign.add_activity(activity)
    campaign.add_activity(transfer)

    # run the campaign
    campaign.dispatch()


if __name__ == "__main__":
    main()