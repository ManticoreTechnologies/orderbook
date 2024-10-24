import asyncio
import websockets
import json
import rpc


async def authenticate_and_listen():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Receive nonce from server
        nonce_message = await websocket.recv()
        nonce = nonce_message.split(": ")[1]

        # Sign the nonce
        signed_message = rpc.sign_message("EdsY3uu7tteVKCr7FdkrWs26t75LBwy4wQ", message)

        # Send authentication message
        auth_message = {
            "public_address": "EdsY3uu7tteVKCr7FdkrWs26t75LBwy4wQ",
            "signature": signed_message.signature.hex()
        }
        await websocket.send(json.dumps(auth_message))

        # Receive authentication response
        auth_response = await websocket.recv()
        print(auth_response)

        if "successful" in auth_response:
            while True:
                message = await websocket.recv()
                print(f"Received message: {message}")


async def test_basic_connection():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected to the WebSocket server")


if __name__ == "__main__":
    asyncio.run(test_basic_connection())
