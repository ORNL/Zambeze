
from abc import abstractmethod 
from abc import ABC

class Service(ABC):

    @abstractmethod
    def __init__(self):
        raise NotImplementedError("process method of derived service must be implemented.")

    @abstractmethod
    def configure(self, config: dict):
        raise NotImplementedError("for configuring service.")

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the service, should be lower case"""
        raise NotImplementedError("name method of derived service must be implemented.")

    @abstractmethod
    def process(self, package: dict):
        raise NotImplementedError("process method of derived service must be implemented.")
