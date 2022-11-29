import logging
from .abstract_message import AbstractMessage
from ..zambeze_types import MessageType
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageStatus(AbstractMessage):
    type = MessageType.STATUS
    data = {}

    def __init__(self, new_data: dict, logger: Optional[logging.Logger] = None) -> None:
        object.__setattr__(self, "type", MessageType.STATUS)
        object.__setattr__(self, "data", new_data)
