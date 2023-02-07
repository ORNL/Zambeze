from ..abstract_uri_separator import AbstractURISeparator
from zambeze.orchestration.network import isAddressValid, isValidDomainName

# Standard imports
import logging
import os
from typing import Optional


class RsyncURISeparator(AbstractURISeparator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("rsync", logger=logger)

    def separate(self, uri: str, extra_args=None) -> dict:
        """Will take a rsync URI and break it into its components

        :param uri: Rsync uri should be like rsync://127.0.0.1/path/file.txt
        :type uri: str

        :Example:

        >>> separator = RsyncURISeparator()
        >>> rsync_uri = rsync://path/file.txt
        >>> uri_components = separator.separate(rsync_uri)
        >>> print( uri_components["path"] ) # Path
        >>> print( uri_components["file_name"]) # File name
        >>> print( uri_components["error_message"] ) # Error message
        >>> print( uri_components["netloc"] ) # ip or domain

        The output should be

        >>> /path/
        >>> file.txt
        """
        uri = uri.lstrip(" ").rstrip(" ")

        file_uri_tag = "rsync://"

        package = {
            "protocol": "rsync",
            "error_message": "",
            "path": "",
            "file_name": "",
            "netloc": "",
        }

        print(f"URI is {uri}")
        # Start by ensuring the start of the uri begins with globus://
        if not uri.startswith(file_uri_tag):
            error_msg = f"Incompatible rsync URI format {uri} must start with "
            error_msg = error_msg + "rsync://"
            package["error_messag"] = error_msg
            return package

        file_and_path = uri[len(file_uri_tag) :]

        print(file_and_path)
        if "/" in file_and_path:
            print(file_and_path.index("/"))
            potential_netloc = file_and_path[: file_and_path.index("/")]
            if isAddressValid(potential_netloc):
                file_and_path = file_and_path.removeprefix(potential_netloc)
                package["netloc"] = potential_netloc
            elif isValidDomainName(potential_netloc):
                file_and_path = file_and_path.removeprefix(potential_netloc)
                package["netloc"] = potential_netloc

        print(f"After removing rsync:// path is {file_and_path}")
        path = os.path.dirname(file_and_path)
        print(f"Removing file from path {path}")

        if not path.startswith(os.sep):
            path = os.sep + path
            print(f"1: {path}")

        if not path.endswith(os.sep):
            path += os.sep
            print(f"2: {path}")

        package["path"] = path
        package["file_name"] = os.path.basename(file_and_path)
        return package
