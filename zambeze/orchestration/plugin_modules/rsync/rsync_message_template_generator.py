#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

# Local imports
from ..abstract_plugin_message_template_generator import (
    PluginMessageTemplateGenerator
)
from ..common_dataclasses import (
    Items,
    Move,
    TransferTemplateInner,
    TransferTemplate,
    RsyncItem,
    Endpoints,
    RsyncTransferTemplateInner,
    RsyncTransferTemplate,
)
from .rsync_common import (
    PLUGIN_NAME,
    SUPPORTED_ACTIONS,
    validateRequiredSourceAndDestinationValuesValid,
)

# Standard imports
from typing import Optional

import logging


class RsyncMessageTemplateGenerator(PluginMessageTemplateGenerator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(PLUGIN_NAME, logger=logger)
        self._supported_actions = SUPPORTED_ACTIONS

    def generate(self, args=None):
        """Args can be used to generate a more flexible template. Say for
        instance you wanted to transfer several different items.
        """
        return RsyncTransferTemplate(
            RsyncTransferTemplateInner(
                "synchronous", [Endpoints(RsyncItem("", "", ""), RsyncItem("", "", ""))]
            )
        )
