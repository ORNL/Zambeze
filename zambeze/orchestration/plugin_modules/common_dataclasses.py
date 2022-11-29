from dataclasses import dataclass, field


@dataclass
class Move:
    source: str
    destination: str


@dataclass
class TransferTemplateInner:
    """Type can be synchronous or asynchronous"""

    type: str
    items: list = field(default_factory=list)


@dataclass
class Items:
    items: list = field(default_factory=list)


@dataclass
class TransferTemplate:
    transfer: TransferTemplateInner


@dataclass
class RsyncItem:
    ip: str
    path: str
    user: str


@dataclass
class Endpoints:
    source: RsyncItem
    destination: RsyncItem


@dataclass
class RsyncTransferTemplateInner:
    type: str
    items: list = field(default_factory=list)


@dataclass
class RsyncTransferTemplate:
    transfer: TransferTemplateInner
