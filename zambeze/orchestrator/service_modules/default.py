from .service import Service

from copy import deepcopy
# Define our default class 
class Shell(Service):

    def __init__(self):
        self.__name = "shell" 
        pass 
        
    def configure(self, config: dict):
        self.__config = deepcopy(config)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def info(self) -> dict:
        return {}

    def check(self, package: list[dict]) -> dict:
        print("Checking shell service")
        return {"run": False}

    def process(self, package: list[dict]):
        print("Running shell service") 
