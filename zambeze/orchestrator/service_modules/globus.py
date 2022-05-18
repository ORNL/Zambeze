from copy import deepcopy
from .service import Service

class Globus(Service):

    def __init__(self):
        pass

    def configure(self, config: dict):
        self.__config = deepcopy(config)

    @property
    def name(self) -> str:
        return "globus"

    def process(self, package: dict):
        print("Running Globus service") 
