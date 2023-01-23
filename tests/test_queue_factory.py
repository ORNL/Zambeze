# Local imports
from zambeze.orchestration.queue.queue_factory import QueueFactory
from zambeze.orchestration.zambeze_types import ChannelType, QueueType

# Standard imports
import asyncio
import pytest
import os
import random
import logging


async def factory_nats(queue):
    await queue.connect()
    await queue.subscribe(ChannelType.TEST)
    original_number = random.randint(0, 100000000000)
    await queue.send(ChannelType.TEST, {"value": original_number})
    returned_msg = await queue.next_msg(ChannelType.TEST)
    assert returned_msg["value"] == original_number
    await queue.close()


@pytest.mark.gitlab_runner
def test_factory_nats():

    logger = logging.getLogger(__name__)
    factory = QueueFactory(logger)
    config = {}
    config["ip"] = os.getenv("ZAMBEZE_CI_TEST_NATS_IP")
    config["port"] = os.getenv("ZAMBEZE_CI_TEST_NATS_PORT")

    queue = factory.create(QueueType.NATS, config)
    asyncio.run(factory_nats(queue))
