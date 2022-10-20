from abc import ABC, abstractmethod
from ..zambeze_types import MessageType


class AbstractMessage(ABC):

    @abstractmethod
    def __init__(self, message: dict):
        """Will turn the dict into a message, will throw exception if not valid.

        Will not accept an invalid method. Call checkMessage first if you don't
        want to throw an exception. This will overwrite existing content.
        """
        raise NotImplementedError(
            "set - method does not exist for:" f"{self._message_type.value}"
        )

    @property
    @abstractmethod
    def type(self) -> MessageType:
        """Returns the Message type. i.e. ACTIVITY"""
        raise NotImplementedError(
            "type - method does not exist for:" f"{self._message_type.value}"
        )

    @property
    @abstractmethod
    def message(self) -> dict:
        """Returns the Message as a dict"""
        raise NotImplementedError(
            "type - method does not exist for:" f"{self._message_type.value}"
        )


