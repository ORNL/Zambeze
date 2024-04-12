from zambeze.orchestration.db.dao.dao_utils import get_update_stmt, get_insert_stmt
from zambeze.orchestration.db.dao.abstract_dao import AbstractDAO
from zambeze.orchestration.db.model.abstract_entity import AbstractEntity
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


class ActivityDAO(AbstractDAO):
    def insert(self, entity: AbstractEntity) -> None:
        values = entity.get_all_values()
        insert_stmt = get_insert_stmt(entity)

        self._logger.debug(f"Saving entity: {insert_stmt}")
        self._logger.debug(f"\t Values: {values}")

        try:
            with self._engine.connect() as conn:
                conn.execute(text(insert_stmt), values)
        except SQLAlchemyError as e:
            msg = f"Insert error with the local db. Exception was {e}"
            self._logger.error(msg)
            raise

    def insert_and_return_id(self, entity: AbstractEntity) -> int:
        values = entity.get_all_values()
        insert_stmt = get_insert_stmt(entity)

        self._logger.debug(f"Saving entity: {insert_stmt}")
        self._logger.debug(f"\t Values: {values}")

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(insert_stmt), values)
                _id = result.lastrowid
        except SQLAlchemyError as e:
            msg = f"Insert and return error with local db. Exception was {e}"
            self._logger.error(msg)
            raise

        return _id

    def update(self, entity: AbstractEntity) -> None:
        values = entity.get_values_without_id()
        update_stmt = get_update_stmt(entity)

        try:
            with self._engine.connect() as conn:
                conn.execute(text(update_stmt), values)
        except SQLAlchemyError as e:
            msg = f"Update error with the local db. Exception was {e}"
            self._logger.error(msg)
            raise
