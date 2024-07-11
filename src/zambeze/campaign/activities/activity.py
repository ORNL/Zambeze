# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging
from enum import Enum
from typing import Optional, Protocol
from zambeze.orchestration.message.abstract_message import AbstractMessage


class ActivityStatus(Enum):
    CREATED = 1
    QUEUED = 2
    RUNNING = 3
    COMPLETED = 4
    FAILED = 5


class Activity(Protocol):
    """Protocol for campaign activities."""

    name: str
    files: list[str]
    command: Optional[str]
    arguments: list[str]
    logger: Optional[logging.Logger]
    campaign_id: Optional[str]
    origin_agent_id: Optional[str]
    running_agent_ids: Optional[list[str]]
    message_id: Optional[str]
    activity_id: Optional[str]
    source_file: Optional[str]
    dest_directory: Optional[str]
    override_existing: Optional[bool]
    submission_time: Optional[str]

    def generate_message(self) -> AbstractMessage: ...
