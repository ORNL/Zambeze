# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from importlib.metadata import version

from .campaign.campaign import Campaign
from .campaign.shell_activity import ShellActivity
from .campaign.transfer_activity import TransferActivity

__author__ = "https://zambeze.org"
__credits__ = "Oak Ridge National Laboratory"
__version__ = version("zambeze")

__all__ = ["Campaign", "ShellActivity", "TransferActivity"]
