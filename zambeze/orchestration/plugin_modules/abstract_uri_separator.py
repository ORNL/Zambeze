# Local imports

from zambeze.log_manager import LogManager

# Standard imports
import logging

from abc import ABC, abstractmethod
from typing import Optional


class AbstractURISeparator(ABC):
    def __init__(self, logger: LogManager) -> None:
        self._logger: LogManager = logger

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the separator.

        The name should be lower case

        :return: Name of the separator
        :rtype: string
        """
        raise NotImplementedError("Name method has not been implemented.")

    @abstractmethod
    def separate(self, uri: str, extra_args=None) -> dict:
        """Should return a dict with the different components

        Standard key value pairs that should always be returned

        "error_message"
        "protocol"
        "file_name"
        "port"
        "user"
        "path"

        As an example if the following uri was passed in

        URI = file://home/jb/awesome.txt

        {
            "error_message": "",
            "protocol": "file",
            "path": "/home/jb/",
            "hostname": "localhost",
            "port": "22",
            "user": "steve",
            "file_name": "awesome.txt"
        }

        NOTE: path will always begin and end with the separator
        """
        raise NotImplementedError("separate method has not been created.")
