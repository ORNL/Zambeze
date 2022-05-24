# Local imports
from .service import Service

# Standard imports
from copy import deepcopy


class Shell(Service):
    """Class serves as an example of a service"""

    def __init__(self):
        self.__name = "shell"
        self.__type = "bash"
        self.__configured = False
        pass

    def configure(self, config: dict):
        self.__config = deepcopy(config)
        self.__configured = True

    @property
    def configured(self) -> bool:
        return self.__configured

    @property
    def name(self) -> str:
        return self.__name

    @property
    def help(self) -> str:
        return "Shell does not require any configuration."

    @property
    def supportedActions(self) -> list[str]:
        return []

    @property
    def info(self) -> dict:
        return {}

    def check(self, arguments: list[dict]) -> dict:
        print("Checking shell service")
        return {"run": False}

    def process(self, arguments: list[dict]):
        if not self.__configured:
            raise Exception("Cannot run shell service, must first be configured.")
        print("Running shell service")
