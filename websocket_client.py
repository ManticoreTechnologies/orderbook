import asyncio
import websockets

async def listen_to_orderbook():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected to the WebSocket server.")
        try:
            while True:
                message = await websocket.recv()
                print(f"Received message: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(listen_to_orderbook())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            # If the event loop is already running, use it
            loop = asyncio.get_event_loop()
            loop.run_until_complete(listen_to_orderbook())
        else:
            raise
