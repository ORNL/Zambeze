
from abc import abstractmethod 
from abc import ABC

class Service(ABC):

#    @abstractmethod
    def __init__(self):
        raise NotImplementedError("process method of derived service must be implemented.")

    @abstractmethod
    def configure(self, config: dict):
        raise NotImplementedError("for configuring service.")

    @property
    @abstractmethod
    def info(self) -> dict:
        """This method is to be used after configuration step and will return
        information about the service such as configuration settings and defaults."""
        raise NotImplementedError("returns information about the service.")

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the service, should be lower case"""
        raise NotImplementedError("name method of derived service must be implemented.")

    @abstractmethod
    def check(self, package: list[dict]) -> dict:
        """Determine if the proposed package can be executed by this instance"""

    @abstractmethod
    def process(self, package: list[dict]):
        raise NotImplementedError("process method of derived service must be implemented.")
