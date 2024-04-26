# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import argparse
import json
import logging
import os
import pathlib
import subprocess

from datetime import datetime
from importlib.metadata import version
from signal import SIGKILL


logger = logging.getLogger(__name__)


def start():
    """
    Start Zambeze agent as its own daemonized subprocess. This will write logs
    to a user's ~/.zambeze directory and automatically select ports for both
    data and heartbeat communications.
    """
    logger.info("Initializing zambeze agent...")

    # Create base logging directory
    logs_base_dir = pathlib.Path.home() / ".zambeze/logs"

    # First check to make sure no agents already running!
    state_path = pathlib.Path.home() / ".zambeze/agent.state"

    if state_path.is_file():
        with state_path.open("r") as f:
            old_state = json.load(f)
        if old_state["status"] == "RUNNING":
            msg = "ERROR. Agent already running. Please stop agent before running a new one!"
            logger.info(msg)

    # Ensure that we have a folder in which to write logs
    try:
        logs_base_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.error(f"Failed to create log directory at {logs_base_dir}")
        return

    # Create directory for log files
    fmt = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")[:-3]
    log_dir_path = pathlib.Path.home() / ".zambeze/logs" / fmt
    log_dir_path.mkdir(exist_ok=True)
    log_path = log_dir_path / "zambeze.log"
    logger.info(f"Log path is {log_path}")

    # Pass stdout/stderr to devnull (in subprocesses) to avoid memory issues.
    devnull = open(os.devnull, "wb")

    # Open the subprocess and save the process state to file (for future access).
    arg_list = ["zambeze-agent", "--log-path", str(log_path), "--debug"]
    proc = subprocess.Popen(arg_list, stdout=devnull, stderr=devnull)
    logger.info(f"Started agent with PID: {proc.pid}")

    agent_state = {
        "pid": proc.pid,
        "log_path": str(log_path),
        "status": "RUNNING",
    }

    with state_path.open("w") as f:
        json.dump(agent_state, f)


def stop():
    """
    Stop a user's running Zambeze agent.
    """
    logger.info("Received stop signal")

    old_state = {}

    # Check to make sure agent is *supposed to be* running.
    state_path = pathlib.Path.home() / ".zambeze/agent.state"

    if state_path.is_file():
        with state_path.open("r") as f:
            old_state = json.load(f)
        if old_state["status"] in ["STOPPED", "INITIALIZED"]:
            logger.info("Agent is already stopped, exiting...")
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
        msg = "Process ID does not exist, agent already terminated. Cleaning up..."
        logger.debug(msg)

    # Reset state to be correct.
    old_state["status"] = "STOPPED"
    old_state["pid"] = None
    old_state["zmq_heartbeat_port"] = None
    old_state["zmq_activity_port"] = None

    # Flush state to disk.
    with state_path.open("w") as f:
        json.dump(old_state, f)

    logger.info("Agent successfully stopped!")


def status():
    """
    Status of the zambeze agent.
    """
    state_path = pathlib.Path.home() / ".zambeze/agent.state"

    if not state_path.is_file():
        msg = "Agent does not exist, start an agent with `zambeze start`"
        logger.info(msg)
        return

    with state_path.open("r") as f:
        old_state = json.load(f)

    logger.info(f"Agent status is {old_state['status']}")


def main():
    """
    Main entry point for zambeze command line interface.
    """

    # Command line parser for zambeze
    parser = argparse.ArgumentParser(description="Zambeze command line interface")

    commands = ["start", "stop", "status"]
    parser.add_argument("command", choices=commands, nargs="?", help="agent commands")

    parser.add_argument("-c", "--config", action="store_true", help="blah blah")
    parser.add_argument("-v", "--version", action="version", version=version("zambeze"))
    args = parser.parse_args()

    # Configure logging
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(fmt)

    logger.addHandler(ch)

    # Handle commands
    if args.command == "start":
        start()
    elif args.command == "stop":
        stop()
    elif args.command == "status":
        status()
    else:
        print("Use \33[32mzambeze --help\33[0m for zambeze agent commands")
