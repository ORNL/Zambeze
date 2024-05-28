# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import importlib.metadata

from .campaign import Activity, Campaign
from .campaign.activities import ShellActivity, TransferActivity, PythonActivity

__author__ = "https://zambeze.org"
__credits__ = "Oak Ridge National Laboratory"
__version__ = importlib.metadata.version("zambeze")

__all__ = ["Activity", "Campaign", "ShellActivity", "PythonActivity", "TransferActivity"]
