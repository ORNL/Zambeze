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

    # Rsync template should have all the following attributes
    no_fail = True
    try:
        assert rsync_template.transfer.type == "synchrnous"
        rsync_template.transfer.items[0].source.ip = ""
        rsync_template.transfer.items[0].source.path = ""
        rsync_template.transfer.items[0].source.user = ""
        rsync_template.transfer.items[0].destination.ip = ""
        rsync_template.transfer.items[0].destination.path = ""
        rsync_template.transfer.items[0].destination.user = ""
    except Exception:
        no_fail = False

    assert no_fail


@pytest.mark.unit
def test_rsync_messageTemplate_and_validate():

    instance = RsyncMessageHelper()
    rsync_template = instance.messageTemplate()
    checks = instance.validateMessage([dict(rsync_template)])
    assert len(checks) == 1
    assert checks[0]["transfer"]
