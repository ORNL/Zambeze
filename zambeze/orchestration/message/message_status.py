
import logging
from .abstract_message import AbstractMessage
from ..zambeze_types import MessageType
from typing import Optional


class MessageStatus(AbstractMessage):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._message_type = MessageType.STATUS
        self._required_keys = ["activity_id", "campaign_id", "agent_id",
        "status"]

    @property
    def type(self) -> MessageType:
        return self._message_type

    @property
    def supportedKeys(self) -> list[str]:
        return self._required_keys

    @property
    def requiredKeys(self) -> list[str]:
        return self._required_keys
