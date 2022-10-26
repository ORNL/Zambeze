import logging
from typing import Optional

from .message_activity import MessageActivity
from .message_status import MessageStatus
from .message_activity_validator import (MessageActivityValidator,
                                         createActivityTemplate)
from .message_status_validator import (MessageStatusValidator,
                                       createStatusTemplate)
from .abstract_queue import AbstractMessage
from ..zambeze_types import MessageType


class MessageFactory:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger

    def createTemplate(message_type: MessageType) -> tuple:
        """
        Will create a tuple with all the fields needed to built a message
        """
        if message_type == MessageType.ACTIVITY:
            activity = createActivityTemplate()
            return (message_type, activity)
        elif message_type == MessageType.STATUS:
            status = createStatusTemplate()
            return (message_type, status)
        else:
            raise Exception(
                "Unrecognized message type cannot createTemplate: "
                f"{message_type.value}"
            )

    def create(self, args: tuple) -> AbstractMessage:
        """Is responsible for creating a Message.

        The tuple must be of the form:

        ( MessageType, {} )
        
        """

        if len(args) != 2:
            raise Exception("Malformed input, create method expects tuple of"
                            "length 2")

        if args[0] == MessageType.ACTIVITY:
            validator = MessageActivityValidator()
            result = validator.check(args[1])
            if result[0]:
                return MessageActivity(self._logger, args[1])
            else:
                raise Exception("Invalid activity message: {result[1]}")
        elif args[0] == MessageType.STATUS:
            validator = MessageStatusValidator()
            result = validator.check(args[1])
            if result[0]:
                return MessageStatus(args[1])
            else:
                raise Exception("Invalid status message: {result[1]}")
        else:
            raise Exception(
                "Unrecognized message type cannot instantiate: " f"{args[0].value}"
            )
