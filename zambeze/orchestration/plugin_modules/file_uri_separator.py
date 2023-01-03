from .abstract_uri_separator import URISeparator

# Standard imports
import logging
import os
from typing import Optional


class FileURISeparator(URISeparator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("file", logger=logger)

    def separate(self, uri: str, extra_args=None) -> dict:
        """Will take a file URI and break it into its components

        :param uri: File uri should be like file://path/file.txt
        :type uri: str

        :Example:

        >>> file_uri = file://path/file.txt
        >>> uri_components = fileURISeparator(file_uri)
        >>> print( uri_components["path"] ) # Path
        >>> print( uri_components["file_name"]) # File name
        >>> print( uri_components["error_message"] ) # Error message

        The output should be

        >>> /path/
        >>> file.txt
        """
        uri = uri.lstrip(" ").rstrip(" ")

        file_uri_tag = "file://"

        package = {"protocol": "file", "error_message": "", "path": "", "file_name": ""}
        # Start by ensuring the start of the uri begins with globus://
        if not uri.startswith(file_uri_tag):
            error_msg = f"Incompatible file URI format {uri} must start with "
            error_msg = error_msg + "file://"
            package["error_messag"] = error_msg
            return package

        file_and_path = uri[len(file_uri_tag):]
        path = os.path.dirname(file_and_path)

        if not path.startswith(os.sep):
            path = os.sep + path

        if not path.endswith(os.sep):
            path = path + os.sep

        package["path"] = path
        package["file_name"] = os.path.basename(file_and_path)
        return package
