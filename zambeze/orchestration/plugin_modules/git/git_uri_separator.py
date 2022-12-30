from ..abstract_uri_separator import URISeparator

# Standard imports
import logging
import os
from typing import Optional


class GitURISeparator(URISeparator):
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__("git", logger=logger)

    def __removeConsecutiveDuplicates(self, s, char):
        if len(s) < 2:
            return s

        if s[0] == char:
            if s[0] == s[1]:
                return self.__removeConsecutiveDuplicates(s[1:], char)
        return s[0] + self.__removeConsecutiveDuplicates(s[1:], char)

    def separate(self, uri: str, extra_args=None) -> dict:
        """Will take a file URI and break it into its components

        :param uri: Git uri should be like git://org1/awesome_proj/path/file.txt
        :type uri: str

        :Example:

        >>> git_uri = git://orig1/awesome_proj/main/path/file.txt
        >>> uri_components = gitURISeparator(git_uri)
        >>> print( uri_components["project"]) # "awesome_proj"
        >>> print( uri_components["owner"]) # "org1"
        >>> print( uri_components["path"] ) # Path
        >>> print( uri_components["branch"] ) # Branch
        >>> print( uri_components["file_name"]) # File name
        >>> print( uri_components["error_message"] ) # Error message

        The output should be

        >>> /path/
        >>> file.txt
        """
        uri = uri.lstrip(" ").rstrip(" ")

        file_uri_tag = "git://"

        package = {
            "protocol": "git",
            "error_message": "",
            "project": "",
            "owner": "",
            "path": "",
            "file_name": "",
        }
        # Start by ensuring the start of the uri begins with globus://
        if not uri.startswith(file_uri_tag):
            error_msg = f"Incompatible git URI format {uri} must start with "
            error_msg = error_msg + "git://"
            package["error_messag"] = error_msg
            return package

        file_and_path_project_owner = uri[len(file_uri_tag):]

        # There needs to be at least two / left in the string after removing
        # the git:// prefix, becuase the git URI must contain a project and
        # owner
        print("Before removeConsecutiveDuplicates")
        print(file_and_path_project_owner)
        file_and_path_project_owner = self.__removeConsecutiveDuplicates(
            file_and_path_project_owner, os.sep
        )

        if file_and_path_project_owner.count(os.sep) < 3:
            error_msg = "git URI at a minimum must contain a project "
            error_msg += " owner and branch: git:://owner/project/branch/ to be valid"

        print("Before split")
        print(file_and_path_project_owner)
        split_str = file_and_path_project_owner.split(os.sep)
        print("After split")
        print(split_str)
        package["owner"] = split_str[0]
        package["project"] = split_str[1]
        package["branch"] = split_str[2]

        # Indicates there is no file, just a path that ends in /
        if file_and_path_project_owner[-1] == os.sep:
            index = 3
            package["path"] = os.sep
            while index < len(split_str):
                package["path"] += split_str[index] + os.sep
                index += 1
        else:
            # indicates there is a file at the end
            package["file_name"] = split_str[-1]
            index = 3
            package["path"] = os.sep
            while index < (len(split_str) - 1):
                package["path"] += split_str[index] + os.sep
                index += 1

        return package
