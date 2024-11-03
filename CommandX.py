# Import the on decorator from SocketX
from Database import accounts, orders
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

@on("place_order")
@protected
async def place_order(websocket, client_info, market, side, type, amount, price):
    #split market into base and quote
    base = market.split("_")[0]
    quote = market.split("_")[1]
    # Get the clients account
    account_info = accounts.get_account(client_info['address'])
    if account_info is None:
        raise Exception("Account not found")
    # Check the balance of the account
    balance = accounts.get_balance(client_info['address'], quote)
    print(f"Balance: {balance}")
    if int(balance) < int(amount):
        return f"Insufficient balance for {amount} of {quote}"
    # Place the order
    try:
        order_id = orders.place_order(client_info['address'], market, side, type, amount, price)
        return f"Your order has been placed with id {order_id}"
    except Exception as e:
        return f"Error placing order: {e}"

@on("get_orders")
@protected
async def get_orders(websocket, client_info):
    
    account_orders = orders.get_account_orders(client_info['address'])
    return f"account_orders: {account_orders}"

@on("cancel_all_orders")
@protected
async def cancel_all_orders(websocket, client_info):
    orders.cancel_all_orders(client_info['address'])
    return f"All orders cancelled"

@on("cancel_all_order_for_market")
@protected
async def cancel_all_order_for_market(websocket, client_info, market):
    orders.cancel_all_orders_for_market(client_info['address'], market)
    return f"All orders for {market} cancelled"

# TODO: Add commands for creating and managing orders
# TODO: Add commands for getting market data
