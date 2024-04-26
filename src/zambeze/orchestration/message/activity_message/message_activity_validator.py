# Standard imports
from typing import Optional, Any, overload

import logging

# Local imports
from ..abstract_message_validator import AbstractMessageValidator
from .message_activity_template_generator import (
    ActivityTemplate,
    REQUIRED_ACTIVITY_COMPONENTS,
    OPTIONAL_ACTIVITY_COMPONENTS,
)
from zambeze.utils.identity import valid_uuid


class MessageActivityValidator(AbstractMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._required_keys = REQUIRED_ACTIVITY_COMPONENTS.keys()
        self._optional_keys = OPTIONAL_ACTIVITY_COMPONENTS.keys()

    @property
    def supportedKeys(self) -> list[str]:
        return [*self._required_keys, *self._optional_keys]

    @property
    def requiredKeys(self) -> list[str]:
        return self._required_keys

    def _check_uuids(self, message: Any):
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

        if not valid_uuid(message.origin_agent_id, 4):
            return (
                False,
                (
                    "Required origin_agent_id attribute for activity message must"
                    f"be a valid version 4 UUID but is not: {message.origin_agent_id}"
                ),
            )

    @overload
    def check(self, message: Any) -> tuple[bool, str]:
        pass

    def check(self, message) -> tuple[bool, str]:
        if not isinstance(message, ActivityTemplate):
            return (
                False,
                (
                    f"Unsupported argument type dectected {type[message]}"
                    " can only create an activity message with an "
                    "ActivityTemplate"
                ),
            )

        # Simply checks that each required item does not have None as a value
        for attribute in REQUIRED_ACTIVITY_COMPONENTS:
            att = getattr(message, attribute)
            if att is None:
                return False, f"Required attribute is not defined: {attribute}"

        if message.type != "ACTIVITY":
            return (
                False,
                (
                    "Required type attribute for activity message must"
                    f"be ACTIVITY but is instead: {message.type}"
                ),
            )

        self._check_uuids(message)

        if not isinstance(message.submission_time, str):
            return (
                False,
                (
                    "Required submission_time attribute for activity message must"
                    f"be a valid string but is not: {message.message_id}"
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

        return True, ""
