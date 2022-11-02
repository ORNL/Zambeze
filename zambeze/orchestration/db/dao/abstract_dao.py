from abc import ABCMeta, abstractmethod
from typing import Optional
import logging

from zambeze.orchestration.db.dao import get_db_engine


class AbstractDAO(object, metaclass=ABCMeta):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger: logging.Logger = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self._engine = get_db_engine()

    @abstractmethod
    def insert(self, entity):
        pass

    @abstractmethod
    def insert_returning_id(self, entity):
        pass

    @abstractmethod
    def update(self, entity):
        pass

    # @abstractmethod
    # def dict_based_update(self, new_values, id_value):
    #     pass
