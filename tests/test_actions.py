import pytest
import uuid

from zambeze.actions import Factory

###############################################################################
# Testing Action: Control
###############################################################################
def test_action_control():
    payload = {
        "type": "Control",
        "target_id": uuid.UUID("69bb52ce-c59c-11ec-abff-00155d8c61bb"),
        "task_id": uuid.UUID("4c963e70-c59c-11ec-bb5f-00155d8c61bb"),
        "body": "This is the body",
    }
    control_action = Factory(payload)
    print(str(control_action))
    assert (
        str(control_action)
        == "{'type': 'Control', 'target_id': '69bb52ce-c59c-11ec-abff-00155d8c61bb', 'task_id': '4c963e70-c59c-11ec-bb5f-00155d8c61bb', 'body': 'This is the body'}"
    )


def test_action_control_missing_target_id():
    payload = {"type": "Control", "task_id": uuid.uuid1(), "body": "This is the body"}

    with pytest.raises(Exception):
        assert Factory(payload)


def test_action_control_missing_task_id():
    payload = {"type": "Control", "target_id": uuid.uuid1(), "body": "This is the body"}

    with pytest.raises(Exception):
        assert Factory(payload)


def test_action_control_missing_type():
    payload = {
        "task_id": uuid.uuid1(),
        "target_id": uuid.uuid1(),
        "body": "This is the body",
    }

    with pytest.raises(Exception):
        assert Factory(payload)


###############################################################################
# Testing Action: Data
###############################################################################
def test_action_data():
    payload = {
        "type": "Data",
        "source": "/home/source/file1.txt",
        "destination": "home/dest/file1.txt",
    }
    data_action = Factory(payload)
    print(str(data_action))
    assert (
        str(data_action)
        == "{'type': 'Data', 'source': '/home/source/file1.txt', 'destination': 'home/dest/file1.txt'}"
    )


def test_action_data_missing_type():
    payload = {"source": "/home/source/file1.txt", "destination": "home/dest/file1.txt"}

    with pytest.raises(Exception):
        assert Factory(payload)


def test_action_data_missing_source():
    payload = {"type": "Data", "destination": "home/dest/file1.txt"}

    with pytest.raises(Exception):
        assert Factory(payload)


def test_action_data_missing_destination():
    payload = {
        "type": "Data",
        "source": "/home/source/file1.txt",
    }

    with pytest.raises(Exception):
        assert Factory(payload)


###############################################################################
# Testing Action: Compute
###############################################################################


def test_action_compute():
    payload = {
        "type": "Compute",
        "workflow_id": uuid.UUID("8353332c-c59d-11ec-9b3a-00155d8c61bb"),
        "parameters": {"compute": "this is a workflow param"},
    }
    com = Factory(payload)
    assert (
        str(com)
        == "{'type': 'Compute', 'workflow_id': '8353332c-c59d-11ec-9b3a-00155d8c61bb', 'parameters': {'compute': 'this is a workflow param'}}"
    )
