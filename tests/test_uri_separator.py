# Local imports
from zambeze.orchestration.uri_separator import URISeparator

# Standard imports
import pytest
import uuid


@pytest.mark.unit
def test_uri_separator1():
    separator = URISeparator()

    URI = "file://dir1/file.txt"

    split_uri = separator.separate(URI)
    print(split_uri)
    assert split_uri["protocol"] == "file"
    assert split_uri["path"] == "/dir1/"
    assert split_uri["file_name"] == "file.txt"


def test_rsync_uri_separator2():
    separator = URISeparator()

    URI = "rsync://dir1/file.txt"

    split_uri = separator.separate(URI)
    print(split_uri)
    assert split_uri["protocol"] == "rsync"
    assert split_uri["path"] == "/dir1/"
    assert split_uri["file_name"] == "file.txt"


@pytest.mark.unit
def test_uri_separator3():
    separator = URISeparator()
    URI = "git://org1/awesome_proj/main/file.txt"

    split_uri = separator.separate(URI)

    assert split_uri["protocol"] == "git"
    assert split_uri["project"] == "awesome_proj"
    assert split_uri["owner"] == "org1"
    assert split_uri["branch"] == "main"
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == "file.txt"


@pytest.mark.unit
def test_globus_uri_separator4():
    separator = URISeparator()

    UUID = uuid.uuid4()
    URI = f"globus://{UUID}/file.txt"

    split_uri = separator.separate(URI)
    print(split_uri)
    assert split_uri["protocol"] == "globus"
    assert split_uri["uuid"] == str(UUID)
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == "file.txt"
