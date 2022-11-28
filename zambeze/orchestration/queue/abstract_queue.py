from abc import ABC, abstractmethod
from ..zambeze_types import QueueType, ChannelType


class AbstractQueue(ABC):
    _queue_type: QueueType

    @property
    @abstractmethod
    def type(self) -> QueueType:
        """Returns the Queue Client type. i.e. RabbitMQ"""
        raise NotImplementedError(
            "type - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def uri(self) -> str:
        """Returns the uri to the queue i.e. http://127.0.0.1:1451"""
        raise NotImplementedError(
            "uri - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def connected(self) -> bool:
        """If the Queue Client was able to connect to the Queue returns True
        else it will return False"""
        raise NotImplementedError(
            "connected - method does not exist for:" f"{self._queue_type.value}"
        )

    @abstractmethod
    async def connect(self) -> tuple[bool, str]:
        """This method will attempt to connect the client to the Queue.

        :return: if able to connect will return True with a string saying as
        much, if unable to connect will return False with an error message.
        :rtype: tuple[bool, str]

        Example:

        >>> val = await queue.connect()
        """
        raise NotImplementedError(
            "connect - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def subscribed(self, channel: ChannelType) -> bool:
        """Checks to see if the client is subscribed to a particular channel.

        :param channel: This is the channel that we are checking to see if
        the client is subscribed too. If no channel is provided will set equal
        to None
        :type channel: ChannelType
        :return: Will return true if subscribed to at least one channel or if
        a channel is provided, will return True if subscribed to that
        particular channel.
        :rtype: bool

        Example:
        This example assumes the following code is called from within an async
        function.

        >>> queue = factory.create(QueueType.NATS, config)
        >>> assert queue.subscribed is False
        >>> await queue.connect()
        >>> assert queue.subscribed is False
        >>> await queue.subscribe(ChannelType.STATUS)
        >>> assert queue.subscribed is True
        >>> assert queue.subscribed(ChannelType.STATUS) is True
        >>> await queue.unsubscribe(ChannelType.STATUS)
        >>> assert queue.subscribed(ChannelType.STATUS) is False
        """
        raise NotImplementedError(
            "subscribed - method does not exist for:" f"{self._queue_type.value}"
        )

    @abstractmethod
    async def subscribe(self, channel: ChannelType):
        """Subscribe to a channel.

        There are no limits to the number of channels that can be subscribed
        too.

        :param channel: the channel to subscribe to
        :type channel: ChannelType
        """
        raise NotImplementedError(
            "subscribe - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def subscriptions(self) -> list[ChannelType]:
        """Returns a list containing all of the channels the client is
        subscribed too."""
        raise NotImplementedError(
            "subscriptions - method does not exist for:" f"{self._queue_type.value}"
        )

    @abstractmethod
    async def nextMsg(self, channel: ChannelType) -> dict:
        raise NotImplementedError(
            "nextMsg - method does not exist for:" f"{self._queue_type.value}"
        )

    async def ackMsg(self):
        raise NotImplementedError(
            "ackMsg - method does not exist for:" f"{self._queue_type.value}"
        )

    async def nackMsg(self):
        raise NotImplementedError(
            "nackMsg - method does not exist for:" f"{self._queue_type.value}"
        )

    @abstractmethod
    async def send(self, channel: ChannelType, body: dict):
        raise NotImplementedError(
            "send - method does not exist for:" f"{self._queue_type.value}"
        )

    @abstractmethod
    async def close(self):
        raise NotImplementedError(
            "close - method does not exist for:" f"{self._queue_type.value}"
        )
