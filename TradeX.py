from datetime import datetime
from Database import accounts
from SocketX import on, start_server
import secrets

from rpc import verify_message, get_new_address


# Create a dictionary to store the client's account information
clients_info = {} # websocket: client_info_template
client_info_template = {
    "name": None, 
    "address": None, 
    "authenticated": False, 
    "challenge": None, 
    "history_of_successful_authentications": [], 
    "history_of_failed_authentications": [], 
    "deposit_addresses": None # {asset: address}
}


def protected(func):
    # Decorator to make a command protected
    async def wrapper(websocket, *args, **kwargs):
        # Check if the websocket is in the clients_info dictionary
        print(f"------------------------------")
        print(websocket)
        try:
            client_info = clients_info[websocket]
        except KeyError:
            return "Woah there, who the fuck are you?! Please send a greetings_from message."

        # Check if the client is authenticated
        if not client_info.get("authenticated", False):
            # Return a coroutine that yields the error message
            return await asyncio.sleep(0, result="You are not authenticated. Please authenticate yourself with the 'auth' command.")

        # Call the original function if authenticated
        return await func(websocket, *args, **kwargs)
    return wrapper

# Every client that connects to the server will send a greetings_from message
# This is used to identify the client and send a welcome message so the client knows it is connected
@on("greetings_from")
async def init_connection(websocket, client_name):

    # Copy the client info template and add the name
    clients_info[websocket] = {"name": client_name, "address": None, "authenticated": False, "challenge": None, "history_of_successful_authentications": [], "history_of_failed_authentications": [], "deposit_addresses": None}

    # Return a welcome message to the client
    return f"Hello {clients_info[websocket]['name']}! Welcome to TradeX. You are connected via an unauthenticated connection. Please authenticate yourself with the 'auth' command."

# Every client that connects to the server will optionally send an auth message
# This is used to authenticate the client and allow access to protected commands for that specific address
@on("auth")
async def auth(websocket, address):
    print(f"Authenticating client {address} via websocket {websocket}")
    # The first step of every authentication process is to provide the client with a challenge
    # This challenge is a random number that the client must sign with their private key
    # The server will verify the signature and if valid, will authenticate the client
    # The server will then return the client with their account information
    clients_info[websocket]["address"] = address
    # Lets begin by creating a challenge
    challenge = secrets.token_hex(16)
    clients_info[websocket]["challenge"] = challenge
    # Send the challenge to the client
    return f"auth_challenge {challenge}"

# The next step of authentication is to wait for the client to send the signed challenge
@on("auth_challenge_response")
async def auth_challenge_response(websocket, signature):
    # The server will verify the signature and if valid, will authenticate the client
    # The server will then return the client with their account information

    if verify_message(clients_info[websocket]["address"], signature, clients_info[websocket]["challenge"]):
        # Add authenticated flag to the client's info
        clients_info[websocket]["authenticated"] = True
        # Remove the challenge from the client's info so it cannot be reused
        clients_info[websocket]["challenge"] = None

        # Log the authentication to the clients history of successful authentications
        clients_info[websocket]["history_of_successful_authentications"].append(f"{datetime.now()}, {clients_info[websocket]['address']}")

        # Return the client with their account information
        return f"Authentication successful. Welcome {clients_info[websocket]['name']}! Your address is {clients_info[websocket]['address']}. Now that you are authenticated, you can use the 'get_account_info', 'create_order', and other protected commands."
    else:
        # Log the authentication to the clients history of failed authentications
        clients_info[websocket]["history_of_failed_authentications"].append(f"{datetime.now()}, {clients_info[websocket]['address']}")
        return "Authentication failed. The signature provided does not match the challenge. This failed attempt has been logged. Please try again."



@on("get_account")
@protected
async def get_account(websocket):
    """ Get the account info from the database and return it to the client 
    if an account does not exist, create a new one with empty balances and orders """

    # Get the account info from the database
    account_info = accounts.get_account(clients_info[websocket]["address"])
    if account_info is None:
        # If the account is none then just create a new account with empty balances and orders
        accounts.create_account(clients_info[websocket]["address"])
        account_info = accounts.get_account(clients_info[websocket]["address"])
        return f"{account_info}"
    else:
        return f"{account_info}"

@on("place_order")
@protected
async def place_order(websocket, type, side, market, quantity, price):
    # Place the order in the orderbook
    # Return the order id
    # Ideally we will just be able to do:
    # orderbook.place_order(order)
    # And order is a dictionary with the following keys:
    # "type": "market" or "limit"
    # "side": "bid" or "ask"
    # "market": "EVR-USD"
    # "quantity": 100
    # "price": 100
    # Im going to make a new orderbook class that will handle the orderbook and the orders
    return f"Order placed successfully. Order ID is 1234567890."

@on("cancel_order")
@protected
async def cancel_order(websocket, order_id):
    # Cancel the order in the orderbook
    # Return the order id
    # Ideally we will just be able to do:
    # orderbook.cancel_order(order_id)
    return "Order cancelled successfully. Order ID is 1234567890."

@on("new_deposit_address")
@protected
async def new_deposit_address(websocket, assetName):
    print(f"Getting a new deposit address for {assetName} for {clients_info[websocket]['address']}")
    """ Get a new deposit address from the database and return it to the client """
    return accounts.get_new_deposit_address(clients_info[websocket]["address"], assetName)

@on("get_asks")
async def get_asks(websocket):
    return f"{order_book.asks}"

@on("get_bids")
async def get_bids(websocket):
    return f"{order_book.bids}"

@on("get_orderbook")
async def get_orderbook(websocket):
    return f"{{bids: {order_book.bids}, asks: {order_book.asks}}}"



