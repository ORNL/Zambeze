from ..abstract_uri_separator import AbstractURISeparator
from zambeze.orchestration.network import is_address_valid

# Standard imports
import logging
import os
from typing import Optional


class RsyncURISeparator(AbstractURISeparator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("rsync", logger=logger)

    def separate(self, uri: str, extra_args=None) -> dict:
        """Will take a rsync URI and break it into its components

         NOTE: The rsync sheme URI followed what is specified here:
         https://www.rfc-editor.org/rfc/rfc5781

        URI scheme syntax: An rsync URI describes a source or destination for
        the rsync application including a hostname, path, and optional user
        and port.  The generic form of the rsync URI is:

        rsync://[user@]host[:PORT]/Source

        The rsync URI follows the general syntax from RFC 3986 and is defined
        by the following ABNF [RFC5234]:

        rsyncuri = "rsync:" hier-part
                         ; See RFC 3986 for the definition
                         ; of hier-part

        URI scheme semantics: An rsync URI may be used as either a source or
        destination for the rsync application.  If the port is not specified,
        it defaults to 873.

        Encoding considerations: Since the rsync URI is defined using
        standard elements from RFC 3986, no special encoding considerations
        are present.

        Applications/protocols that use this URI scheme name: The only
        application that uses rsync URIs is rsync.

        Interoperability considerations: Since only one application is
        expected to make use of rsync URIs, this U
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

        # Start by ensuring the start of the uri begins with globus://
        if not uri.startswith(file_uri_tag):
            error_msg = f"Incompatible rsync URI format {uri} must start with "
            error_msg = error_msg + "rsync://"
            package["error_messag"] = error_msg
            return package

        file_and_path = uri[len(file_uri_tag) :]

        if "/" in file_and_path:
            potential_netloc = file_and_path[: file_and_path.index("/")]
            if is_address_valid(potential_netloc):
                file_and_path = file_and_path.removeprefix(potential_netloc)
                package["netloc"] = potential_netloc

        path = os.path.dirname(file_and_path)

        if not path.startswith(os.sep):
            path = os.sep + path

        if not path.endswith(os.sep):
            path += os.sep

        package["path"] = path
        package["file_name"] = os.path.basename(file_and_path)
        return package
