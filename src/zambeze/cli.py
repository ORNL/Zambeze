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
import time

from datetime import datetime
from importlib.metadata import version
from signal import SIGKILL


logger = logging.getLogger(__name__)


def _get_log_file(log_path):
    """Gets a PurePath object for the log path if it exists.

    Parameters
    ----------
    log_path : str
        Path to the log file.

    Returns
    -------
    tuple
        The first element is a pathlib.Path object if the log file exists, the second element
        is an error message if the log path is invalid.
    """
    log_file = pathlib.Path(log_path) if log_path else None
    if not log_file or not log_file.is_file():
        return (
            None,
            "Log file not found for agent, verify the agent's state with `zambeze status`",
        )
    return log_file, None


def _valid_follow(state, new_state):
    """Checks if the log path has changed in the agent's state and is a valid path.

    The state of the agent updates on events like agent restarts, and the log path may change. If there is
    a change, we need to verify that the new path is valid so that we can safely follow the new log file.
    Otherwise, it is an invalid follow.

    Parameters
    ----------
    state : dict
        The current state of the agent.
    new_state : dict
        The updated state of the agent.

    Returns
    -------
    tuple
        The first element is a boolean indicating whether the log path has changed and is valid,
        the second element is an error message if the new state is invalid.
    """
    mlog_path = new_state.get("log_path")
    if mlog_path != state.get("log_path"):
        mlog_file, err_msg = _get_log_file(mlog_path)
        if err_msg:
            return False, err_msg
        state["log_handle"].close()
        state["log_handle"] = open(mlog_file, "rb")
        state["log_path"] = mlog_path
        return True, None
    return False, None


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

    # Create path for log file
    try:
        fmt = datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")[:-3]
        log_path = logs_base_dir / fmt / "zambeze.log"
        log_path.parent.mkdir(exist_ok=True)
        log_path.touch(exist_ok=True)
    except OSError:
        logger.error(f"Failed to create log file at {log_path}")
        return
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


def logs(mode, num_lines, follow=False):
    """Provides logging information of the agent.

    Parameters
    ----------
    mode : str
        Mode for displaying logs. Can be either 'head' or 'tail'.
    num_lines : int
        Number of lines to display.
    follow : bool
        Boolean whether to follow the log file. Available only in the 'tail' mode.
    """

    # Head mode does not support following logs
    if mode == "head" and follow:
        logger.info("Cannot follow logs in head mode. Exiting...")
        return

    state_path = pathlib.Path.home() / ".zambeze/agent.state"
    if not state_path.is_file():
        logger.info("Agent does not exist, start an agent with `zambeze start`")
        return

    with state_path.open("r") as sf:
        state = json.load(sf)
        state["mtime"] = state_path.stat().st_mtime

        log_file, err_msg = _get_log_file(state.get("log_path"))
        if err_msg:
            logger.error(err_msg)
            return

        if mode == "tail":
            state["log_handle"] = lf = open(log_file, "rb")
            # Seek to the end of the file and read the last `num_lines` lines going backwards.
            # Uses a new line character as a delimiter to count the number of lines seen so far.
            lf.seek(0, os.SEEK_END)
            end = curr = lf.tell()
            seen_lines = 0
            while curr >= 0 and seen_lines < num_lines:
                lf.seek(curr, os.SEEK_SET)
                char = lf.read(1)
                if char == b"\n" and curr != end - 1:
                    seen_lines += 1
                curr -= 1

            if curr < 0:
                lf.seek(0, os.SEEK_SET)

            for line in lf:
                print(line.decode().strip())

            # If follow is set, keep reading the log file for new lines. Upon agent restarts,
            # follow the new log file if the log path has changed
            if follow:
                try:
                    while True:
                        mstate_mtime = state_path.stat().st_mtime
                        if mstate_mtime > state["mtime"]:
                            sf.seek(0, os.SEEK_SET)
                            mstate = json.load(sf)
                            state["mtime"] = mstate_mtime

                            path_change, err_msg = _valid_follow(state, mstate)
                            if err_msg:
                                logger.error(err_msg)
                                break
                            if path_change:
                                lf = state["log_handle"]

                        line = lf.readline()
                        if not line:
                            time.sleep(0.1)
                        else:
                            print(line.decode().strip())
                except KeyboardInterrupt:
                    print()

            lf.close()
        else:
            # Display the first `num_lines` lines of the log file
            with open(log_file, "r") as lf:
                for _ in range(num_lines):
                    line = lf.readline()
                    if not line:
                        break
                    print(line.strip())


def main():
    """
    Main entry point for zambeze command line interface.
    """

    # Command line parser for zambeze
    parser = argparse.ArgumentParser(description="Zambeze command line interface")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("start", help="Start the agent")
    subparsers.add_parser("stop", help="Stop the agent")
    subparsers.add_parser("status", help="Check the status of the agent")
    logs_parser = subparsers.add_parser("logs", help="View logs of the agent")
    logs_parser.add_argument(
        "--mode",
        choices=["head", "tail"],
        default="tail",
        help="Log mode (default: tail)",
    )
    logs_parser.add_argument(
        "--numlines",
        type=int,
        default=10,
        help="Number of lines to display (default: 10)",
    )
    logs_parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Follow the log file",
    )

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
    elif args.command == "logs":
        logs(args.mode, args.numlines, args.follow)
    else:
        print("Use \33[32mzambeze --help\33[0m for zambeze agent commands")
