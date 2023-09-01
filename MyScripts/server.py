import asyncio

import websockets


async def hello(websocket):

    name = await websocket.recv()

    print(f"<<< {name}")


    greeting = f"Hello {name}!"


    await websocket.send(greeting)

    print(f">>> {greeting}")


async def main():

    async with websockets.serve(hello, "192.168.0.4", 80):

        await asyncio.Future()  # run forever


if __name__ == "__main__":
    print("Server start")
    asyncio.run(main())