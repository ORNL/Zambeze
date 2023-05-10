# Local imports
import zambeze.orchestration.plugin_modules.git.git as git
from zambeze.orchestration.plugin_modules.git.git_message_template_generator import (
    GitMessageTemplateGenerator,
)
from zambeze.log_manager import LogManager

# Standard imports
import logging
import os
import pytest
import random
import time

from dataclasses import asdict

logger = LogManager(logging.DEBUG, name="test_plugin_git")


@pytest.mark.gitlab_runner
def test_git_checkCommitSuccess():
    """Tests that the Git Plugin correctly verifies the json dict used to make
    a commit to a file.

    Test will create a file and then upload it to the GitHub Repo. The file
    will contain a single random number.
    """

    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit-" + str(time.time_ns()) + ".txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    generator = GitMessageTemplateGenerator(logger)

    template = generator.generate("commit")

    template.commit.items[0].source = "file://localhost" + current_dir + "/" + file_name
    template.commit.destination = "git://Zambeze84/TestRepo/main/" + file_name
    template.commit.commit_message = ("Adding a file",)
    template.commit.credentials.user_name = "zambeze84"
    template.commit.credentials.access_token = access_token
    template.commit.credentials.email = "zambeze84@gmail.com"

    git_plugin = git.Git()
    git_plugin.configure({})

    arguments = asdict(template)
    print(arguments)
    checked_actions = git_plugin.check([arguments])
    print(checked_actions)
    assert checked_actions[0]["commit"][0]
    os.remove(file_name)


@pytest.mark.gitlab_runner
def test_git_checkCommitFailure1():
    """This test should fail because the commit package is missing the repo
    key"""
    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit-" + str(time.time_ns()) + ".txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    generator = GitMessageTemplateGenerator(logger)

    template = generator.generate("commit")

    template.commit.items[0].source = "file://localhost" + current_dir + "/" + file_name
    template.commit.destination = "git://Zambeze84/main/" + file_name
    template.commit.commit_message = ("Adding a file",)
    template.commit.credentials.user_name = "zambeze84"
    template.commit.credentials.access_token = access_token
    template.commit.credentials.email = "zambeze84@gmail.com"

    git_plugin = git.Git()
    git_plugin.configure({})

    arguments = asdict(template)
    print(arguments)

    checked_actions = git_plugin.check([arguments])
    assert not checked_actions[0]["commit"][0]
    os.remove(file_name)


@pytest.mark.gitlab_runner
def test_git_checkCommitFailure2():
    """This test should fail because the commit package is missing the
    source key"""

    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit-" + str(time.time_ns()) + ".txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()
    generator = GitMessageTemplateGenerator(logger)

    template = generator.generate("commit")

    template.commit.items[0].source = ""
    template.commit.destination = "git://Zambeze84/main/" + file_name
    template.commit.commit_message = ("Adding a file",)
    template.commit.credentials.user_name = "zambeze84"
    template.commit.credentials.access_token = access_token
    template.commit.credentials.email = "zambeze84@gmail.com"

    git_plugin = git.Git()
    git_plugin.configure({})

    arguments = asdict(template)
    print(arguments)
    checked_actions = git_plugin.check([arguments])
    assert not checked_actions[0]["commit"][0]
    os.remove(file_name)


@pytest.mark.gitlab_runner
def test_git_checkCommitFailure3():
    """This test should fail because the commit package is missing the
    credentials key"""

    current_dir = os.getcwd()
    file_name = "demofile_for_git_commit-" + str(time.time_ns()) + ".txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    generator = GitMessageTemplateGenerator(logger)

    template = generator.generate("commit")

    template.commit.items[0].source = "file://localhost" + current_dir + "/" + file_name
    template.commit.destination = "git://Zambeze84/main/" + file_name
    template.commit.commit_message = ("Adding a file",)

    git_plugin = git.Git()
    git_plugin.configure({})

    arguments = asdict(template)
    print(arguments)
    checked_actions = git_plugin.check([arguments])
    assert not checked_actions[0]["commit"][0]
    os.remove(file_name)


@pytest.mark.gitlab_runner
def test_git_processCommitAndDownload():
    """Tests that the Git Plugin correctly verifies the json dict used to make
    a commit to a file.

    Test will create a file and then upload it to the GitHub Repo. The file
    will contain a single random number.
    """

    access_token = os.getenv("ZAMBEZE84_GITHUB_ACCESS_TOKEN")
    current_dir = os.getcwd()

    time_stamp = str(time.time_ns())
    file_name = "demofile_for_git_commit-" + time_stamp + ".txt"
    f = open(current_dir + "/" + file_name, "w")
    original_number = random.randint(0, 100000000000)
    f.write(str(original_number))
    f.close()

    generator = GitMessageTemplateGenerator(logger)

    template = generator.generate("commit")

    print(f"Current dir {current_dir}")

    template.commit.items[0].source = "file://localhost" + current_dir + "/" + file_name
    template.commit.destination = "git://Zambeze84/TestRepo/main/" + file_name
    template.commit.commit_message = "Adding a file"
    template.commit.credentials.user_name = "zambeze84"
    template.commit.credentials.access_token = access_token
    template.commit.credentials.email = "zambeze84@gmail.com"

    print("Template is")
    print(template)
    git_plugin = git.Git()
    git_plugin.configure({})
    arguments = asdict(template)
    git_plugin.check([arguments])
    git_plugin.process([arguments])

    file_name2 = "demofile_for_git_commit_download-" + time_stamp + ".txt"

    template = generator.generate("download")

    template.download.destination = "file://localhost" + current_dir + "/" + file_name2
    template.download.items[0].source = "git://Zambeze84/TestRepo/main/" + file_name
    template.download.credentials.user_name = "zambeze84"
    template.download.credentials.access_token = access_token
    template.download.credentials.email = "zambeze84@gmail.com"

    git_plugin = git.Git()
    git_plugin.configure({})

    arguments = asdict(template)
    git_plugin.check([arguments])

    attempts = 10
    number_from_repo = "NA"
    while True:
        git_plugin.process([arguments])

        with open(file_name2) as f:
            number_from_repo = f.read()

        if number_from_repo == str(original_number):
            break
        if attempts > 10:
            break
        attempts += 1
        time.sleep(1)

    assert number_from_repo == str(original_number)
    os.remove(file_name)
    os.remove(file_name2)
