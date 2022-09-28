# Local imports
from zambeze.orchestration.queue.queue_nats import QueueNats
from zambeze.orchestration.queue.queue_factory import MessageType
from zambeze.orchestration.queue.queue_factory import QueueType

# Standard imports
import os
import pwd
import pytest
import random
import socket


@pytest.mark.unit
def test_queue_nats_type():
    queue = QueueNats()
    assert queue.type == QueueType.NATS

@pytest.mark.unit
def test_queue_nats_uri():

    queue = QueueNats({})
    assert queue.uri == "nats://127.0.0.1:4222"

    config = {}
    config["ip"] = "127.0.0.1"
    config["port"] = "4222"
    queue = QueueNats(config)
    assert queue.uri == f"nats://{config['ip']}:{config['port']}"


@pytest.mark.unit
def test_queue_nats_connected():

    queue = QueueNats({})
    assert queue.uri == "nats://127.0.0.1:4222"

    config = {}
    config["ip"] = "127.0.0.1"
    config["port"] = "4222"
    queue = QueueNats(config)
    assert queue.connected is False


@pytest.mark.gitlab_runner
def test_queue_nats_connect_close():

    config = {}
    config["ip"] = os.getenv("ZAMBEZE_CI_TEST_NATS_IP")
    config["port"] = os.getenv("ZAMBEZE_CI_TEST_NATS_PORT")

    queue = QueueNats(config)

    queue = QueueNats(config)
    assert queue.connected is False
    queue.connect()
    assert queue.connected
    queue.close()
    assert queue.connected is False


@pytest.mark.gitlab_runner
def test_queue_nats_subscribe():

    config = {}
    config["ip"] = os.getenv("ZAMBEZE_CI_TEST_NATS_IP")
    config["port"] = os.getenv("ZAMBEZE_CI_TEST_NATS_PORT")

    queue = QueueNats(config)

    assert len(queue.subscriptions) == 0
    queue.subscribe(MessageType.TEST)
    assert len(queue.subscriptions) == 1
    assert queue.subscriptions[0] == MessageType.TEST
    queue.subscribe(MessageType.ACTIVITY)
    assert len(queue.subscriptions) == 2
    queue.unsubscribe(MessageType.TEST)
    assert len(queue.subscriptions) == 1
    assert queue.subscriptions[0] == MessageType.ACTIVITY


@pytest.mark.gitlab_runner
def test_queue_nats_send_subscribe_nextMsg():

    config = {}
    config["ip"] = os.getenv("ZAMBEZE_CI_TEST_NATS_IP")
    config["port"] = os.getenv("ZAMBEZE_CI_TEST_NATS_PORT")

    queue = QueueNats(config)

    queue.connect()
    original_number = random.randint(0, 100000000000)
    queue.send(MessageType.TEST, {"value": original_number})
    queue.subscribe(MessageType.TEST)
    returned_msg = queue.nextMsg(MessageType.TEST)
    assert returned_msg["value"] == original_number
    queue.close()
