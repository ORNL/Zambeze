
import logging
from .abstract_message import AbstractMessage, AbstractMessageValidator
from ..zambeze_types import MessageType
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageStatus(AbstractMessage):
    def __init__(self, message: dict, logger: Optional[logging.Logger] = None) -> None:
        self._message_type = MessageType.STATUS
        self._message = {}

    @property
    def type(self) -> MessageType:
        return self._message_type

    @property
    def message(self) -> dict:
        return self._message
