# Local imports
from zambeze.orchestration.plugin_modules.git.git_uri_separator import GitURISeparator

# Standard imports
import os
import pwd
import pytest
import socket


@pytest.mark.unit
def test_git_uri_separator1():
    separator = GitURISeparator()
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
    separator = GitURISeparator()
    URI = "git://org1/awesome_proj/main/dir1/dir2/file.txt"

    split_uri = separator.separate(URI)

    assert split_uri["protocol"] == "git"
    assert split_uri["project"] == "awesome_proj"
    assert split_uri["owner"] == "org1"
    assert split_uri["branch"] == "main"
    assert split_uri["path"] == "/dir1/dir2/"
    assert split_uri["file_name"] == "file.txt"
