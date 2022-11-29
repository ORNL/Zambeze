from abc import ABC, abstractmethod


class AbstractMessageValidator(ABC):
    @property
    @abstractmethod
    def supportedKeys(self) -> list[str]:
        """Returns a list of supported keys"""
        raise NotImplementedError("supportedKeys - method does not exist.")

    @property
    @abstractmethod
    def requiredKeys(self) -> list[str]:
        """Return a list of the keys that are required"""
        raise NotImplementedError("requiredKeys - method does not exist.")

    @abstractmethod
    def check(self, message: dict) -> tuple[bool, str]:
        """Return whether message is valid

        :return: if true return true and if false return false with an error
        message
        :rtype: tuple(bool, str)
        """
        raise NotImplementedError("checkMessage - method does not exist.")
