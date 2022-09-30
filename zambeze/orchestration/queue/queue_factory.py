import logging
from enum import Enum
from typing import Optional

from .queue_nats import QueueNATS
from .abstract_queue import AbstractQueue
from ..zambeze_types import QueueType

class QueueFactory:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger

    def create(self, queue_type: QueueType, args: dict) -> AbstractQueue:

        if queue_type == QueueType.NATS:
            return QueueNATS(args, self._logger)
        elif queue_type == QueueType.RABBITMQ:
            raise Exception(
                "RabbitMQ queue client has not yet been implemented: " f"{queue_type.value}"
            )
        else:
            raise Exception(
                "Unrecognized queue type cannot instantiate: " f"{queue_type.value}"
            )
