# Local imports
from zambeze.orchestration.db.dao.dao_utils import create_local_db
from zambeze.orchestration.db.model.activity_model import ActivityModel
from zambeze.orchestration.db.dao.activity_dao import ActivityDAO
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest
from time import time

logger = LogManager(logging.DEBUG, name="activity_test_log")
create_local_db()
_dao = ActivityDAO(logger)


@pytest.mark.unit
def test_insert_activity():
    activity = ActivityModel(
        agent_id="8ecd07db-e6a1-4462-b84c-8e3091738061", created_at=int(time() * 1000)
    )
    _dao.insert(activity)


@pytest.mark.unit
def test_insert_returning_id():
    activity = ActivityModel(
        agent_id="8ecd07db-e6a1-4462-b84c-8e3091738061", created_at=int(time() *
            1000)
    )
    activity_id = _dao.insert_and_return_id(activity)
    assert activity_id is not None
    assert isinstance(activity_id, int)


@pytest.mark.unit
def test_update():
    activity = ActivityModel(
        agent_id="8ecd07db-e6a1-4462-b84c-8e3091738061", created_at=int(time() *
            1000)
    )
    activity_id = _dao.insert_and_return_id(activity)
    assert isinstance(activity_id, int)
    activity.activity_id = activity_id
    activity.ended_at = int(time() * 1000)
    _dao.update(activity)
