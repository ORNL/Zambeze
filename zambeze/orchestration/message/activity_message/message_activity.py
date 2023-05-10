import logging
from ..abstract_message import AbstractMessage

from zambeze.log_manager import LogManager
from zambeze.orchestration.zambeze_types import MessageType
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageActivity(AbstractMessage):
    type = MessageType.ACTIVITY
    data = {}

    def __init__(self, new_data: dict, logger: LogManager) -> None:
        super().__init__()
        object.__setattr__(self, "type", MessageType.ACTIVITY)
        object.__setattr__(self, "data", new_data)
