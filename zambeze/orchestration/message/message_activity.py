
import logging
from .abstract_message import AbstractMessage
from ..zambeze_types import MessageType
from typing import Optional


class MessageActivity(AbstractMessage):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._message_type = MessageType.ACTIVITY

    @property
    def type(self) -> MessageType:
        return self._message_type
