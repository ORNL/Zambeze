# Local imports
from zambeze.orchestration.plugin_modules.file_uri_separator import FileURISeparator
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest
import os

logger = LogManager(logging.DEBUG, name="test_file_uri_separtor")

@pytest.mark.unit
def test_file_uri_separator():
    separator = FileURISeparator(logger)

    URI = "file:/dir1/file.txt"

    split_uri = separator.separate(URI)
    print(split_uri)
    assert split_uri["protocol"] == "file"
    assert split_uri["path"] == "/dir1/"
    assert split_uri["file_name"] == "file.txt"


@pytest.mark.unit
def test_file_uri_separator2():
    separator = FileURISeparator(logging)

    # globus://file_path/file.txt
    file_path = "file_path/"
    file_name = "file.txt"
    uri = "file:///" + file_path + file_name
    split_uri = separator.separate(uri)

    assert split_uri["protocol"] == "file"
    assert split_uri["path"] == os.sep + file_path
    assert split_uri["file_name"] == file_name
    assert len(split_uri["error_message"]) == 0


@pytest.mark.unit
def test_file_uri_separator3():
    separator = FileURISeparator(logging)
    # file://file.txt
    file_path = ""
    file_name = "file.txt"
    uri = "file:///" + file_path + file_name
    split_uri = separator.separate(uri)
    print("split_uri")
    print(split_uri)
    assert split_uri["protocol"] == "file"
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == file_name
    assert len(split_uri["error_message"]) == 0


@pytest.mark.unit
def test_file_uri_separator4():
    separator = FileURISeparator(logging)
    # file:///
    file_path = "/"
    file_name = ""
    uri = "file:///" + file_path + file_name
    split_uri = separator.separate(uri)

    assert split_uri["protocol"] == "file"
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == ""
    assert len(split_uri["error_message"]) == 0


@pytest.mark.unit
def test_file_uri_separator5():
    separator = FileURISeparator(logging)
    # "file:// "
    file_path = " "
    file_name = ""
    uri = "file:///" + file_path + file_name
    split_uri = separator.separate(uri)

    assert split_uri["protocol"] == "file"
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == ""
    assert len(split_uri["error_message"]) == 0


@pytest.mark.unit
def test_file_uri_separator6():
    separator = FileURISeparator(logging)
    # "  file:// "
    file_path = " "
    file_name = ""
    uri = "  file:///" + file_path + file_name
    split_uri = separator.separate(uri)

    assert split_uri["protocol"] == "file"
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == ""
    assert len(split_uri["error_message"]) == 0
