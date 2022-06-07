import asyncio
import nats

# import time


async def main():
    nc = await nats.connect("172.22.1.67")
    knownmsg = ["execapp", "datatransfer"]

    async def handle(msg):
        if msg.subject in knownmsg:
            print(msg)
        else:
            print("Unknown message")

    # sub = await nc.subscribe("execapp", cb=handle)

    sub2 = await nc.subscribe("execapp")
    while True:
        try:
            msg = await sub2.next_msg()
            print("Message received", msg)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
