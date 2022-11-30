# Standard imports
from dataclasses import make_dataclass

# Local imports
from ..general_message_components import REQUIRED_GENERAL_COMPONENTS

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


# pyre-ignore[11]
def createActivityTemplate() -> ActivityTemplate:
    return ActivityTemplate(None, None, None, None, None, None, None, None, None)
