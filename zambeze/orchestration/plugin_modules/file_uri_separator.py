from .abstract_uri_separator import AbstractURISeparator

# Standard imports
import logging
import os
from typing import Optional


class FileURISeparator(AbstractURISeparator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("file", logger=logger)

    def separate(self, uri: str, extra_args=None) -> dict:
        """Will take a file URI and break it into its components

        NOTE: This URI implementation attempts to follow:
        https://www.rfc-editor.org/rfc/rfc8089

        Though it is not complete

        :param uri: File uri should be like file:///path/file.txt
        :type uri: str

        :Example:

        >>> file_uri = file://hostname/path/file.txt
        >>> uri_components = fileURISeparator(file_uri)
        >>> print( uri_components["path"] ) # Path
        >>> print( uri_components["hostname"] ) # ""
        >>> print( uri_components["port"] ) # ""
        >>> print( uri_components["file_name"]) # File name
        >>> print( uri_components["error_message"] ) # Error message

        The output should be

        >>> /path/
        >>> file.txt
        """
        uri = uri.lstrip(" ").rstrip(" ")

        file_uri_prefix = "file:/"

        package = {
            "protocol": "file",
            "error_message": "",
            "path": "",
            "file_name": "",
            "port": "",
            "hostname": "",
            "user": "",
        }
        # Start by ensuring the start of the uri begins with globus://
        if not uri.startswith(file_uri_prefix):
            error_msg = f"Incompatible file URI format {uri} must start with "
            error_msg = error_msg + "file:/"
            package["error_messag"] = error_msg
            return package

        file_host_and_path = uri[len(file_uri_prefix) :]
        file_and_path = ""

        if not file_host_and_path[0].startswith(os.sep):
            # Will assume there is no host
            file_and_path = file_host_and_path
            print(f"1 {file_and_path}")
        elif file_host_and_path.startswith(os.sep + os.sep):
            # Will assume there is no host
            file_and_path = file_host_and_path[2:]
            print(f"2 {file_and_path}")
        elif len(file_host_and_path) > 1:
            file_host_and_path = file_host_and_path[1:]
            file_host_and_path = file_host_and_path.split(os.sep, 1)
            host_username_port = file_host_and_path[0]
            print(f"3 {file_and_path}")
            count_at = host_username_port.count("@")
            if count_at == 0:
                host_port = host_username_port
            elif count_at > 1:
                error_msg = f"Incompatible file URI format {uri} cannot contain"
                error_msg += "more than one @ in hostname section"
                package["error_messag"] = error_msg
                return package
            else:
                host_username_port = host_username_port.split("@", 1)
                package["user"] = host_username_port[0]
                host_port = host_username_port[1]

            count_colon = host_port.count(":")
            if count_colon == 0:
                package["hostname"] = host_port
            elif count_at > 1:
                error_msg = f"Incompatible file URI format {uri} cannot contain"
                error_msg += "more than one : in hostname section"
                package["error_messag"] = error_msg
                return package
            else:
                host_port = host_port.split(":", 1)
                package["hostname"] = host_port[0]
                package["port"] = host_port[1]

            if len(file_host_and_path) > 1:
                file_and_path = file_host_and_path[1]
            else:
                file_and_path = ""

        path = os.path.dirname(file_and_path)

        if not path.startswith(os.sep):
            path = os.sep + path

        if not path.endswith(os.sep):
            path = path + os.sep

        package["path"] = path
        package["file_name"] = os.path.basename(file_and_path)
        return package
