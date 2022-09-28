
import logging
from abc import ABC, abstractmethod
from queue_factory import QueueType, MessageType
from typing import Optional


class Queue(ABC):
    def __init_(
            self, queue_type: QueueType,
            logger: Optional[logging.Logger] = None) -> None:
        self._queue_type = queue_type

    @property
    def type(self) -> QueueType:
        return self._queue_type

    @property
    @abstractmethod
    def uri(self) -> str:
        raise NotImplementedError("uri - method does not exist for:"
                                  f"{self._queue_type.value}")

    @property
    @abstractmethod
    def connected(self) -> bool:
        raise NotImplementedError("connected - method does not exist for:"
                                  f"{self._queue_type.value}")

    @abstractmethod
    def connect(self):
        raise NotImplementedError("connect - method does not exist for:"
                                  f"{self._queue_type.value}")

    @property
    @abstractmethod
    def subscribed(self) -> bool:
        raise NotImplementedError("subscribed - method does not exist for:"
                                  f"{self._queue_type.value}")

    @abstractmethod
    def subscribe(self, msg_type: MessageType):
        raise NotImplementedError("subscribe - method does not exist for:"
                                  f"{self._queue_type.value}")

    @property
    @abstractmethod
    def subscriptions(self) -> list[MessageType]:
        raise NotImplementedError("subscriptions - method does not exist for:"
                                  f"{self._queue_type.value}")

    @abstractmethod
    def nextMsg(self, msg_type: MessageType) -> dict:
        raise NotImplementedError("nextMsg - method does not exist for:"
                                  f"{self._queue_type.value}")

    @abstractmethod
    def send(self, msg_type: MessageType, body: dict):
        raise NotImplementedError("send - method does not exist for:"
                                  f"{self._queue_type.value}")

    @abstractmethod
    def close(self):
        raise NotImplementedError("close - method does not exist for:"
                                  f"{self._queue_type.value}")
