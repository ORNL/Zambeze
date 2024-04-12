"""
Command line interface (CLI) for zambeze.
"""

import argparse
import json
import logging
import os
import pathlib
import subprocess

from datetime import datetime
from importlib.metadata import version
from signal import SIGKILL
from zambeze.orchestration.agent.agent import Agent


def start(debug=False, zmq_activity_port=None, zmq_heartbeat_port=None):
    """
    Start the agent (set logger and ZMQ ports).
    """
    config_path = str(pathlib.Path.home().joinpath(".zambeze").joinpath("agent.yaml"))

    # Create a folder for our current agent
    # -- why? Because we now have multiple logs
    # -- (as of now: zambeze, shell stdout, shell stderr)
    # Users can list them in order of date to see which one is latest.
    fmt_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")[:-3]
    log_dir_path = os.path.expanduser("~") + "/.zambeze/logs/" + fmt_str
    os.makedirs(log_dir_path, exist_ok=True)
    log_path = log_dir_path + "/zambeze.log"

    # Log path comes from agents/commands.py
    agent_logger = logging.getLogger('agent')
    fh = logging.FileHandler(log_path)
    formatter = logging.Formatter(
        "[Zambeze Agent] [%(levelname)s] %(asctime)s - %(message)s"
    )
    fh.setFormatter(formatter)

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
    agent_logger.info(f"ZMQ activity port:\t{zmq_activity_port}")
    agent_logger.info(f"ZMQ heartbeat port:\t{zmq_heartbeat_port}")
    agent_logger.info("*****************************************************")

    Agent(conf_file=config_path, logger=agent_logger)


def start_agent(logger, state_path, zambeze_base_dir) -> None:
    """
    Start the agent via the local zambeze-agent utility and save initial state.
    """
    logger.info("Initializing Zambeze Agent...")
    # Create user dir and make sure the base logging path exists.
    logs_base_dir = zambeze_base_dir.joinpath("logs")

    # First check to make sure no agents already running!
    if state_path.is_file():
        with state_path.open("r") as f:
            old_state = json.load(f)
        if old_state["status"] == "RUNNING":
            logger.info(
                "[ERROR] Agent already running. Please stop agent before running a new one!"
            )

    # Ensure that we have a folder in which to write logs.
    try:
        logs_base_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.error(f"Failed to create log directory: {logs_base_dir}")
        return

    # Create a folder for our current agent
    # -- why? Because we now have multiple logs
    # -- (as of now: zambeze, shell stdout, shell stderr)
    # Users can list them in order of date to see which one is latest.
    fmt_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")[:-3]
    log_dir_path = os.path.expanduser("~") + "/.zambeze/logs/" + fmt_str
    os.makedirs(log_dir_path, exist_ok=True)
    log_path = log_dir_path + "/zambeze.log"

    # Leave this print as it is useful to show this information in the console
    print(f"Log path: {log_path}")

    arg_list = ["zambeze", "--run-agent"]
    logger.info(f"Command: {' '.join(arg_list)}")

    # Pass stdout/stderr to devnull (in subprocesses) to avoid memory issues.
    devnull = open(os.devnull, "wb")

    # Open the subprocess and save the process state to file (for future access).
    proc = subprocess.Popen(arg_list, stdout=devnull, stderr=devnull)
    logger.info(f"Started agent with PID: {proc.pid}")

    agent_state = {
        "pid": proc.pid,
        "log_path": log_path,
        "status": "RUNNING",
    }

    with state_path.open("w") as f:
        json.dump(agent_state, f)


def stop_agent(logger, state_path) -> None:
    """
    Stop the agent by killing its system process and updating the state file.
    """
    logger.info("Received stop signal.")

    old_state = {}

    # Check to make sure agent is *supposed to be* running.
    if state_path.is_file():
        with state_path.open("r") as f:
            old_state = json.load(f)
        if old_state["status"] in ["STOPPED", "INITIALIZED"]:
            logger.info("Agent is already STOPPED. Exiting...")
            return

    # Sends kill signal and wait for child process to die.
    logger.info(f"Killing the agent with PID: {old_state['pid']}")
    try:
        os.kill(old_state["pid"], SIGKILL)
        try:
            os.waitpid(old_state["pid"], 0)
        except ChildProcessError:
            # This block just means that 'kill' won the *race*.
            pass

    except ProcessLookupError:
        logger.debug(
            "Process ID does not exist: agent already terminated. Cleaning up..."
        )

    # Reset state to be correct.
    old_state["status"] = "STOPPED"
    old_state["pid"] = None
    old_state["zmq_heartbeat_port"] = None
    old_state["zmq_activity_port"] = None

    # Flush state to disk.
    with state_path.open("w") as f:
        json.dump(old_state, f)

    logger.info("Agent successfully stopped!\n")


def get_status(logger, state_path):
    """
    Get status of the zambeze agent.
    """
    print("get status")

    if not state_path.is_file():
        msg = "Agent does not exist. Start an agent with `zambeze agent start`."
        logger.info(msg)

    with state_path.open("r") as f:
        old_state = json.load(f)

    logger.info(f"Agent Status: {old_state['status']}.")


def main():
    """
    Main entry point for command line interface.
    """

    # Create top-level parser for `zambeze` command
    parser = argparse.ArgumentParser(description="Zambeze command line interface")
    parser.add_argument("-r", "--run-agent", action="store_true", help="run an agent")
    parser.add_argument("-v", "--version", action="version", version=version("zambeze"))
    subparsers = parser.add_subparsers(title="subcommands", help="valid commands")

    # Create sub-parser for the `zambeze agent` sub-command
    parser_agent = subparsers.add_parser("agent", help="control the agent")
    parser_agent.add_argument("command", choices=["start", "stop", "status"])
    parser_agent.add_argument(
        "-d", "--debug", action="store_true", help="enable debug logging"
    )

    # Create sub-parser for the `zambeze config` sub-command
    parser_config = subparsers.add_parser("config", help="user configuration")
    parser_config.add_argument("a", help="an argument")

    args = parser.parse_args()
    print(args)

    # Setup logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = "[Zambeze Agent] [%(levelname)s] %(asctime)s - %(message)s"
    formatter = logging.Formatter(fmt)

    if args.debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Get paths for zambeze directory and agent state file
    zambeze_base_dir = pathlib.Path.home().joinpath(".zambeze")
    state_path = zambeze_base_dir.joinpath("agent.state")

    # Run functions for agent sub-commands
    if args.command == "start":
        start_agent(logger, state_path, zambeze_base_dir)
    elif args.command == "stop":
        stop_agent(logger, state_path)
    elif args.command == "status":
        get_status(logger, state_path)
    elif args.run_agent:
        start()
