# Standard imports
from dataclasses import make_dataclass
from typing import Optional, Any, TypeVar, overload

import logging

# Local imports
from .abstract_message_validator import AbstractMessageValidator

REQUIRED_ACTIVITY_COMPONENTS = {
    "message_id": "",
    "type": "",
    "activity_id": "",
    "agent_id": "",
    "campaign_id": "",
    "credential": {},
    "submission_time": "",
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
        # Change this to checking if the default required values have been set
        # missing_items = set(self._required_keys).difference(message.keys())
        # if len(missing_items):
        #    return (False, f"Missing required keys from message {missing_items}")
        for attribute in REQUIRED_ACTIVITY_COMPONENTS:
            att = getattr(message, attribute)
            if att is None:
                return (False, f"Required attribute is not defined: {attribute}")
        #        optional_items = set(message.keys()).difference(self._required_keys)
        #        unsupported_items = set(optional_items).difference(self._optional_keys)
        #        if len(unsupported_items):
        return (True, "")
