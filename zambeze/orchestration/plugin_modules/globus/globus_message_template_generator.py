# Local imports
from ..abstract_plugin_template_generator import PluginMessageTemplateGenerator
from ..common_dataclasses import Items, Move, TransferTemplateInner, TransferTemplate
from zambeze.log_manager import LogManager

# Standard imports
from dataclasses import dataclass


class GlobusMessageTemplateGenerator(PluginMessageTemplateGenerator):
    def __init__(self, logger: LogManager) -> None:
        super().__init__("globus", logger=logger)

    def generate(self, args=None):
        if args is None or args == "transfer":
            return TransferTemplate(
                TransferTemplateInner("synchronous", [Move("", "")])
            )
        elif args == "move_to_globus_collection":

            @dataclass
            class MoveToGlobusTemplate:
                move_to_globus_collection: Items

            return MoveToGlobusTemplate(Items([Move()]))
        elif args == "move_from_globus_collection":

            @dataclass
            class MoveFromGlobusTemplate:
                move_from_globus_collection: Items

            return MoveFromGlobusTemplate(Items([Move()]))
        else:
            raise Exception(
                "Unrecognized argument provided, cannot generate " "messageTemplate"
            )
