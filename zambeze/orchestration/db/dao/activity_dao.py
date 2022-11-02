from typing import Dict

from zambeze.orchestration.db.dao import get_insert_stmt, get_update_stmt_from_entity_object
from zambeze.orchestration.db.dao.abstract_dao import AbstractDAO
from zambeze.orchestration.db.model.activity import Activity


class ActivityDAO(AbstractDAO):

    def insert(self, activity: Activity) -> None:
        values = activity.get_all_values()
        insert_stmt = get_insert_stmt(Activity.ENTITY_NAME, Activity.FIELD_NAMES)
        self._logger.debug(f"Saving activity: {insert_stmt}")
        self._logger.debug(f"\t Values: {values}")
        try:
            self._engine.execute(insert_stmt, values)
        except Exception as e:
            error_msg = f"Error while storing in the local db. The exception was\n {e}"
            self._logger.error(error_msg)
            raise Exception(error_msg)

    def insert_returning_id(self, activity: Activity):
        values = activity.get_all_values()
        insert_stmt = get_insert_stmt(Activity.ENTITY_NAME, Activity.FIELD_NAMES)
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

    def update(self, activity: Activity):
        update_stmt = get_update_stmt_from_entity_object(activity)
        try:
            conn = self._engine.connect()
            conn.execute(update_stmt, activity.get_values_without_id())
        except Exception as e:
            error_msg = f"Error while updating in the local db. The exception was\n {e}"
            self._logger.error(error_msg)
            raise Exception(error_msg)

    # def dict_based_update(self, new_values: Dict, id_value):
    #     update_stmt = get_update_stmt_from_dict(Activity.ENTITY_NAME, new_values, Activity.ID_FIELD_NAME, id_value)
    #     try:
    #         conn = self._engine.connect()
    #         conn.execute(update_stmt, tuple(new_values.values()))
    #     except Exception as e:
    #         error_msg = f"Error while updating in the local db. The exception was\n {e}"
    #         self._logger.error(error_msg)
    #         raise Exception(error_msg)
