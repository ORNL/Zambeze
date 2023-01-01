# Local imports
from zambeze.orchestration.plugin_modules.rsync.rsync_uri_separator import (
    RsyncURISeparator,
)

# Standard imports
import pytest


@pytest.mark.unit
def test_rsync_uri_separator():
    separator = RsyncURISeparator()

    URI = "rsync://dir1/file.txt"

    split_uri = separator.separate(URI)
    print(split_uri)
    assert split_uri["protocol"] == "rsync"
    assert split_uri["path"] == "/dir1/"
    assert split_uri["file_name"] == "file.txt"
