from .service import Service

# Define our default class 
class Shell(Service):

    def __init__(self):
       pass 
        
    def configure(self, config: dict):
        self.__config = copy.deepcopy(config)

    @property
    def name(self) -> str:
        return "shell"

    def process(self, package: dict):
        print("Running shell service") 
