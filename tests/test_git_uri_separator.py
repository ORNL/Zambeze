# Local imports
from zambeze.orchestration.plugin_modules.git.git_uri_separator import GitURISeparator
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, name="test_git_uri_separtor")

@pytest.mark.unit
def test_git_uri_separator1():
    separator = GitURISeparator(logger)
    URI = "git://org1/awesome_proj/main/file.txt"

    split_uri = separator.separate(URI)

    assert split_uri["protocol"] == "git"
    assert split_uri["project"] == "awesome_proj"
    assert split_uri["owner"] == "org1"
    assert split_uri["branch"] == "main"
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == "file.txt"


@pytest.mark.unit
def test_git_uri_separator2():
    separator = GitURISeparator(logger)
    URI = "git://org1/awesome_proj/main/dir1/dir2/file.txt"

    split_uri = separator.separate(URI)

    assert split_uri["protocol"] == "git"
    assert split_uri["project"] == "awesome_proj"
    assert split_uri["owner"] == "org1"
    assert split_uri["branch"] == "main"
    assert split_uri["path"] == "/dir1/dir2/"
    assert split_uri["file_name"] == "file.txt"
