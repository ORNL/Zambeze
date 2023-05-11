# Local imports
# fmt: off
from zambeze.orchestration.plugin_modules.git.\
    git_message_template_generator import GitMessageTemplateGenerator
# fmt: on
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, name="test_plugin_git_message_Template_generator")


@pytest.mark.unit
def test_git_messageTemplateCommit():
    instance = GitMessageTemplateGenerator(logger)
    git_template_commit = instance.generate("commit")
    print(git_template_commit)
    # Shell template should have all the following attributes
    no_fail = True
    try:
        git_template_commit.commit.items[0].source = ""
        git_template_commit.commit.destination = ""
        git_template_commit.commit.commit_message == ""
        git_template_commit.commit.credentials.user_name == ""
        git_template_commit.commit.credentials.access_token == ""
        git_template_commit.commit.credentials.email == ""
    except Exception as e:
        print(e.message)
        no_fail = False

    assert no_fail


@pytest.mark.unit
def test_git_messageTemplateDownload():
    instance = GitMessageTemplateGenerator(logger)
    git_template_download = instance.generate("download")
    print(git_template_download)
    # Shell template should have all the following attributes
    no_fail = True
    try:
        git_template_download.download.items[0].source = ""
        git_template_download.download.destination = ""
        git_template_download.download.credentials.user_name == ""
        git_template_download.download.credentials.access_token == ""
        git_template_download.download.credentials.email == ""
    except Exception as e:
        print(e.message)
        no_fail = False

    assert no_fail
