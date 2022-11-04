from abc import ABCMeta, abstractmethod
from typing import Optional
import logging

from zambeze.orchestration.db.dao.dao_utils import get_db_engine


class AbstractDAO(object, metaclass=ABCMeta):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self._engine = get_db_engine()

    @abstractmethod
    def insert(self, entity):
        raise NotImplementedError()

    @abstractmethod
    def insert_and_return_id(self, entity):
        raise NotImplementedError()

    @abstractmethod
    def update(self, entity):
        raise NotImplementedError()
