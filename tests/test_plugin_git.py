# Local imports
import zambeze.orchestration.plugin_modules.git as git

# Standard imports
import os
import pwd
import pytest
import random
import socket


@pytest.mark.unit
def test_git_checkCommit():
    """Tests that the Git Plugin correctly verifies the json dict used to make
    a commit to a file.

    Test will create a file and then upload it to the GitHub Repo. The file
    will contain a single random number.
    """
    file_name = "demofile_for_git_commit.txt"
    f = open(file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    package = {
        "commit": {
            "repo": "https://github.com/Zambeze84/TestRepo.git",
            "branch": "main",
            "path": "path to file",
            "commit_message": "Adding a file",
            "credentials": {
                "user_name": "BobMarley",
                "access_token": "user access token",
                "email": "user@awesome.com"
            }
        }
    }

    git_plugin = git.Git()

    checked_actions = git_plugin.check(package)
    assert checked_actions["commit"]
