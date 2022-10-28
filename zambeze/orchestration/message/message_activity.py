
import logging
from .abstract_message import AbstractMessage
from ..zambeze_types import MessageType
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageActivity(AbstractMessage):
    def __init__(self, message: dict, logger: Optional[logging.Logger] = None) -> None:
        self._message_type = MessageType.ACTIVITY
        self._message = message

    @property
    def type(self) -> MessageType:
        return self._message_type

    @property
    def message(self) -> dict:
        return self._message
