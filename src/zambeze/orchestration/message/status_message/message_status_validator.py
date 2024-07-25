# Standard imports
from typing import Optional, Any, overload

import logging

# Local imports
from ..abstract_message_validator import AbstractMessageValidator
from .message_status_template_generator import (
    REQUIRED_STATUS_COMPONENTS,
    StatusTemplate,
)
from zambeze.identity import valid_uuid


class MessageStatusValidator(AbstractMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._required_keys = REQUIRED_STATUS_COMPONENTS.keys()

    @property
    def supportedKeys(self) -> list[str]:
        return self._required_keys

    @property
    def requiredKeys(self) -> list[str]:
        return self._required_keys

    def _checkUUIDs(self, message: Any):
        if not valid_uuid(message.activity_id, 4):
            return (
                False,
                (
                    "Required activity_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.activity_id}"
                ),
            )

        if not valid_uuid(message.campaign_id, 4):
            return (
                False,
                (
                    "Required campaign_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.campaign_id}"
                ),
            )

        if not valid_uuid(message.agent_id, 4):
            return (
                False,
                (
                    "Required agent_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.agent_id}"
                ),
            )

    @overload
    def check(self, message: Any) -> tuple[bool, str]:
        pass

    def check(self, message) -> tuple[bool, str]:
        """Will ensure that the values of the message have the expected
        format and values"""
        if not isinstance(message, StatusTemplate):
            return (
                False,
                (
                    f"Unsupported argument type dectected {type[message]}"
                    " can only create an status message with an "
                    "StatusTemplate"
                ),
            )

        for attribute in REQUIRED_STATUS_COMPONENTS:
            att = getattr(message, attribute)
            if att is None:
                return (False, f"Required attribute is not defined: {attribute}")

        if message.type != "STATUS":
            return (
                False,
                (
                    "Required type attribute for status message must"
                    f"be STATUS but is instead: {message.type}"
                ),
            )

        self._checkUUIDs(message)

        if not valid_uuid(message.target_id, 4):
            return (
                False,
                (
                    "Required target_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.target_id}"
                ),
            )

        is_valid_int = False
        try:
            valid_epoch_time = int(message.submission_time)
            if valid_epoch_time > 0:
                is_valid_int = True
        except Exception:
            pass

        if is_valid_int is False:
            return (
                False,
                (
                    "Required submission_time attribute for activity message must"
                    "be a valid string with an int for the epoc time:"
                    f"{message.submission_time}"
                ),
            )

        return (True, "")
