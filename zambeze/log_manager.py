# Third party imports
import fcntl

# Standard imports
import asyncio
import copy
import datetime
import logging
import os
import select

from typing import Optional


class LogManager:

    """
    LogManager for providing a single consistent interface for logging all
    output associated with Zambeze

    The log manager should be used in place of logging.Logger from the standard
    python imports.

    It provides a means of having multiple processes write to the same log file
    without corruption via the fnctl module. It is also able to capture the
    output of subprocesses see the 'watch' command below for an example.
    """

    # Prevent pyre from complaining
    _fh: Optional[logging.FileHandler] = None
    _ch: Optional[logging.FileHandler] = None

    def _create_handles(self):
        # For Handlers
        self._format = (
            "[Zambeze] [%(levelname)s] - %(name)s - %(asctime)s - %(message)s"
        )
        formatter = logging.Formatter(self._format)

        def handler_exists(logger, handler_name):
            for handler in logger.handlers:
                if handler.name == handler_name:
                    return True
            return False

        def get_handler(logger, handler_name):
            for handler in logger.handlers:
                if handler.name == handler_name:
                    return handler

        # Set up StreamHandler
        stream_handler = f"{self._name}-stream"
        if not handler_exists(self._logger, stream_handler):
            self._ch = logging.StreamHandler()
            self._ch.name = stream_handler
            self._ch.setLevel(self._level)
            self._ch.setFormatter(formatter)
            self._logger.addHandler(self._ch)
        else:
            self._ch = get_handler(self._logger, stream_handler)
            self._ch.setLevel(self._level)

        # Set up File Handler
        file_handler = f"{self._name}-file"
        if not handler_exists(self._logger, file_handler):
            self._fh = logging.FileHandler(self._log_file_path)
            self._fh.name = file_handler
            self._fh.setLevel(self._level)
            self._fh.setFormatter(formatter)
            self._logger.addHandler(self._fh)
        else:
            self._fh = get_handler(self._logger, file_handler)
            self._fh.setLevel(self._level)

    def _create(self, level: int, name: str, log_path: str):
        self._level = level
        self._name = name
        # Processes that are being watched
        self._processes = []

        self._logger = logging.getLogger(self._name)
        self._logger.setLevel(self._level)

        # If no log path is specified use default location and type
        if "" == log_path:
            fmt_str = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")[:-3]
            self._log_file_path = (
                os.path.expanduser("~") + f"/.zambeze/logs/{self._name}-{fmt_str}.log"
            )
        else:
            self._log_file_path = log_path

        directory = os.path.dirname(self._log_file_path)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)

        self._create_handles()
        # Needed for locking
        self._log_file_descriptor = self._fh.stream.fileno()

    def __init__(self, level: int, name: str = "zambeze-logger", log_path: str = ""):
        """
        Initialization of the LogManager

        :param level: This is a required parameter and can be one of the log
        levels provided by the logging import module. i.e. logging.INFO,
        logging.DEBUG, logging.CRITICAL, logging.ERROR, logging.WARNING
        :type level: This is an int consistent with the logging modules levels
        :param name: This is the name of the logger, if non is set then the
        default zambeze-logger will be used
        :type name: This is a str
        :param log_path: This is the location and file where the logs will be
        sent, if none is provided then the logger will be default place logs in
        ~/.zambeze/logs
        """
        self._log_file_path: str = ""
        self._create(level, name, log_path)

    def __getstate__(self):
        return {
            "level": self._level,
            "name": self._name,
            "log_path": self._log_file_path,
        }

    def __setstate__(self, state):
        self._create(state["level"], state["name"] + "_B", state["log_path"])

    def setLevel(self, level):
        # Will change the log level of all the handlers
        self._level = level
        self._logger.setLevel(self._level)
        self._ch.setLevel(self._level)
        self._fh.setLevel(self._level)

    def debug(self, msg):
        fcntl.flock(
            self._log_file_descriptor, fcntl.LOCK_EX
        )  # Acquire an exclusive lock
        self._logger.debug(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    def info(self, msg):
        fcntl.flock(
            self._log_file_descriptor, fcntl.LOCK_EX
        )  # Acquire an exclusive lock
        self._logger.info(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    def warning(self, msg):
        fcntl.flock(
            self._log_file_descriptor, fcntl.LOCK_EX
        )  # Acquire an exclusive lock
        self._logger.warning(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    def error(self, msg):
        fcntl.flock(
            self._log_file_descriptor, fcntl.LOCK_EX
        )  # Acquire an exclusive lock
        self._logger.error(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    def critical(self, msg):
        fcntl.flock(
            self._log_file_descriptor, fcntl.LOCK_EX
        )  # Acquire an exclusive lock
        self._logger.critical(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    @property
    def path(self):
        return self._log_file_path

    @property
    def name(self):
        return self._name

    @property
    def level(self) -> str:
        if self._level == logging.INFO:
            return "INFO"
        elif self._level == logging.DEBUG:
            return "DEBUG"
        elif self._level == logging.WARN:
            return "WARNING"
        elif self._level == logging.ERROR:
            return "ERROR"
        elif self._level == logging.CRITICAL:
            return "CRITICAL"
        raise Exception("Log level set in LogManager is unrecognized")

    """
    Meant to be used with a subprocess instance that has been configured with
    the settings shown in the example.

    NOTE: for this to work all output must be redirected to stdout as shown

    :Example"
    process = subprocess.Popen(
                    shell_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True)

    log_manager.watch([process])

    # Call wait when you want to ensure the process is complete before
    # continuing.
    process.wait()
    """

    def watch(self, processes: list, watch_name: str = ""):
        async def write_to_log_async(logger, msg, log_file_descriptor, watch_name):
            fcntl.flock(log_file_descriptor, fcntl.LOCK_EX)  # Acquire an exclusive lock
            logger.info(f" {watch_name} " + msg)
            fcntl.flock(log_file_descriptor, fcntl.LOCK_UN)  # Release the

        # Alternate reading lines from the different processes
        async def read_subprocess_output(
            processes, logger, file_descriptor, watch_name
        ):
            # Alter the stdout of the process so that they are non blocking
            for process in processes:
                stdout_fd = process.stdout.fileno()
                flags = fcntl.fcntl(stdout_fd, fcntl.F_GETFL)
                fcntl.fcntl(stdout_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Read the lines
            index = 0
            while True:
                if len(processes) == 0:
                    break

                # Cycle the processes
                index = (index + 1) % len(processes)
                process = processes[index]

                # Grab the chuncks that are ready to be read
                ready, _, _ = select.select(
                    [process.stdout], [], [], 0.1
                )  # Non-blocking select
                if process.stdout in ready:
                    chunk = process.stdout.read()
                    if chunk:
                        asyncio.create_task(
                            write_to_log_async(
                                logger,
                                chunk,
                                file_descriptor,
                                watch_name + "-" + str(index),
                            )
                        )
                    else:
                        processes.pop(index)

        async def watch_subprocesses(processes, watch_name):
            tasks = [
                read_subprocess_output(
                    processes, self._logger, self._log_file_descriptor, watch_name
                )
            ]
            await asyncio.gather(*tasks)
            [process.stdout.close() for process in processes]

        if len(watch_name) == 0:
            watch_name = "subprocess:anon"
        else:
            watch_name = "subprocess:" + watch_name

        asyncio.run(watch_subprocesses(copy.copy(processes), watch_name))
