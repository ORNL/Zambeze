from zambeze.orchestration.db.dao.dao_utils import get_update_stmt, get_insert_stmt
from zambeze.orchestration.db.dao.abstract_dao import AbstractDAO
from zambeze.orchestration.db.model.abstract_entity import AbstractEntity
from zambeze.log_manager import LogManager

# Standard imports
import logging


class ActivityDAO(AbstractDAO):
    def insert(self, entity: AbstractEntity) -> None:
        values = entity.get_all_values()
        insert_stmt = get_insert_stmt(entity)
        self._logger.debug(f"Saving entity: {insert_stmt}")
        self._logger.debug(f"\t Values: {values}")
        try:
            self._engine.execute(insert_stmt, values)
        except Exception as e:
            error_msg = f"Error while storing in the local db. The exception was\n {e}"
            self._logger.error(error_msg)
            raise Exception(error_msg)

    def insert_and_return_id(self, entity: AbstractEntity) -> int:
        values = entity.get_all_values()
        insert_stmt = get_insert_stmt(entity)
        self._logger.debug(f"Saving entity: {insert_stmt}")
        self._logger.debug(f"\t Values: {values}")
        try:
            conn = self._engine.connect()
            trans = conn.begin()
            executed = conn.execute(insert_stmt, values)
            _id = executed.lastrowid
            trans.commit()
            conn.close()
            return _id
        except Exception as e:
            error_msg = f"Error while storing in the local db. The exception was\n {e}"
            self._logger.error(error_msg)
            raise Exception(error_msg)

    def update(self, entity: AbstractEntity) -> None:
        update_stmt = get_update_stmt(entity)
        try:
            conn = self._engine.connect()
            conn.execute(update_stmt, entity.get_values_without_id())
        except Exception as e:
            error_msg = f"Error while updating in the local db. The exception was\n {e}"
            self._logger.error(error_msg)
            raise Exception(error_msg)
