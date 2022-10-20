import logging
from typing import Optional

from .message_activity import MessageActivity
from .message_status import MessageStatus
from .message_activity_validator import MessageActivityValidator
from .message_status_validator import MessageStatusValidator
from .abstract_queue import AbstractMessage
from ..zambeze_types import MessageType


class MessageFactory:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger

    def create(self, message_type: MessageType, args: dict) -> AbstractMessage:
        """Is responsible for creating a Message.
        """
        if message_type == MessageType.ACTIVITY:
            validator = MessageActivityValidator()
            result = validator.check(args)
            if result[0]:
                return MessageActivity(self._logger, args)
            else:
                raise Exception("Invalid activity message: {result[1]}")
        elif message_type == MessageType.STATUS:
            validator = MessageStatusValidator()
            result = validator.check(args)
            if result[0]:
                return MessageStatus(args)
            else:
                raise Exception("Invalid status message: {result[1]}")
        else:
            raise Exception(
                "Unrecognized message type cannot instantiate: " f"{message_type.value}"
            )
