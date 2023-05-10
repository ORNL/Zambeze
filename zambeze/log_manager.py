
# Third party imports
import fcntl

# Standard imports
import asyncio
import copy
import datetime
import logging
import os
import select
import time

class LogManager():
    """
    Set the level logging.INFO etc
    """
    def __init__(self, level, log_path=""):

        # If no log path is specified use default location and type
        if "".__eq__(log_path):
            fmt_str = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f")[:-3]
            self._log_file_path = os.path.expanduser('~') + f"/.zambeze/logs/{fmt_str}.log"
        else:
            self._log_file_path = log_path

        directory = os.path.dirname(self._log_file_path)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)

        self._level = level
        self._name = "zambeze-logger"
        self._logger = logging.getLogger(self._name)
        self._logger.setLevel(self._level)

        # For Handlers
        self._format = "[Zambeze Agent] [%(levelname)s] - %(name)s - %(asctime)s - %(message)s"
        formatter = logging.Formatter(self._format)

        # Set up StreamHandler
        ch = logging.StreamHandler()
        ch.setLevel(self._level)
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

        # Set up File Handler
        fh = logging.FileHandler(self._log_file_path)
        fh.setLevel(self._level)
        fh.setFormatter(formatter)
        self._logger.addHandler(fh)

        # Needed for locking
        self._log_file_descriptor = fh.stream.fileno()
       
        # Processes that are being watched
        self._processes = []

    def setLevel(self, level):
        # Will change the log level of all the handlers
        self._logger.setLevel(level)

    def debug(self, msg):
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_EX)  # Acquire an exclusive lock
        self._logger.debug(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the


    def info(self, msg):
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_EX)  # Acquire an exclusive lock
        self._logger.info(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    def warning(self, msg):
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_EX)  # Acquire an exclusive lock
        self._logger.warning(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    def error(self, msg):
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_EX)  # Acquire an exclusive lock
        self._logger.error(msg)
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_UN)  # Release the

    def critical(self, msg):
        fcntl.flock(self._log_file_descriptor, fcntl.LOCK_EX)  # Acquire an exclusive lock
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


    """
    Meant to be used with a subprocess instance that has been configured with
    the following settings

    :Example"
    process = subprocess.Popen(
                    shell_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1)

    log_manager.watch([process])

    # Call wait when you want to ensure the process is complete
    process.wait()
    """
    def watch(self, processes: list):

        async def write_to_log_async(logger, msg, log_file_descriptor):
            fcntl.flock(log_file_descriptor, fcntl.LOCK_EX)  # Acquire an exclusive lock
            logger.info(msg)
            fcntl.flock(log_file_descriptor, fcntl.LOCK_UN)  # Release the

        # Alternate reading lines from the different processes
        async def read_subprocess_output(processes, logger, file_descriptor):
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
                ready, _, _ = select.select([process.stdout], [], [], 0.1)  # Non-blocking select
                if process.stdout in ready:
                    chunk = process.stdout.read()
                    if chunk:
                        asyncio.create_task(write_to_log_async(logger, chunk, file_descriptor))
                    else:
                        processes.pop(index)

        async def watch_subprocesses(processes):
            tasks = [read_subprocess_output(processes, self._logger, self._log_file_descriptor)]
            await asyncio.gather(*tasks)
            [process.stdout.close() for process in processes]
        
        asyncio.run(watch_subprocesses(copy.copy(processes)))
