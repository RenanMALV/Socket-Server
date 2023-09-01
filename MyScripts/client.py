
import asyncio
import websockets

async def hello():
    print("Client start")
    uri = "ws://renanmalv.ddns.net:80"
    async with websockets.connect(uri) as websocket:
        name = "Renan"

        await websocket.send(name)
        print(f">>> {name}")

        greeting = await websocket.recv()
        print(f"<<< {greeting}")

asyncio.run(hello())