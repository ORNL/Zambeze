import json
import logging
import nats
from .abstract_queue import AbstractQueue
from .queue_exceptions import QueueTimeoutException
from ..zambeze_types import ChannelType, QueueType
from typing import Optional
import dill


class QueueNATS(AbstractQueue):
    def __init__(
        self, queue_config: dict, logger: Optional[logging.Logger] = None
    ) -> None:

        self._queue_type = QueueType.NATS
        self._logger = logger
        self._ip = "127.0.0.1"
        self._port = "4222"
        self._nc = None
        self._sub = {}

        if "ip" in queue_config:
            self._ip = queue_config["ip"]
        if "port" in queue_config:
            self._port = queue_config["port"]

    async def __disconnected(self):
        if self._logger:
            self._logger.info(
                f"Disconnected from nats... {self._settings.get_nats_connection_uri()}"
            )

    async def __reconnected(self):
        if self._logger:
            self._logger.info(
                f"Reconnected to nats... {self._settings.get_nats_connection_uri()}"
            )

    @property
    def type(self) -> QueueType:
        return self._queue_type

    @property
    def uri(self) -> str:
        """Get the NATS connection URI.

        :returns: NATS connection URI
        :rtype: str

        Raises:
        :raises Exception: if no ip address to NATS is provided
        :raises Exception: if no port for NATS is provided
        """
        if self._ip is None:
            raise Exception("No ip specified for NATS queue")
        if self._port is None:
            raise Exception("No port specified for NATS queue")

        return f"nats://{self._ip}:{self._port}"

    @property
    def connected(self) -> bool:
        return self._nc is not None

    async def connect(self) -> tuple[bool, str]:
        try:
            self._nc = await nats.connect(
                self.uri,
                reconnected_cb=self.__reconnected,
                disconnected_cb=self.__disconnected,
                connect_timeout=1,
            )
        except Exception:
            if self._logger:
                # pyre-ignore[16]
                self._logger.debug(
                    f"Unable to connect to nats server at {self.uri}"
                    "1. Make sure your firewall ports are open.\n"
                    "2. That the nats service is up and running.\n"
                    "3. The correct ip address and port have been specified.\n"
                    "4. That an agent.yaml file exists for the zambeze agent.\n"
                )
                self._nc = None

        if self.connected:
            return (True, f"Able to connect to NATS machine at {self.uri}")
        return (
            False,
            "Connection attempt timed out while trying to connect to NATS "
            f"at {self.uri}",
        )

    @property
    def subscribed(self, channel: ChannelType) -> bool:
        if self._sub:
            if channel in self._sub:
                if self._sub[channel] is not None:
                    return True
        return False

    @property
    def subscriptions(self) -> list[ChannelType]:
        active_subscriptions = []
        if not self._sub:
            return active_subscriptions
        for subscription in self._sub.keys():
            if self._sub[subscription] is not None:
                active_subscriptions.append(subscription)
        return active_subscriptions

    async def subscribe(self, channel: ChannelType):
        if self._nc is None:
            raise Exception(
                "Cannot subscribe to topic, client is not " "connected to a NATS queue"
            )
        self._sub[channel] = await self._nc.subscribe(channel.value)

    async def unsubscribe(self, channel: ChannelType):
        if not self._sub:
            return
        if channel not in self._sub:
            return
        if not self._sub[channel]:
            return
        await self._sub[channel].unsubscribe()
        self._sub[channel] = None

    async def nextMsg(self, channel: ChannelType):
        if not self._sub:
            raise Exception(
                "Cannot get next message client is not subscribed \
                    to any NATS topic"
            )
        if channel not in self._sub:
            raise Exception(
                f"Cannot get next message client is not subscribed \
                        to any NATS topic: {channel.value}"
            )

        try:
            msg = await self._sub[channel].next_msg(timeout=1)
            print("Received data")
            data = dill.loads(msg.data)
            print("After dill loads")
            print(data)

        except nats.errors.TimeoutError:
            raise QueueTimeoutException("nextMsg call - checking NATS")

        return data

    async def ackMsg(self, channel: ChannelType):
        if self._sub:
            if channel in self._sub:
                await self._sub[channel].ack()

    async def nackMsg(self, channel: ChannelType):
        if self._sub:
            if channel in self._sub:
                await self._sub[channel].nack()

    async def send(self, channel: ChannelType, body):
        if self._nc is None:
            raise Exception(
                "Cannot send message to NATS, client is "
                "not connected to a NATS queue"
            )
        print("Queue is sending")
        print(body)
        await self._nc.publish(channel.value, dill.dumps(body))

    async def close(self):
        if self._sub:
            for subscription in self._sub:
                if subscription is not None:
                    await self._sub[subscription].unsubscribe()
        await self._nc.drain()
        self._nc = None
        self._sub = {}
