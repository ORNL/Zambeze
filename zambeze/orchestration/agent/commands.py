#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import json
import logging
import os
import pathlib
import subprocess
import zmq

from datetime import datetime
from signal import SIGKILL

from zambeze.log_manager import LogManager

# Pass stdout/stderr to devnull (in subprocesses) to avoid memory issues.
devnull = open(os.devnull, "wb")

zambeze_base_dir = pathlib.Path.home().joinpath(".zambeze")
state_path = zambeze_base_dir.joinpath("agent.state")


def agent_start(logger: LogManager, debug: bool = False) -> None:
    """
    Start the agent via the local zambeze-agent utility and save initial state.

    :param logger: The agent logger that writes to ~/.zambeze/logs
    :type logger: logging.Logger
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
                "[ERROR] Agent already running. "
                "Please stop agent before running a new one!"
            )

    # Ensure that we have a folder in which to write logs.
    try:
        logs_base_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.error(f"Failed to create log directory: {logs_base_dir}")
        return

    # Create a random identifier for logs (UUID).
    # Users can list them in order of date to see which one is latest.
    zambeze_log_path = logs_base_dir.joinpath(
        f"{datetime.utcnow().strftime('%Y_%m_%d-%H_%M_%S_%f')[:-3]}.log"
    )

    # Randomly select two ports...
    # Both ports should be available, because we're binding
    # (i.e., making the 1st unavailable to choose the 2nd)
    hb_socket = zmq.Context().socket(zmq.REP)
    # hb_port = hb_socket.bind_to_random_port(
    #     "tcp://*", min_port=50000, max_port=60000, max_tries=100
    # )

    data_socket = zmq.Context().socket(zmq.REP)
    # data_port = data_socket.bind_to_random_port(
    #     "tcp://*", min_port=50000, max_port=60000, max_tries=100
    # )

    # Technically creating a small RACE CONDITION to re-bind in agent.
    # Will want to explore ways to avoid this.
    data_socket.close()
    hb_socket.close()

    # *********** #
    # TODO: Use ZMQ utilities to auto-find port.
    data_port = 5555
    hb_port = 5556
    # *********** #

    arg_list = ["zambeze-agent", "--log-path", str(zambeze_log_path.resolve())]

    if debug:
        arg_list.append("--debug")

    arg_list.append("--zmq-heartbeat-port")
    arg_list.append(str(hb_port))
    arg_list.append("--zmq-activity-port")
    arg_list.append(str(data_port))

    logger.info(f"Command: {' '.join(arg_list)}")

    # Open the subprocess and save the process state to file (for future access).
    proc = subprocess.Popen(arg_list, stdout=devnull, stderr=devnull)
    logger.info(f"Started agent with PID: {proc.pid}")

    agent_state = {
        "pid": proc.pid,
        "log_path": str(zambeze_log_path.resolve()),
        "zmq_heartbeat_port": hb_port,
        "zmq_activity_port": data_port,
        "status": "RUNNING",
    }

    with state_path.open("w") as f:
        json.dump(agent_state, f)


def agent_stop(logger: LogManager) -> None:
    """
    Stop the agent by killing its system process and updating the state file.

    :param logger: The agent logger that writes to ~/.zambeze/logs
    :type logger: logging.Logger
    """
    logger.info("Received stop signal.")

    old_state: dict
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


def agent_get_status(logger: LogManager) -> None:
    """
    Get the status of the user's local agent and print it to the console
    (and do nothing else).

    :param logger: The agent logger that writes to ~/.zambeze/logs
    :type logger: logging.Logger
    """
    if not state_path.is_file():
        logger.info(
            "Agent does not exist. You can start an agent with 'zambeze agent start'."
        )

    with state_path.open("r") as f:
        old_state = json.load(f)

    logger.info(f"Agent Status: {old_state['status']}.")
