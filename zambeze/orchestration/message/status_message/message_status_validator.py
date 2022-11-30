# Standard imports
from typing import Optional, Any, overload

import logging

# Local imports
from ..abstract_message_validator import AbstractMessageValidator
from .message_status_template_generator import (
        REQUIRED_STATUS_COMPONENTS,
        StatusTemplate
)


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

        for attribute in REQUIRED_STATUS_COMPONENTS:
            att = getattr(message, attribute)
            if att is None:
                return (False, f"Required attribute is not defined: {attribute}")

        return (True, "")
