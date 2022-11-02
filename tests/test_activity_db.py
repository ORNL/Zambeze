import unittest
from time import time

from zambeze.orchestration.db.dao import create_local_db

from zambeze.orchestration.db.model.activity import Activity
from zambeze.orchestration.db.dao.activity_dao import ActivityDAO


class TestActivity(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        create_local_db()
        self._dao = ActivityDAO()

    def test_insert_activity(self):
        activity = Activity(agent_id='test_agent', created_at=int(time()*1000))
        self._dao.insert(activity)

    def test_insert_returning_id(self):
        activity = Activity(agent_id='8ecd07db-e6a1-4462-b84c-8e3091738061', created_at=int(time() * 1000))
        activity_id = self._dao.insert_returning_id(activity)
        self.assert_(activity_id is not None)
        self.assertEqual(type(activity_id), int)

    def test_update(self):
        activity = Activity(agent_id='8ecd07db-e6a1-4462-b84c-8e3091738061', created_at=int(time() * 1000))
        activity_id = self._dao.insert_returning_id(activity)
        self.assertEqual(type(activity_id), int)
        activity.activity_id = activity_id
        activity.ended_at = 2
        self._dao.update(activity)


if __name__ == '__main__':
    unittest.main()
