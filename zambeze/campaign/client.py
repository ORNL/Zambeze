import asyncio
import nats
import json


async def main():
    nc = await nats.connect("172.22.1.67")

    await nc.publish("execapp", b"/bin/echo hello world.")
    await nc.publish("execapp", json.dumps("task":"hello","cmd":"/bin/echo","args":"Hello World!").encode())

    await nc.close()


if __name__ == "__main__":
    asyncio.run(main())
