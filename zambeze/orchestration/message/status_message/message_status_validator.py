# Standard imports
from typing import Optional, Any, overload

import logging

# Local imports
from ..abstract_message_validator import AbstractMessageValidator
from .message_status_template_generator import (
    REQUIRED_STATUS_COMPONENTS,
    StatusTemplate,
)
from zambeze.orchestration.identity import validUUID


class MessageStatusValidator(AbstractMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._required_keys = REQUIRED_STATUS_COMPONENTS.keys()

    @property
    def supportedKeys(self) -> list[str]:
        return self._required_keys

    @property
    def requiredKeys(self) -> list[str]:
        return self._required_keys

    @overload
    def check(self, message: Any) -> tuple[bool, str]:
        ...

    def check(self, message) -> tuple[bool, str]:
        """Will ensure that the values of the message have the expected
        format and values"""
        # pyre-ignore[6]
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

        if not validUUID(message.activity_id, 4):
            return (
                False,
                (
                    "Required activity_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.activity_id}"
                ),
            )

        if not validUUID(message.campaign_id, 4):
            return (
                False,
                (
                    "Required campaign_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.campaign_id}"
                ),
            )

        if not validUUID(message.agent_id, 4):
            return (
                False,
                (
                    "Required agent_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.agent_id}"
                ),
            )

        if not validUUID(message.message_id, 4):
            return (
                False,
                (
                    "Required message_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.message_id}"
                ),
            )

        if not validUUID(message.target_id, 4):
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
