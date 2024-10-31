import asyncio
import websockets
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary to store event handlers
event_handlers = {}


def on(event_name):
    """Decorator to register an event handler."""
    def decorator(func):
        event_handlers[event_name] = func
        return func
    return decorator

# This will be the websocket server for all of TradeX
# It will be used to send and receive messages from the TradeX clients
async def hello(websocket, path):
    try:
        while True:
            message = await websocket.recv()
            logger.info(f"Received message: {message}")

            # Split the message into command and arguments
            parts = message.split()
            command = parts[0]
            args = parts[1:]

            # Check if there's a registered handler for the command
            if command in event_handlers:
                try:
                    # Pass the arguments to the handler
                    response = await event_handlers[command](websocket,*args)
                    await websocket.send(response)
                    logger.info(f"Sent response: {response}")
                except Exception as e:
                    error_message = f"Error processing command '{command}': {e}"
                    await websocket.send(error_message)
                    logger.error(error_message)
            else:
                warning_message = f"No handler for command: {command}"
                await websocket.send(warning_message)
                logger.warning(warning_message)

    except websockets.ConnectionClosed as e:
        logger.error(f"Connection closed: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

async def start_server():
    """Start the WebSocket server."""
    start_server = await websockets.serve(hello, "localhost", 8765)
    logger.info("WebSocket server started on ws://localhost:8765")
    await start_server.wait_closed()

def run_server():
    """Run the WebSocket server."""
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped manually")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    run_server()
