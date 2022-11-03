from abc import ABC, abstractmethod
from ..zambeze_types import MessageType


class AbstractMessage(ABC):
    """Returns the Message type. i.e. ACTIVITY"""
    type: MessageType
    """Returns the Message as a dict"""
    message: dict
