from enum import Enum

class ChannelType(Enum):
    ACTIVITY = "ACTIVITY"
    STATUS = "STATUS"
    TEST = "TEST"


class QueueType(Enum):
    RABBITMQ = "RabbitMQ"
    NATS = "NATS"

