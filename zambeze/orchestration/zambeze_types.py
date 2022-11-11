from enum import Enum


class ChannelType(Enum):
    ACTIVITY = "ACTIVITY"
    STATUS = "STATUS"
    TEST = "TEST"


class MessageType(Enum):
    ACTIVITY = "ACTIVITY"
    STATUS = "STATUS"


class QueueType(Enum):
    RABBITMQ = "RabbitMQ"
    NATS = "NATS"
