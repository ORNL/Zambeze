import logging
from .abstract_queue import AbstractQueue
from .queue_exceptions import QueueTimeoutException
from ..zambeze_types import ChannelType, QueueType
import dill
import pika


class QueueRMQ(AbstractQueue):
    def __init__(self, queue_config: dict, logger: logging.Logger) -> None:
        self._queue_type = QueueType.RABBITMQ
        self._logger = logger
        self._ip = "127.0.0.1"
        self._port = "5672"
        self._rmq = None
        self._rmq_channel = None
        self._sub = {}

        self.callback_queue = None

        if "ip" in queue_config:
            self._ip = queue_config["ip"]
        if "port" in queue_config:
            self._port = queue_config["port"]

    def __disconnected(self):
        if self._logger:
            self._logger.info(f"Disconnected from RabbitMQ... {self._ip}:{self._port}")

    def __reconnected(self):
        if self._logger:
            self._logger.info(f"Reconnected to RabbitMQ... {self._ip}:{self._port}")

    @property
    def type(self) -> QueueType:
        return self._queue_type

    @property
    def uri(self) -> str:
        """We don't use RabbitMQ URI to connect."""
        raise NotImplementedError()

    @property
    def connected(self) -> bool:
        return self._rmq is not None

    def connect(self) -> tuple[bool, str]:
        try:
            self._rmq = pika.BlockingConnection(pika.ConnectionParameters(self._ip))
            self._rmq_channel = self._rmq.channel()
            self._logger.info("[Queue RMQ] Creating RabbitMQ channels...")

            # These are the two queues we listen on.
            # Note: these are *not subscriptions*; subscribing to filters not yet supported.
            self._rmq_channel.queue_declare(queue="ACTIVITIES")
            self._rmq_channel.queue_declare(queue="CONTROL")

        except Exception as e:
            if self._logger:
                self._logger.debug(
                    f"Unable to connect to RabbitMQ server at {self._ip}:{self._port}\n"
                    "1. Make sure your firewall ports are open.\n"
                    "2. That the rabbitmq-service is up and running.\n"
                    "3. The correct ip address and port have been specified.\n"
                    "4. That an agent.yaml file exists for the zambeze agent.\n"
                )
                self._logger.error(f"CAUGHT: {e}")
                self._rmq = None
                self._rmq_channel = None

        if self.connected:
            return True, f"Able to connect to RabbitMQ at {self._ip}:{self._port}"
        return (
            False,
            "Connection attempt timed out while trying to connect to RabbitMQ "
            f"at {self._ip}:{self._port}",
        )

    @property
    def subscribed(self, channel: ChannelType) -> bool:
        if self._sub:
            if channel in self._sub:
                if self._sub[channel] is not None:
                    return True
        return False

    def listen_and_do_callback(self, callback_func, channel_to_listen, should_auto_ack):
        """Listen for messages on a persistent websocket connection;
        --> do action in callback function on receipt."""

        listen_on_channel = self._rmq_channel

        self._logger.debug(
            f"[message_handler] "
            f"[***] Waiting using persistent listener on "
            f"RabbitMQ {channel_to_listen} channel."
        )

        listen_on_channel.basic_consume(
            queue=channel_to_listen,
            on_message_callback=callback_func,
            auto_ack=should_auto_ack,
        )
        listen_on_channel.start_consuming()

    @property
    def subscriptions(self) -> list[ChannelType]:
        active_subscriptions = []
        if not self._sub:
            return active_subscriptions
        for subscription in self._sub.keys():
            if self._sub[subscription] is not None:
                active_subscriptions.append(subscription)
        return active_subscriptions

    def subscribe(self, channel: ChannelType):
        raise NotImplementedError()
        # if self._rmq is None:
        #     self._sub[channel] = self._rmq.subscribe(channel.value)

    def unsubscribe(self, channel: ChannelType):
        if not self._sub:
            return
        if channel not in self._sub:
            return
        if not self._sub[channel]:
            return
        self._sub[channel].unsubscribe()
        self._sub[channel] = None

    def next_msg(self, channel: ChannelType):
        if not self._sub:
            raise Exception(
                "Cannot get next message client is not subscribed \
                    to any RabbitMQ topic"
            )
        if channel not in self._sub:
            raise Exception(
                f"Cannot get next message client is not subscribed \
                        to any RabbitMQ topic: {channel.value}"
            )

        try:
            msg = self._sub[channel].next_msg(timeout=1)
            data = dill.loads(msg.data)
        except Exception as e:
            error_msg = "next_msg call - checking RabbitMQ"
            error_msg += f" error: {e}"
            raise QueueTimeoutException(error_msg)

        return data

    def ack_msg(self, channel: ChannelType):
        if self._sub:
            if channel in self._sub:
                self._sub[channel].ack()

    def nack_msg(self, channel: ChannelType):
        if self._sub:
            if channel in self._sub:
                self._sub[channel].nack()

    def send(self, channel: ChannelType, exchange, body):
        """In 'send activity', body is activity message!"""
        if self._rmq is None:
            raise Exception(
                "Cannot send message to RabbitMQ, client is "
                "not connected to a RabbitMQ queue"
            )

        self._logger.info(body.data)
        self._logger.info(type(body.data))

        self._rmq_channel.basic_publish(
            exchange=exchange, routing_key=channel, body=dill.dumps(body)
        )

    def close(self):
        if self._sub:
            for subscription in self._sub:
                if subscription is not None:
                    self._sub[subscription].unsubscribe()
        self._rmq.drain()
        self._rmq = None
        self._sub = {}
