
import logging
from .abstract_message import AbstractMessage
from ..zambeze_types import MessageType
from typing import Optional


class MessageActivity(AbstractMessage):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._message_type = MessageType.ACTIVITY
        self._required_keys = [
                "activity_id",
                "activity_type",
                "campaign_id",
                "agent_id"]
        self._optional_keys = ["action", "needs"]

    @property
    def type(self) -> MessageType:
        return self._message_type

    @property
    def supportedKeys(self) -> list[str]:
        return [*self._required_keys, *self._optional_keys]

    @property
    def requiredKeys(self) -> list[str]:
        return self._required_keys
