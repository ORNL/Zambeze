# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from typing import Optional
from .abstract_activity import Activity
from urllib.parse import urlparse

class TransferActivity(Activity):


    def _sanitizeItems(self):
        """Will take a lit of items

        >>> items = [
        >>>    {  
        >>>       "source": "url1",
        >>>       "destination": "url2",
        >>>    },
        >>>    {
        >>>       "source": "url3",
        >>>       "destination": "url4",
        >>>    }
        >>> ]
                
        Will make sure that the urls use consistent protocols
        Will throw and error if folder is specified insteand of item.
        """

        for item in items:
            if "source" not in item:
                raise Exception("Missing 'source' from transfer item")
            if "destination" not in item:
                raise Exception("Missing 'destination' from transfer item")

            if item["source"].endswith("/"):
                raise Exception(f"Folders are not yet supported change 'source' url {item['source']}")
            if item["destination"].endswith("/"):
                raise Exception(f"Folders are not yet supported change 'destination' url {item['destination']}")

            source = urlparse(item["source"])
            destination = urlparse(item["destination"])

            if source.schema != destination.schema:
                error_msg = "Source and destination url schemas differ"
                error_msg = error_msg + f"\nsource: {source.schema}"
                error_msg = error_msg + f"\ndestination: {destination.schema}"
                raise Exception(error_msg)

    """A transfer activity.

    :param name: Campaign activity name.
    :type name: str

    :param source: List of file URIs.
    :type file uris: Optional[list[str]]

    :param destination: Action's command.
    :type file uris: Optional[list[str]]

    :param logger: The logger where to log information/warning or errors.
    :type logger: Optional[logging.Logger]
    """

    def __init__(
        self,
        name: str,
        items: Optional[list[dict]] = [],
        logger: Optional[logging.Logger] = None,
        **kwargs
    ) -> None:
        """Create an object of a unix shell activity."""
        supported_types = [ AttributeType.ARGUMENTS, AttributeType.ARGUMENT ]
        self.__items = items
        super().__init__(name, supported_attributes=supported_types, logger=logger)
        self.logger: Optional[logging.Logger] = (
            logger if logger else logging.getLogger(__name__)
        )

        # Pull out environment variables, IF users submitted them.
        if "env_vars" in kwargs:
            self.env_vars = kwargs.get("env_vars")
        else:
            self.env_vars = []

        # identify plugin
        self._sanitizeItems()


    def generate_message(self) -> dict:
        return {
            "plugin": "shell",
            "items": self._items
        }
