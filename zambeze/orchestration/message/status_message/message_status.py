from ..abstract_message import AbstractMessage

from zambeze.log_manager import LogManager
from zambeze.orchestration.zambeze_types import MessageType
from dataclasses import dataclass


@dataclass(frozen=True)
class MessageStatus(AbstractMessage):
    type = MessageType.STATUS
    data = {}

    def __init__(self, new_data: dict, logger: LogManager) -> None:
        object.__setattr__(self, "type", MessageType.STATUS)
        object.__setattr__(self, "data", new_data)
