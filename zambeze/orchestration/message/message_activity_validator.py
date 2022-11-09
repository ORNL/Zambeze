import logging
from .abstract_message_validator import AbstractMessageValidator
from typing import Optional


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


def createActivityTemplate() -> dict:
    return {**REQUIRED_ACTIVITY_COMPONENTS, **OPTIONAL_ACTIVITY_COMPONENTS}


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

    def check(self, message: dict) -> (bool, str):

        missing_items = set(self._required_keys).difference(message.keys())
        if len(missing_items):
            return (False, f"Missing required keys from message {missing_items}")

        optional_items = set(message.keys()).difference(self._required_keys)
        unsupported_items = set(optional_items).difference(self._optional_keys)
        if len(unsupported_items):
            return (False, f"Unsupported keys detected {unsupported_items}")

        return (True, "")