
import nats
import asyncio
# from ..settings import ZambezeSettings
from enum import Enum


class MessageType(Enum):
    COMPUTE = "z_compute"
    DATA = "z_data"
    STATUS = "z_status"
    RESPONSE = "z_response"


async def do_a_thing():
    async def __disconnected(self):
        self._logger.info(
            f"[processor] Disconnected from nats... {self._settings.get_nats_connection_uri()}"
        )

    async def __reconnected(self):
        self._logger.info(
            f"[processor] Reconnected to nats... {self._settings.get_nats_connection_uri()}"
        )

    print("HERE1")
    nc = await nats.connect(
        servers=['nats://0.0.0.0:4222'],
        reconnected_cb=__reconnected,
        disconnected_cb=__disconnected,
        connect_timeout=1,
    )

    print("HERE3")
    # Simple publisher and async subscriber via coroutine.
    sub = await nc.subscribe(MessageType.RESPONSE.value)
    print(sub)
    print("HERE4")


    # try:
    print("HERE5")
    msg = await sub.next_msg()
    print("HERE6")
    import json
    data = json.loads(msg.data)
    print(json.dumps(data, indent=4))
    # async for msg in sub.messages:
    #     print(f"Received a message on '{msg.subject} {msg.reply}': {msg.data.decode()}")
    #     await sub.unsubscribe()
    # except Exception as e:
    #     print(e)

    # msg = sub.next_msg()
    # print(msg.data)

if __name__=="__main__":
    asyncio.run(do_a_thing())