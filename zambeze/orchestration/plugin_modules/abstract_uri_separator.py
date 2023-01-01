import logging

from abc import ABC, abstractmethod
from typing import Optional


class URISeparator(ABC):
    def __init__(self, name: str, logger: Optional[logging.Logger] = None) -> None:
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self._name = name

    @property
    def name(self) -> str:
        """Returns the name of the separator.

        The name should be lower case

        :return: Name of the separator
        :rtype: string
        """
        return self._name

    @abstractmethod
    def separate(self, uri: str, extra_args=None) -> dict:
        """Should return a dict with the different components

        Standard key value pairs that should always be returned

        "error_message"
        "protocol"
        "file_name"
        "path"

        As an example if the following uri was passed in

        URI = file://home/jb/awesome.txt

        {
            "error_message": "",
            "protocol": "file",
            "path": "/home/jb/"
            "file_name": "awesome.txt"
        }

        NOTE: path will always begin and end with the separator
        """
        raise NotImplementedError("separate method has not been created.")
