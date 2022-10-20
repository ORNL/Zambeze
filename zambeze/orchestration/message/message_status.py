
import logging
from .abstract_message import AbstractMessage, AbstractMessageValidator
from ..zambeze_types import MessageType
from typing import Optional

class MessageStatus(AbstractMessage):
    def __init__(self, logger: Optional[logging.Logger] = None, message: dict) -> None:
        self._message_type = MessageType.STATUS
        self._message = {}

    @property
    def type(self) -> MessageType:
        return self._message_type

    @property
    def message(self) -> dict:
        return self._message
