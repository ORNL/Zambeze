from dataclasses import dataclass


@dataclass
class Move:
    source: str
    destination: str


@dataclass
class TransferTemplateInner:
    """Type can be synchronous or asynchronous"""

    type: str
    items: list = []


@dataclass
class Items:
    items: list = []


@dataclass
class TransferTemplate:
    transfer: TransferTemplateInner
