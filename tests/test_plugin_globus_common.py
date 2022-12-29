# Local imports
from zambeze.orchestration.plugin_modules.globus.globus_common import (
    checkAllItemsHaveValidEndpoints,
    getGlobusScopes,
    getMappedCollections
)

# Standard imports
import os
import pytest
import uuid

GITLAB_RUNNER_UUIDs = ["f4e5e85c-3a35-455f-9d91-1ee3a0564935"]


@pytest.mark.unit
def test_getMappedCollections():
    config = {
        "local_endpoints": [
            {
                "uuid": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                "path": "/here/file",
                "type": "guest",
            },
            {
                "uuid": "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
                "path": "/there/file2",
                "type": "mapped",
            },
        ]
    }

    mapped_coll_UUIDs = getMappedCollections(config)

    assert len(mapped_coll_UUIDs) == 1
    assert mapped_coll_UUIDs[0] == "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY"


@pytest.mark.unit
def test_getGlobusScopes():
    mapped_collections = []
    scopes = getGlobusScopes(mapped_collections)
    assert scopes == "urn:globus:auth:scope:transfer.api.globus.org:all"

    # These are invalid entries so they will be ignored
    mapped_collections = ["", "XXXX"]
    scopes = getGlobusScopes(mapped_collections)
    assert scopes == "urn:globus:auth:scope:transfer.api.globus.org:all"

    # Though the middle entry is not really a valid UUID it is 36 chars so
    # it should be passed as a valid scope
    mapped_collections = [
        "",
        "YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY",
        "XXXX",
        "ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ",
    ]

    scopes = getGlobusScopes(mapped_collections)

    correct_scopes = "urn:globus:auth:scope:transfer.api.globus.org:all\
[*https://auth.globus.org/scopes/\
YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY/data_access\
 *https://auth.globus.org/scopes/\
ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ/data_access]"

    assert scopes == correct_scopes


@pytest.mark.unit
def test_checkAllItemsHaveValidEndpoints():
    file_name = "demofile_checkAllItemsHaveValidEndpoints.txt"
    f = open(file_name, "w")
    f.write("Testing for valid source file for test_checkAllItemsHaveValidEndpoints")
    f.close()

    current_valid_path = os.getcwd()
    file_path = current_valid_path + "/" + file_name

    file_name2 = "demofile2_checkAllItemsHaveValidEndpoints.txt"
    f = open(file_name2, "w")
    f.write("Testing for valid source file for test_checkAllItemsHaveValidEndpoints")
    f.close()

    file_path2 = current_valid_path + "/" + file_name2

    random_uuid = str(uuid.uuid4())

    items = [
        {
            "source": "file://" + file_path,
            "destination": "globus://" + random_uuid + "/",
        },
        {
            "source": "file://" + file_path2,
            "destination": "globus://" + random_uuid + "/sub_folder/file2.jpeg",
        },
    ]

    supported_source_path_types = ["file"]
    supported_destination_path_types = ["globus"]

    output = checkAllItemsHaveValidEndpoints(
        items, supported_source_path_types, supported_destination_path_types
    )
    assert output[0]

    items2 = [
        {
            "source": "globus://" + random_uuid + file_path,
            "destination": "globus://" + random_uuid + "/",
        }
    ]

    # This should be false because in this case "globus" is not in the
    # supported_source_path_types
    output = checkAllItemsHaveValidEndpoints(
        items2, supported_source_path_types, supported_destination_path_types
    )
    assert not output[0]

    items3 = [{"source": "file://home/cades/file.txt", "destination": "globus://"}]

    # This should be true because in this case "destination" should
    # use the default endpoint uuid
    output = checkAllItemsHaveValidEndpoints(
        items3, supported_source_path_types, supported_destination_path_types
    )
    assert output[0]
