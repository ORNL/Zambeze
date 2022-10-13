from abc import ABC, abstractmethod
from ..zambeze_types import MessageType


class AbstractMessage(ABC):
    @property
    @abstractmethod
    def type(self) -> MessageType:
        """Returns the Message type. i.e. ACTIVITY"""
        raise NotImplementedError(
            "type - method does not exist for:" f"{self._message_type.value}"
        )

    @property
    @abstractmethod
    def supportedKeys(self) -> list[str]:
        """Returns a list of supported keys"""
        raise NotImplementedError(
            "supportedKeys - method does not exist for:" f"{self._message_type.value}"
        )

    @property
    @abstractmethod
    def requiredKeys(self) -> list[str]:
        """Return a list of the keys that are required"""
        raise NotImplementedError(
            "requiredKeys - method does not exist for:" f"{self._message_type.value}"
        )

    @abstractmethod
    def checkMessage(self, message):
        """Return whether message is valid"""
        raise NotImplementedError(
            "checkMessage - method does not exist for:" f"{self._message_type.value}"
        )

    @abstractmethod
    def set(self, message: dict):
        """Will add the dict as a message, will throw exception if not valid.

        Will not accept an invalid method. Call checkMessage first if you don't
        want to throw an exception. This will overwrite existing content.
        """
        raise NotImplementedError(
            "set - method does not exist for:" f"{self._message_type.value}"
        )

