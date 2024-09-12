"""
Example of counting the number of words in two text files then combine the
results into a total word count result. This creates the following files in
the working directory: gatsby.json, oz.json, and wordcount_summary.txt
"""

import logging
from pathlib import Path
from zambeze import Campaign, ShellActivity


def main():
    """Run several shell activities to count words in text files."""

    # Setup and configure a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[Zambeze Agent] [%(levelname)s] %(asctime)s - %(message)s"
    )
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    # Create activities
    curr_dir = Path.cwd()

    activity_1 = ShellActivity(
        name="Simple Ordered Wordcount (Oz)",
        files=[f"local://{curr_dir}/wordcount.py"],
        command="python",
        arguments=f"{curr_dir}/wordcount.py --textfile {curr_dir}/wizard_of_oz_book.txt --name oz",
        logger=logger,
    )

    activity_2 = ShellActivity(
        name="Simple Ordered Wordcount (Gatsby)",
        files=[f"local://{curr_dir}/wordcount.py"],
        command="python",
        arguments=f"{curr_dir}/wordcount.py --textfile {curr_dir}/gatsby_book.txt --name gatsby",
        logger=logger,
    )

    activity_3 = ShellActivity(
        name="Merge wordcounts",
        files=[],
        command="python",
        arguments=f"{curr_dir}/merge_counts.py --countfiles gatsby.json oz.json",
        logger=logger,
    )

    # Create and dispatch the campaign
    campaign = Campaign("Word count campaign", activities=[activity_1, activity_2, activity_3], logger=logger)
    campaign.dispatch()


if __name__ == "__main__":
    main()
