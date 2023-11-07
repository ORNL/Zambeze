import os
import globus_sdk
import time
import pathlib

from urllib.parse import urlparse
from zambeze.utils.identity import valid_uuid


class TransferHippo:
    def __init__(self, agent_id, settings, logger, tokens=None):
        self._logger = logger
        self._settings = settings
        self._agent_id = agent_id
        self.tokens = tokens

        self.file_objects = dict()
        self._supported_schemes = ["local", "globus"]

        # Globus-specific tooling.  # TODO: boot out to own file.
        self.globus_transfer_client = None  # should be source_ep_id: {'task_data': xxx, 'transfer_client': yyy}
        self.globus_task_ids = []

        """
        TransferHippo is the handler for all data movement in Zambeze. It is responsible for: 
        0. Load in all file path objects, .load()
        1. Validating file paths. E.g., for each file path, .validate()  
        2. Performing auth checks. E.g., for each transfer type, .do_auth_flow()
        3. Creating transfer objects. E.g., for each transfer type, .start_transfer() 
        4. Monitoring for transfer completion (success or failure). E.g., .wait_transfer()
        5. Returning mapping of native file location to new location mappings. E.g., .files
        
        Currently, one should be able to create a TransferHippo that handles all possible source types. 
        
        The supported source types are: 
        A. Local file: 'local'. 
        B. Globus-accessible file: 'globus'
        """

    def load(self, raw_file_paths: list[str]):  # TODO -- listof.

        if len(self.file_objects) > 0:
            raise RuntimeError("TransferHippo can only be loaded once... Aborting!")  # TODO: TransferHippoError.

        for raw_file_path in raw_file_paths:

            file_url = urlparse(raw_file_path)

            # Use this to avoid things like '..' in the file string. For debugging.
            # THIS WILL BE OUR KEY FOR self.file_objects.
            file_path_resolved = str(pathlib.Path(file_url.path).resolve())

            self._logger.debug(f"[th-load] File URL: {file_url}")
            self._logger.debug(f"[th-load] Transfer scheme: {file_url.scheme}")
            self._logger.debug(f"[th-load] File path: {file_path_resolved}")

            if file_path_resolved in self.file_objects:
                raise KeyError("File object already exists. No duplicate values allowed! ")
            else:
                # This dict will later be packed with info.
                self.file_objects[file_path_resolved] = {
                    'file_url': file_url
                }

    def validate(self):
        """ Validate that all file paths are in correct format, relative to transfer type. """
        for file_path_resolved in self.file_objects:
            file_url = self.file_objects[file_path_resolved]['file_url']

            if file_url.scheme not in self._supported_schemes:
                self._logger.error(f"[th-validate] File at {file_path_resolved} not of "
                                   f"supported scheme: {self._supported_schemes}")
                return False

            elif file_url.scheme == "local" and not pathlib.Path(file_path_resolved).exists():
                # If scheme is "Local", just want to check that path exists.
                self._logger.error(f"[th-validate] Local file at {file_path_resolved} unable "
                                   f"to be found.")
                return False

            elif file_url.scheme == "globus":

                if "globus" not in self._settings.settings["plugins"]:
                    self._logger.error(f"[th-validate] Globus not configured"
                                       f"to run on agent machine. ")
                    return False

                # If scheme is "Globus", want to make sure that we have
                #   a valid string in structure globus://<ep_uuid>/path_to_file
                if not valid_uuid(file_url.netloc, 4):
                    self._logger.error(f"[th-validate] Globus Endpoint ID "
                                       f"not in valid UUID4 format.")
                    return False
                # Check to make sure path is not empty
                if file_url.path == "":
                    self._logger.error(f"[th-validate] Globus path to file is empty.")
                    return False

                # TODO: some day use Globus-LS built-ins to see whether file exists.

    def check_auth(self):
        """Perform auth checks for each transfer type. """
        # Check that we can read each file.
        pass

        # Check that we can write to output dir.
        pass

        # Check that we can authenticate with Globus (using token)  # TODO.
        return True

    def start_transfer(self):
        """Use templates to pack a transfer hippo with file(s) to move."""


        globus_init = False
        globus_counter = 0
        for resolved_file_url in self.file_objects:

            file_url_obj = self.file_objects[resolved_file_url]['file_url']

            # all verified local files don't need a transfer!
            if file_url_obj.scheme == "local":
                continue

            if not globus_init:
                # TODO: relax assumption -- all files come from same place.
                # TODO: one taskdata for each source ep
                globus_init = True
                source_ep = file_url_obj.netloc
                dest_ep = self._settings.settings["plugins"]["globus"]["local_ep"]

                self._logger.info(f"EXTOKENS: {self.tokens}")

                self.globus_transfer_client = globus_sdk.TransferClient(
                    authorizer=globus_sdk.AccessTokenAuthorizer(self.tokens["globus"]["access_token"])
                )

                # create a Transfer task consisting of one or more items
                task_data = globus_sdk.TransferData(
                    self.globus_transfer_client,
                    source_endpoint=source_ep,
                    destination_endpoint=dest_ep,
                )

            # Get the filename without any stem.
            filename = resolved_file_url.split('/')[-1]

            # Can be 'here' since we're already in working directory.
            dest_filename = f"{os.path.join(os.getcwd(), filename)}"
            task_data.add_item(
                file_url_obj.path,  # source
                dest_filename,  # dest
            )
            globus_counter += 1

        # Handle case of empty task data.
        # if len(task_data) == 0:
        #     self._logger.info("ERROR ABCDE")
        #     return None

        transfer_task_id = self.globus_transfer_client.submit_transfer(task_data)['task_id']
        self._logger.info(f"GLOBUS COUNTER: {globus_counter}")
        self._logger.info(f"submitted transfer, task_id={transfer_task_id}")

        self.globus_task_ids.append(transfer_task_id)

    def transfer_wait(self, timeout=-1):

        wait_start_t = time.time()
        blow_up = False
        while True:
            for task_id in self.globus_task_ids:
                status = self.globus_transfer_client.get_task(task_id)['status']
                if status != "SUCCEEDED" and status != "FAILED":
                    if time.time() - wait_start_t > timeout and timeout != -1:
                        self._logger.error("TIMEOUT CONDITION ACHIEVED!")
                        blow_up = True
                        break
                    time.sleep(2)
                else:
                    blow_up = True
                    break

            time.sleep(0.5)  # Just gentle rate limiting.
            if blow_up:
                return True
