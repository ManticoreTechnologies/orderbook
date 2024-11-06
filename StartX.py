# Asyncio is used to run the websocket server
import asyncio
import json
import os
# Import the start_server function from SocketX
from SocketX import start_server

# Import the command handlers from CommandX
from CommandX import *



""" The following imports and configuration are required to use the Coinbase CDP API 
    We will use the Coinbase CDP API to create USDC addresses on the BASE chain.
    Each account will have a deposit address for USDC. This will be the same forever.
    The deposit address will be used to send USDC to the account.
"""



if __name__ == "__main__":
    try:
        # Run the start_server coroutine
        asyncio.run(start_server())  
    except KeyboardInterrupt:
        # If the user presses Ctrl+C, print a message and stop the server
        print("Server stopped manually")
    except Exception as e:
        # If an error occurs, print the error message
        print(f"Server error: {e}")
