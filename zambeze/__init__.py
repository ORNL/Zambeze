#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from .version import __version__  # noqa: F401

from .campaign import Activity, Campaign  # noqa: F401
from .campaign.activities import ShellActivity  # noqa: F401

__author__ = "https://zambeze.org"
__credits__ = "Oak Ridge National Laboratory"

import logging

logging.getLogger("zambeze").addHandler(logging.StreamHandler())
