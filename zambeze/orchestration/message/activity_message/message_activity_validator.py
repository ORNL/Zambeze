# Standard imports
from dataclasses import make_dataclass
from typing import Optional, Any, overload

import logging

# Local imports
from ..abstract_message_validator import AbstractMessageValidator
from ..general_message_components import REQUIRED_GENERAL_COMPONENTS

REQUIRED_ACTIVITY_COMPONENTS = {
    **REQUIRED_GENERAL_COMPONENTS,
    "activity_id": "",
    "agent_id": "",
    "campaign_id": "",
    "credential": {},
    "body": {},
}

OPTIONAL_ACTIVITY_COMPONENTS = {"needs": []}

ActivityTemplate = make_dataclass(
    "ActivityTemplate", {**REQUIRED_ACTIVITY_COMPONENTS, **OPTIONAL_ACTIVITY_COMPONENTS}
)


# pyre-ignore[11]
def createActivityTemplate() -> ActivityTemplate:
    return ActivityTemplate(None, None, None, None, None, None, None, None, None)


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

        for attribute in REQUIRED_ACTIVITY_COMPONENTS:
            att = getattr(message, attribute)
            if att is None:
                return (False, f"Required attribute is not defined: {attribute}")
        return (True, "")
