
import os
import pathlib
import time
import globus_sdk

from urllib.parse import urlparse
from zambeze.utils.identity import valid_uuid


class TransferHippoError(Exception):
    """Custom exception class for TransferHippo errors."""
    pass


class TransferHippo:
    """
    TransferHippo is the handler for all data movement in Zambeze. It handles:
    0. Loading file path objects,
    1. Validating file paths,
    2. Performing auth checks,
    3. Creating transfer objects,
    4. Monitoring for transfer completion (success or failure),
    5. Returning mappings of native file location to new location mappings.

    Supported source types are:
    A. Local file: 'local'.
    B. Globus-accessible file: 'globus'.
    """

    def __init__(self, agent_id, settings, logger, tokens=None):
        self._logger = logger
        self._settings = settings
        self._agent_id = agent_id
        self.tokens = tokens

        self.file_objects = {}
        self._supported_schemes = ["local", "globus"]
        self.globus_transfer_client = None  # Globus-specific tooling.
        self.globus_task_ids = []

    def load(self, raw_file_paths):
        """
        Load file path objects into the TransferHippo.

        Args:
            raw_file_paths (list[str]): A list of file paths to load.

        Raises:
            RuntimeError: If files have already been loaded.
            KeyError: If a duplicate file path is found.
        """
        if self.file_objects:
            raise TransferHippoError("TransferHippo can only be loaded once... Aborting!")

        for raw_file_path in raw_file_paths:
            file_url = urlparse(raw_file_path)
            file_path_resolved = str(pathlib.Path(file_url.path).resolve())

            self._logger.debug(f"[th-load] File URL: {file_url}")
            self._logger.debug(f"[th-load] Transfer scheme: {file_url.scheme}")
            self._logger.debug(f"[th-load] File path: {file_path_resolved}")

            if file_path_resolved in self.file_objects:
                raise KeyError("File object already exists. No duplicate values allowed!")

            self.file_objects[file_path_resolved] = {
                'file_url': file_url
            }

    def validate(self):
        """
        Validate that all file paths are in the correct format relative to the transfer type.

        Returns:
            bool: True if validation is successful, False otherwise.
        """
        for file_path_resolved, file_data in self.file_objects.items():
            file_url = file_data['file_url']

            if file_url.scheme not in self._supported_schemes:
                self._logger.error(f"[th-validate] File at {file_path_resolved} not of "
                                   f"supported scheme: {self._supported_schemes}")
                return False

            if file_url.scheme == "local" and not pathlib.Path(file_path_resolved).exists():
                self._logger.error(f"[th-validate] Local file at {file_path_resolved} unable "
                                   f"to be found.")
                return False

            if file_url.scheme == "globus":
                if "globus" not in self._settings.settings["plugins"]:
                    self._logger.error("[th-validate] Globus not configured to run on agent machine.")
                    return False

                if not valid_uuid(file_url.netloc, 4):
                    self._logger.error("[th-validate] Globus Endpoint ID not in valid UUID4 format.")
                    return False

                if not file_url.path:
                    self._logger.error("[th-validate] Globus path to file is empty.")
                    return False

        return True

    def check_auth(self):
        """
        Perform authentication checks for each transfer type.

        Returns:
            bool: True if authentication checks pass, False otherwise.
        """
        # TODO: Implement authentication check logic.
        return True

    def start_transfer(self):
        """
        Start the transfer process for files loaded into the TransferHippo.
        """
        globus_init = False
        globus_counter = 0
        task_data = None

        # TODO: Make this generic; Create transfer holder for each type. Then pack the files in each in a loop.
        #  at the end, start each of the transfers.
        for resolved_file_url, file_data in self.file_objects.items():
            file_url_obj = file_data['file_url']

            if file_url_obj.scheme == "local":
                continue

            if not globus_init:
                globus_init = True
                source_ep = file_url_obj.netloc
                dest_ep = self._settings.settings["plugins"]["globus"]["local_ep"]

                self._logger.info(f"EXTOKENS: {self.tokens}")
                self.globus_transfer_client = globus_sdk.TransferClient(
                    authorizer=globus_sdk.AccessTokenAuthorizer(self.tokens["globus"]["access_token"])
                )
                task_data = globus_sdk.TransferData(
                    self.globus_transfer_client,
                    source_endpoint=source_ep,
                    destination_endpoint=dest_ep,
                )

            filename = os.path.basename(resolved_file_url)
            dest_filename = os.path.join(os.getcwd(), filename)
            task_data.add_item(file_url_obj.path, dest_filename)
            globus_counter += 1

        if task_data and globus_counter > 0:
            transfer_task_id = self.globus_transfer_client.submit_transfer(task_data)['task_id']
            self._logger.info(f"[th-start] submitted transfer, of {globus_counter} files: "
                              f"task_id={transfer_task_id}")
            self.globus_task_ids.append(transfer_task_id)

    def transfer_wait(self, timeout=-1):
        """
        Wait for the transfer to complete.

        Args:
            timeout (int): Time in seconds to wait before timing out.

        Returns:
            bool: True if transfer is completed or False if timed out.
        """

        # TODO: generalize
        wait_start_t = time.time()
        while True:
            for task_id in self.globus_task_ids:
                status = self.globus_transfer_client.get_task(task_id)['status']
                if status in ["SUCCEEDED", "FAILED"]:
                    return True
                if timeout != -1 and time.time() - wait_start_t > timeout:
                    self._logger.error("TIMEOUT CONDITION ACHIEVED!")
                    return False
                time.sleep(2)
            time.sleep(0.5)
