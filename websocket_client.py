import asyncio
import websockets


async def listen_to_orderbook():
    uri = "ws://localhost:8765"
    while True:
        try:
            async with websockets.connect(uri, timeout=10) as websocket:  # Set timeout to 10 seconds
                print("Connected to the WebSocket server.")
                while True:
                    message = await websocket.recv()
                    print(f"Received message: {message}")
        except (websockets.ConnectionClosed, asyncio.CancelledError):
            print("WebSocket connection closed. Reconnecting...")
            await asyncio.sleep(1)  # Wait a bit before reconnecting

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
