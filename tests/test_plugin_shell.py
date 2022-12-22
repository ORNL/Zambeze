# Local imports
import zambeze.orchestration.plugin_modules.shell.shell as shell
from zambeze.orchestration.plugin_modules.shell.shell_message_template_generator import (
    ShellMessageTemplateGenerator, )
from zambeze.orchestration.plugin_modules.shell.shell_message_validator import (
    ShellMessageValidator,
)

# Standard imports
import os
import pytest
import random
import socket

from dataclasses import asdict


@pytest.mark.unit
def test_shell():
    instance = shell.Shell()

    assert instance.name == "shell"

    assert not instance.configured

    assert len(instance.supportedActions) == 0

    config = {}
    instance.configure(config)
    assert instance.configured

    assert len(instance.supportedActions) == 1
    assert "bash" in instance.supportedActions

    assert instance.info["configured"]
    assert instance.info["supported_actions"][0] == "bash"


@pytest.mark.unit
def test_shell_check():

    file_name = "shell_file.txt"
    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name
    original_number = random.randint(0, 100000000000)

    shell_plugin = shell.Shell()

    config = {}
    shell_plugin.configure(config)

    shell_template_generator = ShellMessageTemplateGenerator()
    shell_template = shell_template_generator.generate()
    shell_template.bash.program = "echo"

    name = "John"
    comparison_string = f"My name is: {name} random_number is {original_number}"
    shell_template.bash.args = [
        "My name is: $NAME random_number is $RAN",
        ">",
        str(file_path),
    ]
    shell_template.bash.env_vars = {"NAME": str(name), "RAN": str(original_number)}

    validator = ShellMessageValidator()
    # Checks that the schema is valid
    schema_checks = validator.validateMessage(shell_template)
    assert schema_checks[0]["bash"][0]

    arguments = asdict(shell_template)
    # Checks that plugin can run locally
    run_checks = shell_plugin.check([arguments])
    print(run_checks)

    run_checks = shell_plugin.process([arguments])

    assert os.path.exists(file_path)
    with open(file_path) as f:
        # Now we will verify that it is the same file that was sent
        lines = f.readlines()
        # Should be a single line
        assert lines[0].strip() == comparison_string
