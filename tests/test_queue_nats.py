# Local imports
from zambeze.orchestration.queue.queue_nats import QueueNATS
from zambeze.orchestration.zambeze_types import ChannelType, QueueType

# Standard imports
import asyncio
import os
import pytest
import random


@pytest.mark.nats
def test_queue_nats_type():
    queue = QueueNATS({})
    assert queue.type == QueueType.NATS


@pytest.mark.nats
def test_queue_nats_uri():
    queue = QueueNATS({})
    assert queue.uri == "nats://127.0.0.1:4222"

    config = {}
    config["ip"] = "127.0.0.1"
    config["port"] = "4222"
    queue = QueueNATS(config)
    assert queue.uri == f"nats://{config['ip']}:{config['port']}"


@pytest.mark.nats
def test_queue_nats_connected():
    queue = QueueNATS({})
    assert queue.uri == "nats://127.0.0.1:4222"

    config = {}
    config["ip"] = "127.0.0.1"
    config["port"] = "4222"
    queue = QueueNATS(config)
    assert queue.connected is False


async def queue_nats_connect_close(config):
    queue = QueueNATS(config)
    assert queue.connected is False
    result = await queue.connect()
    print(result)
    assert queue.connected
    await queue.close()
    assert queue.connected is False


@pytest.mark.nats
def test_queue_nats_connect_close():
    config = {}
    config["ip"] = os.getenv("ZAMBEZE_CI_TEST_NATS_IP")
    config["port"] = os.getenv("ZAMBEZE_CI_TEST_NATS_PORT")

    asyncio.run(queue_nats_connect_close(config))


async def queue_nats_subscribe(config):
    queue = QueueNATS(config)
    assert len(queue.subscriptions) == 0
    await queue.connect()
    await queue.subscribe(ChannelType.TEST)
    assert len(queue.subscriptions) == 1
    assert queue.subscriptions[0] == ChannelType.TEST
    await queue.subscribe(ChannelType.ACTIVITY)
    assert len(queue.subscriptions) == 2
    await queue.unsubscribe(ChannelType.TEST)
    assert len(queue.subscriptions) == 1
    assert queue.subscriptions[0] == ChannelType.ACTIVITY


@pytest.mark.nats
def test_queue_nats_subscribe():
    config = {}
    config["ip"] = os.getenv("ZAMBEZE_CI_TEST_NATS_IP")
    config["port"] = os.getenv("ZAMBEZE_CI_TEST_NATS_PORT")
    asyncio.run(queue_nats_subscribe(config))


async def queue_nats_send_subscribe_nextMsg(config, original_number):
    queue = QueueNATS(config)
    await queue.connect()
    await queue.subscribe(ChannelType.TEST)
    await queue.send(ChannelType.TEST, {"value": original_number})
    returned_msg = await queue.next_msg(ChannelType.TEST)
    assert returned_msg["value"] == original_number
    await queue.close()


@pytest.mark.nats
def test_queue_nats_send_subscribe_nextMsg():
    config = {}
    config["ip"] = os.getenv("ZAMBEZE_CI_TEST_NATS_IP")
    config["port"] = os.getenv("ZAMBEZE_CI_TEST_NATS_PORT")
    original_number = random.randint(0, 100000000000)

    asyncio.run(queue_nats_send_subscribe_nextMsg(config, original_number))
