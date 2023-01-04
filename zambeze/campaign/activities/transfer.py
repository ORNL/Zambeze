# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Oak Ridge National Laboratory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import logging

from typing import Optional
from .abstract_activity import Activity, AttributeType
from urllib.parse import urlparse
import time
import uuid

from zambeze.orchestration.message.abstract_message import AbstractMessage
from zambeze.orchestration.message.message_factory import MessageFactory
from zambeze.orchestration.zambeze_types import MessageType, ActivityType


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
        print("Printing Items")
        print(self.__items)
        for item in self.__items:
            print(f"item is {item}")
            if not isinstance(item, dict):
                error_msg = "Problematic type, must be a dict with 'source'"
                error_msg += f" and 'destination' keys. Type is {type(item)}"
                error_msg += f" with content: {item}"
                raise Exception(error_msg)

            if "source" not in item:
                raise Exception("Missing 'source' from transfer item")
            if "destination" not in item:
                raise Exception("Missing 'destination' from transfer item")

            if item["source"].endswith("/"):
                error_msg = "Folders are not yet supported change 'source'"
                error_msg += f" url {item['source']}"
                raise Exception(error_msg)
            if item["destination"].endswith("/"):
                error_msg = "Folders are not yet supported change 'destination'"
                error_msg += f" url {item['destination']}"
                raise Exception(error_msg)

            source = urlparse(item["source"])
            destination = urlparse(item["destination"])

            print(source)
            if source.scheme != destination.scheme:
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

    __items: Optional[dict]

    def __init__(
        self,
        name: str,
        items: Optional[list[dict]] = [],
        logger: Optional[logging.Logger] = None,
        campaign_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        message_id: Optional[str] = None,
        activity_id: Optional[str] = str(uuid.uuid4()),
        **kwargs
    ) -> None:
        """Create an object of a unix shell activity."""
        if isinstance(items, list):
            self.__items = items
        elif isinstance(items, dict):
            self.__items = [items]
        else:
            raise Exception("items must be a dict or list[dict]")

        super().__init__(
                name,
                supported_attributes=[AttributeType.TRANSFER_ITEMS],
                logger=logger,
                campaign_id=campaign_id,
                agent_id=agent_id,
                message_id=message_id,
                activity_id=activity_id
                )

        self.logger: Optional[logging.Logger] = (
            logger if logger else logging.getLogger(__name__)
        )

        # identify plugin
        self._sanitizeItems()

    def add(self, attr_type: AttributeType, attribute) -> None:

        if attr_type not in self._supported_attributes:
            error_msg = f"Activity {self.name} does not support "
            error_msg += f"the provided type {attr_type}"
            raise Exception(error_msg)

        if attr_type == AttributeType.AttributeType.TRANSFER_ITEMS:
            """Add a list of files to the dataset.

            :param files: List of file URIs.
            :type files: list[str]
            """
            if isinstance(attribute, list):
                self.__items.extend(attribute)
            elif isinstance(attribute, dict):
                self.__items.extend([attribute])
            else:
                error_msg = "TRANSFER_ITEMS must be of type dict or of type "
                error_msg += f"list[dict], but they are {attribute}"
                error_msg += f" type is: {type(attribute)}"
                raise Exception(error_msg)
            self._sanitizeItems()
        else:
            raise Exception("Unsupported AttributeType detected")

    def set(self, attr_type: AttributeType, attribute) -> None:
        if attr_type not in self._supported_attributes:
            error_msg = f"Activity {self.name} does not support the "
            error_msg += f"provided type {attr_type}"
            raise Exception(error_msg)

        if attr_type == AttributeType.TRANSFER_ITEMS:
            """Set the list of files.

            :param files: List of file URIs.
            :type files: list[str]
            """
            if isinstance(attribute, list):
                self.__items = attribute
            elif isinstance(attribute, dict):
                self.__items = [attribute]
            else:
                error_msg = "TRANSFER_ITEMS must be of type dict or of type "
                error_msg += f"list[dict], but they are {attribute}"
                error_msg += f" type is: {type(attribute)}"
                raise Exception(error_msg)
            self._sanitizeItems()
        else:
            raise Exception("Unsupported AttributeType detected")
        print("Items")
        print(self.__items)


    def generate_message(self) -> AbstractMessage:

        factory = MessageFactory()
        template = factory.createTemplate(
            MessageType.ACTIVITY, ActivityType.TRANSFER)

        template[1].activity_id = self.activity_id
        template[1].message_id = self.message_id
        template[1].agent_id = self.agent_id
        template[1].campaign_id = self.campaign_id
        template[1].credential = {}
        template[1].submission_time = str(int(time.time()))
        template[1].body.type = "TRANSFER"
        template[1].body.parameters.items[0].source = self.__items[0]["source"]
        template[1].body.parameters.items[0].destination = self.__items[0]["destination"]

        return factory.create(template)
