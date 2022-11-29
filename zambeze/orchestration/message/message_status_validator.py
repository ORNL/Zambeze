import logging
from .abstract_message_validator import AbstractMessageValidator
from typing import Optional

REQUIRED_ACTIVITY_COMPONENTS = {
    "message_id": "",
    "submission_time": "",
    "type": "",
    "activity_id": "",
    "target_id": "",
    "campaign_id": "",
    "agent_id": "",
    "body": {},
}

OPTIONAL_ACTIVITY_COMPONENTS = {}


def createStatusTemplate() -> dict:
    return {**REQUIRED_ACTIVITY_COMPONENTS, **OPTIONAL_ACTIVITY_COMPONENTS}


class MessageStatusValidator(AbstractMessageValidator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._required_keys = REQUIRED_ACTIVITY_COMPONENTS.keys()

    @property
    def supportedKeys(self) -> list[str]:
        return self._required_keys

    @property
    def requiredKeys(self) -> list[str]:
        return self._required_keys

    def check(self, message: dict) -> tuple[bool, str]:

        missing_items = set(self._required_keys).difference(message.keys())
        if len(missing_items):
            return (False, f"Missing required keys from message {missing_items}")

        unsupported_items = set(message.keys()).difference(self._required_keys)
        if len(unsupported_items):
            return (False, f"Unsupported keys detected {unsupported_items}")

        return (True, "")
