# Local imports
# fmt: off
from zambeze.orchestration.plugin_modules.rsync.\
    rsync_message_template_generator import RsyncMessageTemplateGenerator
# fmt: on
from zambeze.orchestration.plugin_modules.rsync.rsync_message_validator import (
    RsyncMessageValidator,
)
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, name="test_plugin_rsync_message_validator")


@pytest.mark.unit
def test_rsync_messageTemplate_and_validate():
    instance = RsyncMessageTemplateGenerator(logger)
    rsync_template = instance.generate()

    rsync_template.transfer.type = "synchronous"
    rsync_template.transfer.items[0].source.ip = "128.23.2.1"
    rsync_template.transfer.items[0].source.user = "cades"
    rsync_template.transfer.items[0].source.path = "/home/cades"
    rsync_template.transfer.items[0].destination.ip = "127.0.0.1"
    rsync_template.transfer.items[0].destination.user = "bananas"
    rsync_template.transfer.items[0].destination.path = "/home/bananas"

    validator = RsyncMessageValidator(logger)
    print("******************")
    print("Validating")
    checks = validator.validateMessage(rsync_template)
    print(checks)
    assert "transfer" in checks[0]
    assert checks[0]["transfer"][0]
