from ..abstract_uri_separator import URISeparator
from ...identity import valid_uuid

import logging
import os
import re
from typing import Optional


class GlobusURISeparator(URISeparator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("globus", logger=logger)

    def separate(self, uri: str, extra_args=None) -> dict:
        """Will take a globus URI and break it into its components

        :param uri: the globus uri globus://XXXXX...XXX/path/file.txt
        :type uri: str

        :Example:

        >>> default_uri = "YYYYZZZZ-YYYY-ZZZZ-YYYY-ZZZZYYYYZZZZ"
        >>> globus_uri = globus://XXXXYYYY-XXXX-XXXX-XXXX-XXXXYYYYXXXX/path/file.txt
        >>> uri_components = globusURISeparator(globus_uri, default_uri)
        >>> print( uri_components["uuid"] ) # UUID
        >>> print( uri_components["path"] ) # Path
        >>> print( uri_components["file_name"] ) # File name
        >>> print( uri_components["error_message"] ) # Error message

        The output should be

        >>> XXXXYYYY-XXXX-XXXX-XXXX-XXXXYYYYXXXX
        >>> /path/
        >>> file.txt

        :Example: When no endpoint UUID is provided in the URI the default shoul
        be used

        >>> default_uri = "YYYYZZZZ-YYYY-ZZZZ-YYYY-ZZZZYYYYZZZZ"
        >>> globus_uri = globus://path/file.txt
        >>> uri_components = globusURISeparator(globus_uri, default_uri)
        >>> print( uri_components["uuid"] ) # UUID
        >>> print( uri_components["path"] ) # Path
        >>> print( uri_components["file_name"] ) # File name
        >>> print( uri_components["error_message"] ) # Error message

        The output should be

        >>> YYYYZZZZ-YYYY-ZZZZ-YYYY-ZZZZYYYYZZZZ
        >>> /path/
        >>> file.txt
        """
        default_uuid = extra_args
        uri = uri.lstrip(" ").rstrip(" ")

        globus_uri_tag = "globus://"
        # Start by ensuring the start of the uri begins with globus://
        package = {
            "protocol": "globus",
            "path": "",
            "file_name": "",
            "uuid": "",
            "error_message": "",
        }
        if not uri.startswith(globus_uri_tag):
            error_msg = f"Incompatible Globus URI format {uri} must start with "
            error_msg = error_msg + "globus://"
            package["error_message"] = error_msg
            return package

        UUID_and_path = uri[len(globus_uri_tag) :]
        # Replace multiple occurances of // with single /
        UUID_and_path = re.sub(os.sep + "{2,}", os.sep, UUID_and_path)

        print(f"UUID_and_path is  {UUID_and_path}")
        UUID = UUID_and_path[0:36]
        print(f"UUID from path is {UUID}")
        file_and_path = UUID_and_path

        legal_uuid = default_uuid
        # Check if the first 36 chars contains os.sep it is probably a file_path
        # in which case the default uuid should be provided
        if os.sep not in UUID:
            if not valid_uuid(UUID):
                error_msg = f"Incompatible Globus URI format {uri} must contain 36 "
                error_msg += "character valid UUID of the form "
                error_msg += "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                error_msg += f" the provided UUID is {UUID} and is of length "
                error_msg += f"{len(UUID)} "
                error_msg += "it must also conform to RFC4122"
                package["error_message"] = error_msg
                return package
            legal_uuid = UUID
            file_and_path = UUID_and_path[36:]
        else:
            if default_uuid is None:
                error_msg = f"Incompatible Globus URI format {uri} must contain 36 "
                error_msg += "character valid UUID of the form "
                error_msg += "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                error_msg += f" the provided UUID is {UUID} and is of length "
                error_msg += f"{len(UUID)} "
                error_msg += "it must also conform to RFC4122"
                package["error_message"] = error_msg
                return package

        path = os.path.dirname(file_and_path)

        if not path.startswith(os.sep):
            path = os.sep + path

        if not path.endswith(os.sep):
            path = path + os.sep

        package["uuid"] = legal_uuid
        package["path"] = path
        package["file_name"] = os.path.basename(file_and_path)
        return package
