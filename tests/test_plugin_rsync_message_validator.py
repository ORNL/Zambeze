# Local imports
from zambeze.orchestration.plugin_modules.rsync.rsync_message_validator import (
    RsyncMessageValidator,
)

# Standard imports
import pytest


@pytest.mark.unit
def test_rsync_messageTemplate_and_validate():

    instance = RsyncMessageValidator()
    rsync_template = instance.messageTemplate()
    checks = instance.validateMessage([rsync_template])
    assert len(checks) == 1
    assert checks[0]["transfer"]
