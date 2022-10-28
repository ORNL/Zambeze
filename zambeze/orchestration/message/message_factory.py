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
    def __init__(self, plugins, logger: Optional[logging.Logger] = None):
        self._logger = logger
        self._plugins = plugins

    def createTemplate(
            self,
            message_type: MessageType,
            plugin_name=None,
            args=None) -> tuple:
        """
        Will create a tuple with all the fields needed to built a message
        """
        if message_type == MessageType.ACTIVITY:
            activity = createActivityTemplate()
            if plugin_name is not None:
                activity["body"] = self._plugins.messageTemplate(plugin_name, args)
            return (message_type, activity)
        elif message_type == MessageType.STATUS:
            status = createStatusTemplate
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
                if "plugin" in args[1]["body"]:
                    plugin_name = args[1]["plugin"]
                    results = self._plugins.check(plugin_name, args[1]["body"])
                    if results[0] is False:
                        raise Exception("Invalid plugin message body"
                                        f"{results[1]}")
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
