
import os
import pytest
import subprocess
import time


#@pytest.mark.integration
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

    command = ['python3', image_magick_example]
    # Step 4 launch example
    process = subprocess.Popen(
        command,
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)

    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)
    # Step 5 wait for example to complete
    count = 0
    while not os.path.exists(final_file_path):
        time.sleep(1)
        count += 1
        if count > 3:
            break

    # Step 6 check that a.gif exists
    assert os.path.exists(final_file_path)
