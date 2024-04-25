# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import argparse
import logging
import pathlib

from zambeze.orchestration.agent.agent import Agent


def run_agent(log_path, debug):
    """
    Run the zambeze agent.
    """

    # Path for config files
    config_path = pathlib.Path.home().joinpath(".zambeze").joinpath("agent.yaml")

    # Configure logging
    agent_logger = logging.getLogger(__name__)
    fh = logging.FileHandler(log_path)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(fmt)

    if debug:
        agent_logger.setLevel(logging.DEBUG)
    else:
        agent_logger.setLevel(logging.INFO)

    agent_logger.addHandler(fh)

    agent_logger.info("*****************************************************")
    agent_logger.info("Creating Zambeze agent subprocess with configuration:")
    agent_logger.info("*****************************************************")
    agent_logger.info(f"Log Path:\t\t{log_path}")
    agent_logger.info(f"Config Path:\t\t{config_path}")
    agent_logger.info(f"Debug Logs:\t\t{debug}")
    agent_logger.info("*****************************************************")

    # Create an agent
    Agent(conf_file=config_path, logger=agent_logger)


def main():
    """
    Main entry point for zambeze agent command line interface.
    """

    # Command line parser for zambeze agent
    parser = argparse.ArgumentParser(description="Zambeze agent command line interface")
    parser.add_argument("-lp", "--log-path", help="path to log files")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="enable debug log level"
    )
    args = parser.parse_args()

    # Get args from command line and run zambeze agent
    log_path = args.log_path
    debug = args.debug
    run_agent(log_path, debug)
