# Local imports
from zambeze.orchestration.plugin_modules.globus.globus_uri_separator import (
    GlobusURISeparator,
)

# Standard imports
import os
import pwd
import pytest
import socket
import uuid


@pytest.mark.unit
def test_globus_uri_separator():
    separator = GlobusURISeparator()

    UUID = uuid.uuid4()
    URI = f"globus://{UUID}/file.txt"

    split_uri = separator.separate(URI)
    print(split_uri)
    assert split_uri["protocol"] == "globus"
    assert split_uri["uuid"] == str(UUID)
    assert split_uri["path"] == "/"
    assert split_uri["file_name"] == "file.txt"


@pytest.mark.unit
def test_globus_uri_separator2():
    separator = GlobusURISeparator()
    # globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file_path/file.txt
    valid_uuid = str(uuid.uuid4())
    default_uuid = str(uuid.uuid4())
    file_path = "/file_path/"
    file_name = "file.txt"
    uri = "globus://" + valid_uuid + file_path + file_name
    result = separator.separate(uri, default_uuid)

    assert result["uuid"] == valid_uuid
    assert result["path"] == file_path
    assert result["file_name"] == file_name
    assert len(result["error_message"]) == 0


@pytest.mark.unit
def test_globus_uri_separator3():
    separator = GlobusURISeparator()
    # globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/file.txt
    valid_uuid = str(uuid.uuid4())
    default_uuid = str(uuid.uuid4())
    file_path = "/"
    file_name = "file.txt"
    uri = "globus://" + valid_uuid + file_path + file_name
    result = separator.separate(uri, default_uuid)

    assert result["uuid"] == valid_uuid
    assert result["path"] == "/"
    assert result["file_name"] == file_name
    assert len(result["error_message"]) == 0


@pytest.mark.unit
def test_globus_uri_separator4():
    separator = GlobusURISeparator()
    # globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/
    valid_uuid = str(uuid.uuid4())
    default_uuid = str(uuid.uuid4())
    file_path = "/"
    file_name = ""
    uri = "globus://" + valid_uuid + file_path + file_name
    result = separator.separate(uri, default_uuid)

    assert result["uuid"] == valid_uuid
    assert result["path"] == "/"
    assert result["file_name"] == ""
    assert len(result["error_message"]) == 0


@pytest.mark.unit
def test_globus_uri_separator5():
    separator = GlobusURISeparator()
    # "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX "
    valid_uuid = str(uuid.uuid4())
    default_uuid = str(uuid.uuid4())
    file_path = " "
    file_name = ""
    uri = "globus://" + valid_uuid + file_path + file_name
    result = separator.separate(uri, default_uuid)

    assert result["uuid"] == valid_uuid
    assert result["path"] == "/"
    assert result["file_name"] == ""
    assert len(result["error_message"]) == 0


@pytest.mark.unit
def test_globus_uri_separator6():
    separator = GlobusURISeparator()
    # "  globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX "
    valid_uuid = str(uuid.uuid4())
    default_uuid = str(uuid.uuid4())
    file_path = " "
    file_name = ""
    uri = "  globus://" + valid_uuid + file_path + file_name
    result = separator.separate(uri, default_uuid)

    assert result["uuid"] == valid_uuid
    assert result["path"] == "/"
    assert result["file_name"] == ""
    assert len(result["error_message"]) == 0


@pytest.mark.unit
def test_globus_uri_separator7():
    separator = GlobusURISeparator()
    # "globus://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX////file.txt"
    valid_uuid = str(uuid.uuid4())
    default_uuid = str(uuid.uuid4())
    file_path = "////"
    file_name = "file.txt"
    uri = "globus://" + valid_uuid + file_path + file_name
    result = separator.separate(uri, default_uuid)

    assert result["uuid"] == valid_uuid
    assert result["path"] == "/"
    assert result["file_name"] == file_name
    assert len(result["error_message"]) == 0


@pytest.mark.unit
def test_globus_uri_separator8():
    separator = GlobusURISeparator()
    # "globus://////file.txt "
    default_uuid = str(uuid.uuid4())
    file_path = "////"
    file_name = "file.txt"
    uri = "  globus://" + file_path + file_name
    result = separator.separate(uri, default_uuid)

    assert result["uuid"] == default_uuid
    assert result["path"] == "/"
    assert result["file_name"] == file_name
    assert len(result["error_message"]) == 0
