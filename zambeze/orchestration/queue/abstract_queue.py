from abc import ABC, abstractmethod
from ..zambeze_types import QueueType, ChannelType


class AbstractQueue(ABC):
    @property
    @abstractmethod
    def type(self) -> QueueType:
        raise NotImplementedError(
            "type - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def uri(self) -> str:
        raise NotImplementedError(
            "uri - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def connected(self) -> bool:
        raise NotImplementedError(
            "connected - method does not exist for:" f"{self._queue_type.value}"
        )

    @abstractmethod
    async def connect(self) -> (bool, str):
        raise NotImplementedError(
            "connect - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def subscribed(self) -> bool:
        raise NotImplementedError(
            "subscribed - method does not exist for:" f"{self._queue_type.value}"
        )

    @abstractmethod
    async def subscribe(self, channel: ChannelType):
        raise NotImplementedError(
            "subscribe - method does not exist for:" f"{self._queue_type.value}"
        )

    @property
    @abstractmethod
    def subscriptions(self) -> list[ChannelType]:
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
