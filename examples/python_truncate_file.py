
import logging
from pathlib import Path
from zambeze import Campaign, PythonActivity


def main():
    """
    Run a shell activity campaign to generate an animated GIF.
    """

    # Setup and configure logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(fmt)

    logger.addHandler(ch)

    # Create the campaign
    campaign = Campaign("My Python File Truncation Campaign", logger=logger)
    curr_dir = Path.cwd()

    activity = PythonActivity(
        name="ImageMagick",
        files=[
            f"local://{curr_dir}/../tests/campaigns/imagesequence/{i:02d}.jpg"
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
        py_script_uri=f"{curr_dir}/scripts/python_tests/ml_imports.py",
        env_activation_cmd="conda activate example_env",
        logger=logger
    )

    campaign.add_activity(activity)

    # Run the campaign to execute the shell activity
    campaign.dispatch()


if __name__ == "__main__":
    main()
