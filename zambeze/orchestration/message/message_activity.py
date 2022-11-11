import logging
from .abstract_message import AbstractMessage
from ..zambeze_types import MessageType
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageActivity(AbstractMessage):
    def __init__(
        self, new_message: dict, logger: Optional[logging.Logger] = None
    ) -> None:
        super().__init__()
        object.__setattr__(self, "type", MessageType.ACTIVITY)
        object.__setattr__(self, "message", new_message)
