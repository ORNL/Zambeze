# Local imports
import zambeze.orchestration.plugin_modules.git as git

# Standard imports
import os
import pytest
import random


@pytest.mark.gitlab_runner
def test_git_checkCommitSuccess():
    """Tests that the Git Plugin correctly verifies the json dict used to make
    a commit to a file.

    Test will create a file and then upload it to the GitHub Repo. The file
    will contain a single random number.
    """

    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit.txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    package = [
        {
            "commit": {
                "repo": "TestRepo",
                "owner": "Zambeze84",
                "branch": "main",
                "source": {
                    "path": current_dir + "/" + file_name,
                    "type": "posix absolute",
                },
                "destination": {"path": file_name, "type": "GitHub repository root"},
                "commit_message": "Adding a file",
                "credentials": {
                    "user_name": "zambeze84",
                    "access_token": access_token,
                    "email": "zambeze84@gmail.com",
                },
            }
        }
    ]

    git_plugin = git.Git()
    git_plugin.configure({})
    checked_actions = git_plugin.check(package)
    print(checked_actions)
    assert checked_actions["commit"][0]


@pytest.mark.gitlab_runner
def test_git_checkCommitFailure1():
    """This test should fail because the commit package is missing the repo
    key"""
    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit.txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    package = [
        {
            "commit": {
                "owner": "Zambeze84",
                "branch": "main",
                "source": {
                    "path": current_dir + "/" + file_name,
                    "type": "posix absolute",
                },
                "destination": {"path": file_name, "type": "GitHub repository root"},
                "commit_message": "Adding a file",
                "credentials": {
                    "user_name": "zambeze84",
                    "access_token": access_token,
                    "email": "zambeze84@gmail.com",
                },
            }
        }
    ]
    git_plugin = git.Git()
    git_plugin.configure({})
    checked_actions = git_plugin.check(package)
    assert not checked_actions["commit"][0]


@pytest.mark.gitlab_runner
def test_git_checkCommitFailure2():
    """This test should fail because the commit package is missing the
    destination type key"""

    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit.txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    package = [
        {
            "commit": {
                "repo": "TestRepo",
                "owner": "Zambeze84",
                "branch": "main",
                "source": {
                    "path": current_dir + "/" + file_name,
                    "type": "posix absolute",
                },
                "destination": {"path": file_name},
                "commit_message": "Adding a file",
                "credentials": {
                    "user_name": "zambeze84",
                    "access_token": access_token,
                    "email": "zambeze84@gmail.com",
                },
            }
        }
    ]
    git_plugin = git.Git()
    git_plugin.configure({})
    checked_actions = git_plugin.check(package)
    assert not checked_actions["commit"][0]


@pytest.mark.gitlab_runner
def test_git_checkCommitFailure3():
    """This test should fail because the commit package is missing the
    source key"""

    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit.txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    package = [
        {
            "commit": {
                "repo": "TestRepo",
                "owner": "Zambeze84",
                "branch": "main",
                "destination": {"path": file_name, "type": "GitHub repository root"},
                "commit_message": "Adding a file",
                "credentials": {
                    "user_name": "zambeze84",
                    "access_token": access_token,
                    "email": "zambeze84@gmail.com",
                },
            }
        }
    ]
    git_plugin = git.Git()
    git_plugin.configure({})
    checked_actions = git_plugin.check(package)
    assert not checked_actions["commit"][0]


@pytest.mark.gitlab_runner
def test_git_checkCommitFailure4():
    """This test should fail because the commit package is missing the
    credentials key"""

    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit.txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    package = [
        {
            "commit": {
                "repo": "TestRepo",
                "owner": "Zambeze84",
                "branch": "main",
                "source": {
                    "path": current_dir + "/" + file_name,
                    "type": "posix absolute",
                },
                "destination": {"path": file_name, "type": "GitHub repository root"},
                "commit_message": "Adding a file",
            }
        }
    ]
    git_plugin = git.Git()
    git_plugin.configure({})
    checked_actions = git_plugin.check(package)
    assert not checked_actions["commit"][0]


@pytest.mark.gitlab_runner
def test_git_processCommitAndDownload():
    """Tests that the Git Plugin correctly verifies the json dict used to make
    a commit to a file.

    Test will create a file and then upload it to the GitHub Repo. The file
    will contain a single random number.
    """

    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit.txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    package = [
        {
            "commit": {
                "repo": "TestRepo",
                "owner": "Zambeze84",
                "branch": "main",
                "source": {
                    "path": current_dir + "/" + file_name,
                    "type": "posix absolute",
                },
                "destination": {"path": file_name, "type": "GitHub repository root"},
                "commit_message": "Adding a file",
                "credentials": {
                    "user_name": "zambeze84",
                    "access_token": access_token,
                    "email": "zambeze84@gmail.com",
                },
            }
        }
    ]

    git_plugin = git.Git()
    git_plugin.configure({})
    git_plugin.check(package)
    git_plugin.process(package)

    file_name2 = "demofile_for_git_commit_download.txt"
    package = [
        {
            "download": {
                "repo": "TestRepo",
                "owner": "Zambeze84",
                "branch": "main",
                "destination": {
                    "path": current_dir + "/" + file_name2,
                    "type": "posix absolute",
                },
                "source": {"path": file_name, "type": "GitHub repository root"},
                "credentials": {"access_token": access_token},
            }
        }
    ]

    git_plugin = git.Git()
    git_plugin.configure({})
    git_plugin.check(package)
    git_plugin.process(package)

    with open(file_name2) as f:
        number_from_repo = f.read()

    assert number_from_repo == str(original_number)
