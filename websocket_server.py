import asyncio
import websockets
import threading
import random
import string
import json
import rpc  # Add this import

class WebSocketServer:
    def __init__(self, host='localhost', port=8765, message_callback=None):
        self.host = host
        self.port = port
        self.clients = set()
        self.authenticated_clients = set()  # Track authenticated clients
        self.server = None
        self.loop = asyncio.new_event_loop()
        self.message_callback = message_callback

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        try:
            # Send a nonce to the client
            nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            await websocket.send(f"Nonce: {nonce}")

            while True:
                message = await websocket.recv()
                if message.startswith("Authenticate:"):
                    # Handle authentication
                    auth_data = json.loads(message.split(":", 1)[1])
                    signed_message = auth_data.get("signature")
                    print(f"Received signed message: {signed_message}")

                    # For now, just set authenticated to true
                    self.authenticated_clients.add(websocket)
                    await websocket.send("Authentication successful")
                else:
                    if self.message_callback:
                        response = await self.message_callback(message, websocket in self.authenticated_clients)
                        if response:
                            await websocket.send(response)
                await self.broadcast(message)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            self.authenticated_clients.discard(websocket)

    def authenticate(self, auth_data):
        # Implement your authentication logic here
        # For example, verify a signature or token
        return True  # Placeholder for successful authentication

    async def broadcast(self, message):
        if self.clients:
            disconnected_clients = []
            for client in list(self.clients):
                if client.open:
                    try:
                        await client.send(message)
                    except websockets.ConnectionClosed:
                        disconnected_clients.append(client)
            for client in disconnected_clients:
                if client in self.clients:
                    try:
                        self.clients.remove(client)
                    except KeyError:
                        pass

    def start(self):
        def run_server():
            asyncio.set_event_loop(self.loop)
            self.server = websockets.serve(self.handler, self.host, self.port, loop=self.loop)
            self.loop.run_until_complete(self.server)
            self.loop.run_forever()

        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

    def stop(self):
        if self.server:
            self.loop.call_soon_threadsafe(self.loop.stop)
            print("WebSocket server stopped.")

if __name__ == "__main__":
    ws_server = WebSocketServer(
        host='0.0.0.0',
        port=8765,
        message_callback=lambda message, is_authenticated: process_message(message, order_book, is_authenticated)
    )
    ws_server.start()
    print(f"WebSocket server started at ws://{ws_server.host}:{ws_server.port}")
    
    try:
        while True:
            pass  # Keep main thread running
    except KeyboardInterrupt:
        ws_server.stop()
