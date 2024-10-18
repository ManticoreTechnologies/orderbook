import asyncio
import websockets
import threading

class WebSocketServer:
    def __init__(self, host='localhost', port=8765, message_callback=None):
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None
        self.loop = asyncio.new_event_loop()
        self.message_callback = message_callback  # Add a callback parameter

    async def handler(self, websocket, path):
        # Register client
        self.clients.add(websocket)
        try:

            while True:
                message = await websocket.recv()  # Receive a message from the client
                print(f"Received message: {message}")
                
                # Call the callback function if it's provided
                if self.message_callback:
                    response = await self.message_callback(message)
                    if response:
                        await websocket.send(response)
                
                # Echo received message (you could handle incoming messages differently here)
                await self.broadcast(message)
        except websockets.ConnectionClosed:
            pass
        finally:
            # Unregister client
            self.clients.remove(websocket)

    async def broadcast(self, message):
        # Broadcast a message to all connected clients
        if self.clients:
            disconnected_clients = []
            for client in self.clients:
                if client.open:
                    try:
                        await client.send(message)
                    except websockets.ConnectionClosed:
                        disconnected_clients.append(client)
            # Remove disconnected clients after the iteration
            for client in disconnected_clients:
                self.clients.remove(client)

    def start(self):
        # Start the WebSocket server
        def run_server():
            asyncio.set_event_loop(self.loop)
            self.server = websockets.serve(self.handler, self.host, self.port, loop=self.loop)
            self.loop.run_until_complete(self.server)
            self.loop.run_forever()

        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

    def stop(self):
        # Stop the WebSocket server
        if self.server:
            self.loop.call_soon_threadsafe(self.loop.stop)
            print("WebSocket server stopped.")

if __name__ == "__main__":
    ws_server = WebSocketServer()
    ws_server.start()
    print(f"WebSocket server started at ws://{ws_server.host}:{ws_server.port}")
    
    try:
        while True:
            pass  # Keep main thread running
    except KeyboardInterrupt:
        ws_server.stop()
