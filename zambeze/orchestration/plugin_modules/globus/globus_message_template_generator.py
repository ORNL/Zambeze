# Local imports
from ..abstract_plugin_message_template_generator import (
    PluginMessageTemplateGenerator
)
from ..common_dataclasses import Items, Move, TransferTemplateInner, TransferTemplate

# Standard imports
from dataclasses import dataclass
from typing import Optional
import logging


class GlobusMessageTemplateGenerator(PluginMessageTemplateGenerator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("globus", logger=logger)

    def messageTemplate(self, args=None):
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
