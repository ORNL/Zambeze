# Local imports
# fmt: off
from zambeze.orchestration.plugin_modules.shell.\
    shell_message_template_generator import ShellMessageTemplateGenerator
# fmt: on
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, name="test_plugin_shell_message_Template_generator")


@pytest.mark.unit
def test_shell_messageTemplate():
    instance = ShellMessageTemplateGenerator(logger)
    shell_template = instance.generate()
    print(shell_template)
    # Shell template should have all the following attributes
    no_fail = True
    try:
        shell_template.bash.program = ""
        shell_template.bash.args = [""]
        shell_template.bash.env_vars = {}
    except Exception as e:
        print(e.message)
        no_fail = False

    assert no_fail
