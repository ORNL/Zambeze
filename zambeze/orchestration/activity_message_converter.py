import time
import logging
from typing import Optional

from .zambeze_types import ActivityType, MessageType
from .uri_separator import URISeparator
from .messages.abstract_message import AbstractMessage
from .messages.message_factory import MessageFactory

class ActivityMessageConverter():

    def __init__(self, agent_id: str, logger: Optional[logging.Logger] = None):

        self.__logger = logger
        if self.__logger is None:
            self.__logger = logging.Logger(__name__)

        self.__uri_separator = URISeparator(logger)
        self.__message_factory = MessageFactory(logger)
        self.__agent_id = agent_id

    def convert(
            self,
            msg: AbstractMessage,
            activity_type: ActivityType) -> AbstractMessage:
        """Will convert the AbstractMessage to a different type assumes
        the message in an Activity message"""
       
        if activity_type != ActivityType.PLUGIN:
            error_msg = "Currently only conversion to ActivityType.PLUGIN "
            error_msg += "is supported."
            raise Exception(error_msg)

        if msg.type != MessageType.ACTIVITY:
            error_msg = "Only conversion of activity messages is supported."
            raise Exception(error_msg)

        if msg.body.type == ActivityType.TRANSFER:

            if activity_type == ActivityType.PLUGIN:
                # Determine what plugin to use and then convert to plugin message
                for item in msg.body.parameters.items:
                    source = item.source
                    destination = item.source

                    source_components = self.__uri_separator.separate(source)
                    destination_components = self.__uri_separator.separate(destination)

                    if source_components["protocol"] != destination_components["protocol"]:
                        error_msg = "Cannot convert TRANSER Activity to PLUGIN"
                        error_msg += " activity. Source and destination "
                        error_msg += "protocols differ. source: "
                        error_msg += f"{source_components['protocol']}"
                        error_msg += ", destination: "
                        error_msg += f"{destination_components['protocol']}"
                        raise Exception(error_msg)

                    protocol = source_components["protocol"]
                    if protocol == "rsync":
                        template = self.__message_factory.createTemplate(
                            MessageType.ACTIVITY,
                            ActivityType.PLUGIN,
                            {"plugin": "rsync", "action": "transfer"}
                        )
                        # message_id is added when the template is turned into
                        # a message
                        template[1].activity_id = msg.activity_id
                        template[1].agent_id = self.__agent_id
                        template[1].campaign_id = msg.campaign_id
                        template[1].credential = msg.credential
                        template[1].submission_time = str(int(time.time()))
                        template[1].\
                            body.\
                            parameters.\
                            transfer.items[0].\
                            source.\
                            path = source_components.path
                        template[1].body.\
                            parameters.\
                            transfer.\
                            items[0].source.user = ""
                        template[1].\
                            body.\
                            parameters.\
                            transfer.items[0].\
                            destination.path = destination_components.path
                        template[1].\
                            body.\
                            parameters.\
                            transfer.\
                            items[0].destination.user = ""
                    elif protocol == "globus":
                        template = self.__message_factory.createTemplate(
                            MessageType.ACTIVITY,
                            ActivityType.PLUGIN,
                            {"plugin": "globus", "action": "transfer"}
                        )
                        # message_id is added when the template is turned into
                        # a message
                        template[1].activity_id = msg.activity_id
                        template[1].agent_id = self.__agent_id
                        template[1].campaign_id = msg.campaign_id
                        template[1].credential = msg.credential
                        template[1].submission_time = str(int(time.time()))
                        template[1].\
                            body.\
                            parameters.\
                            transfer.items[0].\
                            source.\
                            path = source_components.path
                        template[1].\
                            body.\
                            parameters.\
                            transfer.items[0].\
                            destination.\
                            path = destination_components.path
                    elif protocol == "file":
                        template = self.__message_factory.createTemplate(
                            MessageType.ACTIVITY,
                            ActivityType.PLUGIN,
                            {"plugin": "rsync", "action": "transfer"}
                        )
                        # message_id is added when the template is turned into
                        # a message
                        template[1].activity_id = msg.activity_id
                        template[1].agent_id = self.__agent_id
                        template[1].campaign_id = msg.campaign_id
                        template[1].credential = msg.credential
                        template[1].submission_time = str(int(time.time()))
                        template[1].body.\
                            parameters.\
                            transfer.items[0].\
                            source.path = source_components.path
                        template[1].\
                            body.\
                            parameters.\
                            transfer.items[0].\
                            destination.path = destination_components.path
                    else:
                        error_msg = "Unsupported transfer protocol specified"
                        raise Exception(error_msg)

                    return self.__message_factory.create(template)

        else:
            error_msg = f"Conversion from type {msg.body.type} not currently "
            error_msg += "supported."
            raise Exception()
