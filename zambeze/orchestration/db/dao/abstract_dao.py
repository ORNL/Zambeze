from abc import ABCMeta, abstractmethod
from typing import Optional, Any
import logging

from zambeze.log_manager import LogManager
from zambeze.orchestration.db.dao.dao_utils import get_db_engine
from zambeze.orchestration.db.model.abstract_entity import AbstractEntity


class AbstractDAO(object, metaclass=ABCMeta):
    _engine: Any

    def __init__(self, logger: LogManager):
        self._logger = logger
        #self._logger: logging.Logger = (
        #    logging.getLogger(__name__) if logger is None else logger
        #)
        self._engine = get_db_engine()

    @abstractmethod
    def insert(self, entity: AbstractEntity) -> None:
        raise NotImplementedError()

    @abstractmethod
    def insert_and_return_id(self, entity: AbstractEntity) -> int:
        raise NotImplementedError()

    @abstractmethod
    def update(self, entity: AbstractEntity) -> None:
        raise NotImplementedError()
