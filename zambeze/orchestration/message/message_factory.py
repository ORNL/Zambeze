import logging
from typing import Optional

from .message_activity import MessageActivity
from .message_status import MessageStatus
from .abstract_queue import AbstractMessage
from ..zambeze_types import MessageType


class MessageFactory:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger

    def create(self, message_type: MessageType, args: dict) -> AbstractMessage:
        """Is responsible for creating a Message.
        """
        if message_type == MessageType.ACTIVITY:
            return MessageActivity(self._logger)
        elif message_type == MessageType.STATUS:
            return MessageStatus(self._logger)
        else:
            raise Exception(
                "Unrecognized message type cannot instantiate: " f"{message_type.value}"
            )
