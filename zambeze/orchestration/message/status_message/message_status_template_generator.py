# Standard imports
from dataclasses import make_dataclass

# Local imports
from ..general_message_components import REQUIRED_GENERAL_COMPONENTS

REQUIRED_STATUS_COMPONENTS = {
    **REQUIRED_GENERAL_COMPONENTS,
    "activity_id": None,
    "target_id": None,
    "campaign_id": None,
    "body": None,
}

OPTIONAL_STATUS_COMPONENTS = {}

StatusTemplate = make_dataclass(
    "StatusTemplate", {**REQUIRED_STATUS_COMPONENTS, **OPTIONAL_STATUS_COMPONENTS}
)


# pyre-ignore[11]
def createStatusTemplate() -> StatusTemplate:
    return StatusTemplate(None, None, None, None, None, None, None, None)
