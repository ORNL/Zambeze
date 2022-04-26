import pytest
import uuid

from zambeze.task import Task

def test_task_action_data():
    payload = {
            "client_id": uuid.UUID("161963a6-c59f-11ec-a6ae-00155d8c61bb"),
            "task_id": uuid.UUID("161964c8-c59f-11ec-a6ae-00155d8c61bb"),
            "credentials": {},
            "action": { "type": "Data", "source": "/home/file1.txt", "destination": "/home/file2.txt" }
            }
    task = Task(payload)
    assert str(task) == "{'client_id': '161963a6-c59f-11ec-a6ae-00155d8c61bb', 'task_id': '161964c8-c59f-11ec-a6ae-00155d8c61bb', 'credentials': {}, 'action': {'type': 'Data', 'source': '/home/file1.txt', 'destination': '/home/file2.txt'}}"

def test_task_action_compute():
    payload = {
            "client_id": uuid.UUID("16196aea-c59f-11ec-a6ae-00155d8c61bb"),
            "task_id": uuid.UUID("1619690a-c59f-11ec-a6ae-00155d8c61bb"),
            "credentials": {},
            "action": { "type": "Compute", "workflow_id": uuid.UUID("16196888-c59f-11ec-a6ae-00155d8c61bb"), "parameters": {"compute_workflow": "run simulation" }}
            }
    task = Task(payload)
    assert str(task) == "{'client_id': '16196aea-c59f-11ec-a6ae-00155d8c61bb', 'task_id': '1619690a-c59f-11ec-a6ae-00155d8c61bb', 'credentials': {}, 'action': {'type': 'Compute', 'workflow_id': '16196888-c59f-11ec-a6ae-00155d8c61bb', 'parameters': {'compute_workflow': 'run simulation'}}}"

def test_task_action_control():
    payload = {
            "client_id": uuid.UUID("16196a7c-c59f-11ec-a6ae-00155d8c61bb"),
            "task_id": uuid.UUID("16196ab8-c59f-11ec-a6ae-00155d8c61bb"),
            "credentials": {},
            "action": { 
                "type": "Control",
                "target_id": uuid.UUID("16196aea-c59f-11ec-a6ae-00155d8c61bb"),
                "task_id": uuid.UUID("16196b1c-c59f-11ec-a6ae-00155d8c61bb"),
                "body": {"content": "Status update" }}
            }
    task = Task(payload)
    assert str(task) == "{'client_id': '16196a7c-c59f-11ec-a6ae-00155d8c61bb', 'task_id': '16196ab8-c59f-11ec-a6ae-00155d8c61bb', 'credentials': {}, 'action': {'type': 'Control', 'target_id': '16196aea-c59f-11ec-a6ae-00155d8c61bb', 'task_id': '16196b1c-c59f-11ec-a6ae-00155d8c61bb', 'body': {'content': 'Status update'}}}"
