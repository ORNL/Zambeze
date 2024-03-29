# Local imports
# fmt: off
from zambeze.orchestration.plugin_modules.shell.\
    shell_message_template_generator import ShellMessageTemplateGenerator
# fmt: on
from zambeze.orchestration.plugin_modules.shell.shell_message_validator import (
    ShellMessageValidator,
)

# Standard imports
import pytest


@pytest.mark.unit
def test_shell_messageTemplate_and_validate():
    instance = ShellMessageTemplateGenerator()
    shell_template = instance.generate()

    shell_template.bash.program = "echo"
    shell_template.bash.args = ["-E", "My name is $NAME"]
    shell_template.bash.env_vars = {"NAME": "John"}

    validator = ShellMessageValidator()
    checks = validator.validate_message(shell_template)
    assert "bash" in checks[0]
    assert checks[0]["bash"][0]
