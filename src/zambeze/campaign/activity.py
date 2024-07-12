# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

from typing import Protocol
from zambeze.orchestration.message.abstract_message import AbstractMessage


class Activity(Protocol):
    """Protocol for campaign activities."""

    name: str

    def generate_message(self) -> AbstractMessage: ...
