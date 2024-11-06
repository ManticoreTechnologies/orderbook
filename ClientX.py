# This is a python based client for TradeX
# There will be an html based client as well hosted on manticore.exchange
# This will be used to test connections and functionality with the TradeX server

import websockets
import asyncio
import logging

# Define custom log levels
SENT_LEVEL = 25
RECEIVED_LEVEL = 26
logging.addLevelName(SENT_LEVEL, "SENT")
logging.addLevelName(RECEIVED_LEVEL, "RECEIVED")

# Function to log at custom levels
def sent(self, message, *args, **kws):
    if self.isEnabledFor(SENT_LEVEL):
        self._log(SENT_LEVEL, message, args, **kws)

def received(self, message, *args, **kws):
    if self.isEnabledFor(RECEIVED_LEVEL):
        self._log(RECEIVED_LEVEL, message, args, **kws)

logging.Logger.sent = sent
logging.Logger.received = received

# Custom formatter using ANSI escape codes
class CustomFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[31m',   # Red
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'SENT': '\033[34m',   # Blue
        'RECEIVED': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"

# Initialize logging with custom formatter
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter('%(message)s'))
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
            logger.sent(f"Sent: {message}")
            while True:
                response = await self.websocket.recv()
                logger.received(f"Received: {response}")
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

    

    # One you receive the challenge from the server, you must sign it with your private key and send it back to the server
    async def handle_authorize_challenge(challenge):
        logger.info(f"Handling auth challenge: {challenge}")

        # Sign the challenge with your private key
        signed_challenge = sign_message(client_address, challenge)

        # Send the signed challenge back to the server
        await client.send(f"authorize_challenge {signed_challenge}")

    await client.send("Hello") # Just a simple ping for clients to test connection
    
    # Authenticate with the server
    #await client.send(f"authorize {client_address}", callback=handle_authorize_challenge)
    #await client.send("get_all_balances")
    await client.send("get_orderbook INFERNA/EVR")
    #await client.send("deposit_asset USD 100")
    #await client.send("get_balance USD")
    #await client.send("cancel_order ac1689e4-d5e9-4a74-9d89-d2358975a2c3")
    #await client.send("place_order EVR_USD bid limit 1 1")
    #await client.send("get_all_orders")
    #await client.send("get_open_orders")
    #await client.send("get_cancelled_orders")
    #await client.send("Secret")
    #await client.send("deposit_asset USD 100")
    #await client.send("get_balance USD")
    #await client.send("withdraw_asset USD 500")
    #await client.send("get_balance USD")
    #await client.send("cancel_all_orders")
    #await client.send("get_orders")
    # We can get the orderbook without authentication
    #await client.send("get_orderbook")
    
    # Authenticate and try to place an order
    #await client.send(f"auth {client_address}", callback=handle_auth_challenge)
    #await client.send("place_order market bid EVR 100 100")
    #await client.send("get_orderbook")
    
    #await client.send("get_account")
    #await client.send("new_deposit_address EVR")
    #Abstracted commands
    #await client.send("get_account_info")
    #await client.send("create_order")
    
    await client.close()

# Run the client
asyncio.get_event_loop().run_until_complete(main())
logger.info("Client finished execution")
