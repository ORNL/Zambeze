# Standard imports
from dataclasses import make_dataclass
from zambeze.orchestration.zambeze_types import ActivityType

# Local imports
from ..general_message_components import REQUIRED_GENERAL_COMPONENTS

from dataclasses import dataclass
from typing import Optional

REQUIRED_ACTIVITY_COMPONENTS = {
    **REQUIRED_GENERAL_COMPONENTS,
    "activity_id": "",
    "campaign_id": "",
    "credential": {},
    "body": {},
}

OPTIONAL_ACTIVITY_COMPONENTS = {"needs": []}

ActivityTemplate = make_dataclass(
    "ActivityTemplate", {**REQUIRED_ACTIVITY_COMPONENTS, **OPTIONAL_ACTIVITY_COMPONENTS}
)

ShellTemplate = make_dataclass(
    "ShellTemplate", {"type": "SHELL", "shell": "", "files": [""], "parameters": {}}
)

TransferTemplate = make_dataclass(
    "TransferTemplate", {"type": "TRANSFER", "parameters": {}}
)

PluginTemplate = make_dataclass(
    "PluginTemplate", {"type": "PLUGIN", "plugin": "", "parameters": {}}
)


@dataclass
class ShellParams:
    program: Optional[str]
    args: Optional[list]
    env_vars: Optional[dict]


@dataclass
class TransferParams:
    items: Optional[list]


@dataclass
class TransferItem:
    source: Optional[str]
    destination: Optional[str]


# pyre-ignore[11]
def createActivityTemplate(activity_type: ActivityType) -> ActivityTemplate:
    template = ActivityTemplate("", "", "", "", "", "", "", {}, {})
    template.type = "ACTIVITY"
    if activity_type == ActivityType.SHELL:
        template.body = ShellTemplate(
            "SHELL", "", "", ShellParams("", [], {})
        )
    elif activity_type == ActivityType.TRANSFER:
        template.body = TransferTemplate(
                "TRANSFER", TransferParams([TransferItem("", "")]))
    elif activity_type == ActivityType.PLUGIN:
        template.body = PluginTemplate("PLUGIN", "", "")
    else:
        raise Exception("Unsupported ActivitityType specified")
    return template
