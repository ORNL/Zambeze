
import logging
from enum import Enum
from typing import Optional


class MessageType(Enum):
    ACTIVITY = "ACTIVITY"
    STATUS = "STATUS"
    TEST = "TEST"


class QueueType(Enum):
    RABBITMQ = "RabbitMQ"
    NATS = "NATS"


class QueueFactory:
    def __init__(self, logger: Optional[logging.logger] = None):
        self._builders = {}

    def create(self, queue_type: QueueType, args: dict):
        builder = self._builders.get(queue_type)
        if not builder:
            raise Exception("Unrecognized queue type cannot instantiate: "
                            f"{queue_type.value}")
        return builder(args)
