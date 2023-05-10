# Local imports
# fmt: off
from zambeze.orchestration.plugin_modules.rsync.\
    rsync_message_template_generator import RsyncMessageTemplateGenerator
# fmt: on
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG,
name="test_plugin_rsync_message_template_generator")

@pytest.mark.unit
def test_rsync_messageTemplate():
    instance = RsyncMessageTemplateGenerator(logger)
    rsync_template = instance.generate()
    print(rsync_template)
    # Rsync template should have all the following attributes
    no_fail = True
    try:
        assert rsync_template.transfer.type == "synchronous"
        rsync_template.transfer.items[0].source.ip = ""
        rsync_template.transfer.items[0].source.path = ""
        rsync_template.transfer.items[0].source.user = ""
        rsync_template.transfer.items[0].destination.ip = ""
        rsync_template.transfer.items[0].destination.path = ""
        rsync_template.transfer.items[0].destination.user = ""
    except Exception as e:
        print(e.message)
        no_fail = False

    assert no_fail
