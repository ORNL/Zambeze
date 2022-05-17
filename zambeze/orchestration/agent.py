import asyncio
import nats
import time

async def main():
    nc = await nats.connect("172.22.1.67")
    print("Connected")
    sub = await nc.subscribe("execapp")
    msg = await sub.next_msg(timeout=100)
    await handle(msg)


async def handle(msg):

    knownmsg=["execapp","datatransfer"]
    
    if msg.subject in knownmsg:
        print(msg)
    else:
        print("Unknown message")


if __name__=="__main__":
   asyncio.run(main())
