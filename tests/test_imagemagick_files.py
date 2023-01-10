
import os
import pytest
import subprocess
import time

import logging
import os

from zambeze import Campaign, ShellActivity


def image_magic_main():

    # logging (for debugging purposes)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[Zambeze Agent] [%(levelname)s] %(asctime)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # create campaign
    campaign = Campaign("My ImageMagick Campaign", logger=logger)

    # define an activity
    curr_dir = os.path.dirname(__file__)
    activity = ShellActivity(
        name="ImageMagick",
        files=[
            f"file://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
            for i in range(1, 11)
        ],
        command="convert",
        arguments=[
            "-delay",
            "20",
            "-loop",
            "0",
            f"{curr_dir}/../tests/campaigns/imagesequence/*.jpg",
            "a.gif",
        ],
        logger=logger,
        # Uncomment if running on M1 Mac.
        env_vars=[("PATH", "$PATH:/opt/homebrew/bin")],
    )
    campaign.add_activity(activity)

    # run the campaign
    campaign.dispatch()


@pytest.mark.integration
def test_imagemagick_files():
    """This test assumes that docker compose is already up and running with
    two agents and a nats queue"""

    # Step 1 get current working dir
    current_folder = os.path.dirname(__file__)
    print(f"Current folder {current_folder}")
    # Step 2 locate examples folder
    examples_folder = current_folder + "/../examples"
    image_magick_example = examples_folder + "/imagemagick-files.py"
    print(f"image_magick_example {image_magick_example}")

    # Step 3 remove a.gif if exists locally
    home_dir = os.path.expanduser('~')
    print(f"Home dir {home_dir}")

    final_file_path = home_dir + "/a.gif"
    print(f"Final file_path {final_file_path}")
    if os.path.exists(final_file_path):
        os.remove(final_file_path)

    image_magic_main()
    # command = ['python3', image_magick_example]
    #
    # # Step 4 launch example
    # process = subprocess.Popen(
    #     command,
    #     shell=False,
    #     stdout=subprocess.DEVNULL,
    #     stderr=subprocess.STDOUT)
    #
    # stdout, stderr = process.communicate()
    # print(stdout)
    # print(stderr)

    # Step 5 wait for example to complete
    count = 0
    while not os.path.exists(final_file_path):
        print(f"File {final_file_path} does not exist yet. Waiting...")
        time.sleep(1)
        count += 1
        if count > 3:
            break

    # Step 6 check that a.gif exists
    assert os.path.exists(final_file_path)
