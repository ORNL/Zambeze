# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import json
import logging
import pathlib
import os
import subprocess
import typer

from datetime import datetime
from signal import SIGKILL

from zambeze.orchestration.agent.agent import ZambezeSettings

# Typer configuration (including 'agent' sub-app).
app = typer.Typer()
agent_app = typer.Typer()
app.add_typer(agent_app, name="agent")

# Logging and state configuration.
logger = logging.getLogger()
state = {"conf_file": None}


@agent_app.command()
def start():
    """
    Start Zambeze agent as its own daemonized subprocess. This will write logs
    to a user's ~/.zambeze directory and automatically select ports for both
    data and heartbeat communications.
    """
    logger.info("Initializing Zambeze Agent...")

    # Create user dir and make sure the base logging path exists
    zambeze_base_dir = pathlib.Path.home().joinpath(".zambeze")
    logs_base_dir = zambeze_base_dir.joinpath("logs")

    # First check to make sure no agents already running!
    state_path = zambeze_base_dir.joinpath("agent.state")

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

    arg_list = [
        "zambeze-agent",
        "--log-path",
        str(log_path),
        "--debug",
    ]
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


@agent_app.command()
def stop():
    """
    Stop a user's running Zambeze agent.
    """
    logger.info("Received stop signal.")

    old_state = {}

    # Check to make sure agent is *supposed to be* running.
    zambeze_base_dir = pathlib.Path.home().joinpath(".zambeze")
    state_path = zambeze_base_dir.joinpath("agent.state")

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


@agent_app.command()
def status():
    """
    Stop a user's running Zambeze agent.
    """
    zambeze_base_dir = pathlib.Path.home().joinpath(".zambeze")
    state_path = zambeze_base_dir.joinpath("agent.state")

    if not state_path.is_file():
        logger.info(
            "Agent does not exist. You can start an agent with 'zambeze agent start'."
        )

    with state_path.open("r") as f:
        old_state = json.load(f)

    logger.info(f"Agent Status: {old_state['status']}.")


@app.command()
def config(
    list: bool = typer.Option(
        False, "--list", "-l", help="List configuration options."
    ),
    file: bool = typer.Option(False, "--file", "-f", help="Show config file location."),
):
    settings = ZambezeSettings(conf_file=state["conf_file"], logger=logger)
    if file:
        typer.echo(f"Zambeze config file: {settings._conf_file}")
    if list:
        typer.echo(json.dumps(settings.settings, indent=2))


@app.callback()
def main(
    conf_filepath: str = typer.Option(
        None, "--conf", "-c", help="Zambeze configuration file."
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
):
    """
    Zambeze command line interface
    """
    # logging
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[Zambeze Agent] [%(levelname)s] %(asctime)s - %(message)s"
    )

    if debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # configuration file
    if conf_filepath:
        state["conf_file"] = pathlib.Path(conf_filepath)
