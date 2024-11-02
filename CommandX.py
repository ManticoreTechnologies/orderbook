# Import the on decorator from SocketX
from Database import accounts
from SocketX import get_client_info, get_client_info_field, on, protected, update_client_info_field

""" Here we define the commands that the server will handle 
    Each command is a function that takes a websocket and returns a response
    The command decorator @on("command_name") is used to register the command
    The protected decorator @protected is used to protect the command
    Protected commands are only available to authenticated clients and are passed the client_info dictionary of the respective client
"""

# A simple public command
@on("Hello")
async def Hello(websocket):
    return "Hello from server"

# A simple protected command
@on("Secret")
@protected
async def Secret(websocket, client_info):
    return f"Super Secret message from server, i know your address ;)... {client_info['address']}"


""" 
    The following commands are protected and focus on interacting with user accounts
    User accounts are stored in the database, each account has a client_address which is the address that the client will use to interact with the server
    the client_address must be unique, if a client tries to register with a duplicate address, the server will return an error
    Each account has a balance dictionary which contains the balance of the account in each currency
"""

@on("get_balance")
@protected
async def get_balance(websocket, client_info, asset):
    """ Balances are stored in the database 
        We need to get the balance from the database and return it to the client
    """
    balance = accounts.get_balance(client_info['address'], asset)
    return f"Your balance is {balance}"
    
@on("deposit_asset")
@protected
async def deposit_asset(websocket, client_info, asset, amount):
    """ We are currently on testnet, so we just add the amount to the balance """
    accounts.deposit_asset(client_info['address'], asset, int(amount))
    return f"You have deposited {amount} of {asset}. Your new balance is {accounts.get_balance(client_info['address'], asset)}"

@on("withdraw_asset")
@protected
async def withdraw_asset(websocket, client_info, asset, amount):
    """ We are currently on testnet, so we just subtract the amount from the balance """
    try:
        accounts.withdraw_asset(client_info['address'], asset, int(amount))
        return f"You have withdrawn {amount} of {asset}. Your new balance is {accounts.get_balance(client_info['address'], asset)}"
    except Exception as e:
        return f"Error withdrawing {amount} of {asset}: {e}"