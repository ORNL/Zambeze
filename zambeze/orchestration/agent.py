import asyncio
import nats
import time

async def main():
    nc = await nats.connect("172.22.1.67")
    print("Connected")
    sub = await nc.subscribe("execapp")
    while True:
        msg = await sub.next_msg()
        handle(msg)
        print("Message handles, going to sleep for 10s")
        time.sleep(10)


async def handle(msg):

    knownmsg=["execapp","datatransfer"]
    
    if msg in knownmsg:
        print(msg)
    else:
        print("Unknown message")


if __name__=="__main__":
   asyncio.run(main())
