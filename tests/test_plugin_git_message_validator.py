# Local imports
# fmt: off
from zambeze.orchestration.plugin_modules.git.\
    git_message_template_generator import (
        GitMessageTemplateGenerator,
    )
# fmt: on
from zambeze.orchestration.plugin_modules.git.git_message_validator import (
    GitMessageValidator,
)
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, name="test_plugin_git_message_validator")


@pytest.mark.unit
def test_shell_messageTemplate_and_validate():
    instance = GitMessageTemplateGenerator(logger)
    git_template_commit = instance.generate("commit")

    git_template_commit.commit.items[0].source = "file://"
    git_template_commit.commit.destination = "git://"
    git_template_commit.commit.commit_message = ""
    git_template_commit.commit.credentials.user_name = "boby"
    git_template_commit.commit.credentials.access_token = ""
    git_template_commit.commit.credentials.email = "boby@wonder.com"

    print(git_template_commit)
    validator = GitMessageValidator(logger)
    checks = validator.validateMessage(git_template_commit)
    print(checks)
    assert "commit" in checks[0]
    assert checks[0]["commit"][0]
