import json
import os
import subprocess
import uuid
import zmq

from signal import SIGKILL


# Pass stdout/stderr to devnull (in subprocesses) to avoid memory issues.
devnull = open(os.devnull, "wb")

user_base_dir = os.path.expanduser("~")
state_path = os.path.join(user_base_dir, ".zambeze/agent.state")


def agent_start(logger):
    """
    Start the agent via the local zambeze-agent utility and save initial state.

    Parameters:
        logger (logging.logger) the agent logger that writes to ~/.zambeze/logs
    Returns:
        None
    """

    logger.info("Initializing Zambeze Agent...")
    # Create user dir and make sure the base logging path exists.
    zambeze_base_dir = os.path.join(user_base_dir, ".zambeze/logs")

    # First check to make sure no agents already running!
    if os.path.isfile(state_path):
        with open(state_path, "r") as f:
            old_state = json.load(f)
        if old_state["status"] == "RUNNING":
            logger.info(
                "[ERROR] Agent already running. "
                "Please stop agent before running a new one!"
            )

    # Ensure that we have a folder in which to write logs.
    try:
        os.makedirs(zambeze_base_dir, exist_ok=True)
    except OSError:
        logger.error("Creating log directory failed! Terminating...")
        return

    # Create a random identifier for logs (UUID).
    # Users can list them in order of date to see which one is latest.
    zambeze_log_path = os.path.join(zambeze_base_dir, str(uuid.uuid4()))

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

    arg_list = [
        "zambeze-agent",
        "--log-path",
        zambeze_log_path,
        "--debug",
        "--zmq-heartbeat-port",
        str(hb_port),
        "--zmq-activity-port",
        str(data_port),
    ]
    logger.info(f"Command: {' '.join(arg_list)}")

    # Open the subprocess and save the process state to file (for future access).
    proc = subprocess.Popen(arg_list, stdout=devnull, stderr=devnull)
    logger.info(f"Started agent with PID: {proc.pid}")

    agent_state = {
        "pid": proc.pid,
        "log_path": zambeze_log_path,
        "zmq_heartbeat_port": hb_port,
        "zmq_activity_port": data_port,
        "status": "RUNNING",
    }

    with open(state_path, "w") as f:
        json.dump(agent_state, f)


def agent_stop(logger):
    """
    Stop the agent by killing its system process and updating the state file.

    Parameters:
        logger (logging.logger) the agent logger that writes to ~/.zambeze/logs
    Returns:
        None
    """

    logger.info("Received stop signal.")

    # Check to make sure agent is *supposed to be* running.
    if os.path.isfile(state_path):
        with open(state_path, "r") as f:
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
    with open(state_path, "w") as f:
        json.dump(old_state, f)

    logger.info("Agent successfully stopped!\n")


def agent_get_status(logger):
    """
    Get the status of the user's local agent and print it to the console
    (and do nothing else).

    Parameters:
        logger (logging.logger) the agent logger that writes to ~/.zambeze/logs
    Returns:
        None
    """
    if not os.path.isfile(state_path):
        logger.info(
            "Agent does not exist. You can start an agent with 'zambeze agent start'."
        )

    with open(state_path, "r") as f:
        old_state = json.load(f)

    logger.info(f"Agent Status: {old_state['status']}.")