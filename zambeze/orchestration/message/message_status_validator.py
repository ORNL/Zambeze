# Standard imports
from dataclasses import make_dataclass
from typing import Optional, Any, overload

import logging

# Local imports
from .abstract_message_validator import AbstractMessageValidator

REQUIRED_ACTIVITY_COMPONENTS = {
    "message_id": None,
    "submission_time": None,
    "type": None,
    "activity_id": None,
    "target_id": None,
    "campaign_id": None,
    "agent_id": None,
    "body": None,
}

OPTIONAL_ACTIVITY_COMPONENTS = {}

StatusTemplate = make_dataclass(
    "StatusTemplate", {**REQUIRED_ACTIVITY_COMPONENTS, **OPTIONAL_ACTIVITY_COMPONENTS}
)


# pyre-ignore[11]
def createStatusTemplate() -> StatusTemplate:
    return StatusTemplate(None, None, None, None, None, None, None, None)


class MessageStatusValidator(AbstractMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._required_keys = REQUIRED_ACTIVITY_COMPONENTS.keys()

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

        print(type(message))
        print(type(StatusTemplate))
        if not isinstance(message, StatusTemplate):
            return (
                False,
                (
                    f"Unsupported argument type dectected {type[message]}"
                    " can only create an status message with an "
                    "StatusTemplate"
                ),
            )

        for attribute in REQUIRED_ACTIVITY_COMPONENTS:
            att = getattr(message, attribute)
            if att is None:
                return (False, f"Required attribute is not defined: {attribute}")

        return (True, "")
