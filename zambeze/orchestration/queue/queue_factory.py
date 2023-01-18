import logging
from typing import Optional

from .queue_nats import QueueNATS
from .queue_rmq import QueueRMQ
# TODO: this enforces queue factory to be of type AbstractQueue. Needs to
# allow RMQ protocols before this can occur.
# from .abstract_queue import AbstractQueue
from ..zambeze_types import QueueType


class QueueFactory:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger

    def create(self, queue_type: QueueType, args: dict):
        """Is responsible for creating a Queue Client.

        The advantages of a factory method is to isolate the implementation
        details of a concrete type to a single file and to provide a standard
        interface for their creation and access.

        :param queue_type: the queue type to be created.
        :type queue_type: the type to created.
        :param args: the arguments specific to the client that are needed for
        its construction.
        :type args: dict
        :return: Should return an abstract Queue based on the provided enum.
        :rtype: AbstractQueue

        Example:

        The following example assumes the code block appears in an async
        function.

        RabbitMQ = QueueType.RabbitMQ
        NATS = QueueType.NATS
        factory = QueueFactory(logger)
        # Create first client
        args = { "ip": 127.0.0.1, "port": 4222 }
        queue_clients[NATS] = QueueFactory.create(NATS, args)
        # Create second client
        args = { "ip": 127.0.0.1, "port": 5672 }
        queue_clients[RabbitMQ] = QueueFactory.create(RabbitMQ, args)
        # Loop through clients and print uri
        for client in queue_clients:
          print(client.uri)
        # Have each client connect to their own queue
        for client in queue_clients:
          await client.connect()
        """
        if queue_type == QueueType.NATS:
            return QueueNATS(args, logger=self._logger)
        elif queue_type == QueueType.RABBITMQ:
            return QueueRMQ(args, logger=self._logger)
        else:
            raise Exception(
                "Unrecognized queue type cannot instantiate: " f"{queue_type.value}"
            )
