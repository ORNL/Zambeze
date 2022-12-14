# Standard imports
from dataclasses import make_dataclass
from typing import Optional, Any, overload

import logging

# Local imports
from ..abstract_message_validator import AbstractMessageValidator
from .message_activity_template_generator import (
    ActivityTemplate,
    REQUIRED_ACTIVITY_COMPONENTS,
    OPTIONAL_ACTIVITY_COMPONENTS,
)
from zambeze.orchestration.identity import validUUID


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

    @overload
    def check(self, message: Any) -> tuple[bool, str]:
        ...

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
                return (False, f"Required attribute is not defined: {attribute}")

        if message.type != "ACTIVITY":
            return (
                False,
                (
                    "Required type attribute for activity message must"
                    f"be ACTIVITY but is instead: {message.type}"
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

        return (True, "")
