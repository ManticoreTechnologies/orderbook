# This is a python based client for TradeX
# There will be an html based client as well hosted on manticore.exchange
# This will be used to test connections and functionality with the TradeX server

import websockets
import asyncio
import logging
import colorlog

# Initialize logging with colorlog
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
))
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class TradeXClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info("Connected to the server")
        except ConnectionRefusedError:
            logger.error("Failed to connect to the server. Please ensure the server is running and accessible.")
            self.websocket = None

    async def send(self, message, callback=None):
        if self.websocket:
            await self.websocket.send(message)
            logger.info(f"Sent: {message}")
            while True:
                response = await self.websocket.recv()
                logger.info(f"Received response: {response}")
                if callback and response.startswith("auth_challenge"):
                    # Parse the response to extract the challenge
                    _, challenge = response.split(maxsplit=1)
                    await callback(challenge)
                    break
                elif not callback:
                    return response
        else:
            logger.error("No connection established. Cannot send message.")

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            logger.info("Connection closed")


from rpc import sign_message
async def main():
    client = TradeXClient("ws://localhost:8765")
    await client.connect()

    client_name = "Phoenix"
    client_address = "EdsY3uu7tteVKCr7FdkrWs26t75LBwy4wQ"

    
    async def handle_auth_challenge(challenge):
        logger.info(f"Handling auth challenge: {challenge}")
        # Send back the signed challenge to the server with command auth_challenge_response
        signed_challenge = sign_message(client_address, challenge)
        await client.send(f"auth_challenge_response {signed_challenge}")
        # Add logic to handle the auth challenge here

    # Try using protected commands before authenticating    
    
    # Every client MUST send a greetings_from message to the server, otherwise they are ignored
    await client.send(f"greetings_from {client_name}")
    
    # We can get the orderbook without authentication
    await client.send("get_orderbook")
    
    # Authenticate and try to place an order
    await client.send(f"auth {client_address}", callback=handle_auth_challenge)
    await client.send("place_order market bid EVR 100 100")
    await client.send("get_orderbook")
    
    #await client.send("get_account")
    #await client.send("new_deposit_address EVR")
    #Abstracted commands
    #await client.send("get_account_info")
    #await client.send("create_order")
    
    await client.close()

# Run the client
asyncio.get_event_loop().run_until_complete(main())
logger.info("Client finished execution")
