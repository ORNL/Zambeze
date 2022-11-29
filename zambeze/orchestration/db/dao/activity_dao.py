from zambeze.orchestration.db.dao.dao_utils import get_update_stmt, get_insert_stmt
from zambeze.orchestration.db.dao.abstract_dao import AbstractDAO
from zambeze.orchestration.db.model.abstract_entity import AbstractEntity


class ActivityDAO(AbstractDAO):
    def insert(self, activity: AbstractEntity) -> None:
        values = activity.get_all_values()
        insert_stmt = get_insert_stmt(activity)
        self._logger.debug(f"Saving activity: {insert_stmt}")
        self._logger.debug(f"\t Values: {values}")
        try:
            self._engine.execute(insert_stmt, values)
        except Exception as e:
            error_msg = f"Error while storing in the local db. The exception was\n {e}"
            self._logger.error(error_msg)
            raise Exception(error_msg)

    def insert_and_return_id(self, activity: AbstractEntity) -> int:
        values = activity.get_all_values()
        insert_stmt = get_insert_stmt(activity)
        self._logger.debug(f"Saving activity: {insert_stmt}")
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

    def update(self, activity: AbstractEntity) -> None:
        update_stmt = get_update_stmt(activity)
        try:
            conn = self._engine.connect()
            conn.execute(update_stmt, activity.get_values_without_id())
        except Exception as e:
            error_msg = f"Error while updating in the local db. The exception was\n {e}"
            self._logger.error(error_msg)
            raise Exception(error_msg)
