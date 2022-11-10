# Local imports
from zambeze.orchestration.plugin_modules.rsync.rsync_message_helper import (
    RsyncMessageHelper,
)

# Standard imports
import pytest


@pytest.mark.unit
def test_rsync_messageTemplate():

    instance = RsyncMessageHelper()
    rsync_template = instance.messageTemplate()

    assert "plugin" in rsync_template
    assert rsync_template["plugin"] == instance.name
    assert "cmd" in rsync_template
    assert "transfer" in rsync_template["cmd"][0]
    assert "source" in rsync_template["cmd"][0]["transfer"]
    assert "destination" in rsync_template["cmd"][0]["transfer"]


@pytest.mark.unit
def test_rsync_messageTemplate_and_validate():

    instance = RsyncMessageHelper()
    rsync_template = instance.messageTemplate()
    checks = instance.validateMessage(rsync_template["cmd"])
    assert len(checks) == 1
    assert checks[0]["transfer"]
