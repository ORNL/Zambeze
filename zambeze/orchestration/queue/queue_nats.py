
import json
import logging
import nats
from .abstract_queue import AbstractQueue
from .queue_factory import MessageType, QueueType
from nats.errors import TimeoutError
from typing import Optional


class QueueNATS(AbstractQueue):
    def __init__(
            self,
            queue_config: dict,
            logger: Optional[logging.Logger] = None) -> None:

        self._queue_type = QueueType.NATS
        self._logger = logger
        self._ip = "127.0.0.1"
        self._port = "4222"
        self._nc = None
        self._sub = None

        if "ip" in queue_config:
            self._ip = queue_config["ip"]
        if "port" in queue_config:
            self._port = queue_config["port"]

    async def __disconnected(self):
        self._logger.info(
            f"Disconnected from nats... {self._settings.get_nats_connection_uri()}"
        )

    async def __reconnected(self):
        self._logger.info(
            f"Reconnected to nats... {self._settings.get_nats_connection_uri()}"
        )

    @property
    def type(self) -> QueueType:
        return self._queue_type

    @property
    def uri(self):
        """
        Get the NATS connection URI.

        :return: NATS connection URI
        :rtype: str
        """
        if self._ip is None:
            raise Exception("No ip specified for NATS queue")
        if self._port is None:
            raise Exception("No port specified for NATS queue")

        return f"nats://{self._ip}:{self._port}"

    @property
    def connected(self) -> bool:
        return self._nc is not None

    async def connect(self):
        self._nc = await nats.connect(
            self._settings.get_nats_connection_uri(),
            reconnected_cb=self.__reconnected,
            disconnected_cb=self.__disconnected,
            connect_timeout=1,
        )

    @property
    def subscribed(self, msg_type: MessageType) -> bool:
        if self._sub is not None:
            if msg_type in self._sub:
                if self._sub[msg_type] is not None:
                    return True
        return False

    @property
    def subscriptions(self) -> list[MessageType]:
        active_subscriptions = []
        if self._sub is None:
            return active_subscriptions
        for subscription in self._sub:
            if subscription is not None:
                active_subscriptions.append(subscription)
        return active_subscriptions

    async def subscribe(self, msg_type: MessageType):
        self._sub[msg_type] = await self._nc.subscribe(msg_type.value)

    async def unsubscribe(self, msg_type: MessageType):
        if self._sub is None:
            return
        if msg_type not in self._sub:
            return
        if self._sub[msg_type] is None:
            return
        await self._sub[msg_type].unsubscribe()
        self._sub[msg_type] = None

    async def nextMsg(self, msg_type: MessageType) -> dict:
        if self._sub is None:
            raise Exception("Cannot get next message client is not subscribed \
                    to any NATS topic")
        if msg_type.value not in self._sub:
            raise Exception("Cannot get next message client is not subscribed \
                    to any NATS topic")
        msg = await self._sub[msg_type].next_msg()
        data = json.loads(msg.data)
        return data

    async def send(self, msg_type: MessageType, body: dict):
        if self._nc is None:
            self.connect()
        await self._nc.publish(msg_type, json.dumps(body).encode())

    async def close(self):
        for subscription in self._sub:
            if subscription is not None:
                subscription.unsubscribe()
        await self._nc.drain()
        self._nc = None
        self._sub = None

