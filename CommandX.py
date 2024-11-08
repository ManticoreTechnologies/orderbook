# Import the on decorator from SocketX
from Database import accounts, markets
from SocketX import get_client_info, get_client_info_field, on, protected, update_client_info_field

""" Here we define the commands that the server will handle 
    Each command is a function that takes a websocket and returns a response
    The command decorator @on("command_name") is used to register the command
    The protected decorator @protected is used to protect the command
    Protected commands are only available to authenticated clients and are passed the client_info dictionary of the clients account
    Authentication is handled in the SocketX.py file
"""


""" Public commands that are available to all clients, authenticated or not """

@on("get_all_markets")
async def get_all_markets(websocket):

    print("Fetching all markets from the database")
    return f"all_markets {markets.list_all_markets()}"

@on("get_market_info")
async def get_market_info(websocket, market_name):
    return f"market_info {markets.get_market_info(market_name)}"

@on("get_orderbook")
async def get_orderbook(websocket, market_name):
    print(f"Fetching orderbook for {market_name}")
    return f"orderbook {markets.get_orderbook(market_name)}"

""" 
    The following commands are protected and focus on interacting with user accounts
    User accounts are stored in the database, each account has a client_address which is the address that the client will use to interact with the server
    the client_address must be unique, if a client tries to register with a duplicate address, the server will return an error
    Each account has a balance dictionary which contains the balance of the account in each currency
"""

@on("get_balance")
@protected
async def get_balance(websocket, client_info, asset):
    print(f"Getting balance for {asset}")
    """ Balances are stored in the database 
        We need to get the balance from the database and return it to the client
    """
    balance = accounts.get_balance_for_asset(client_info['address'], asset)
    return f"balance {asset} {balance}"
    

@on("get_deposit_addresses")
@protected
async def get_deposit_addresses(websocket, client_info):
    deposit_addresses = accounts.get_deposit_addresses(client_info['address'])
    return f"deposit_addresses {deposit_addresses}"

@on("get_all_balances")
@protected
async def get_all_balances(websocket, client_info):
    balances = accounts.get_all_balances(client_info['address'])
    return f"all_balances {balances}"

@on("deposit_asset")
@protected
async def deposit_asset(websocket, client_info, asset, amount):
    """ We are currently on testnet, so we just add the amount to the balance """
    new_balance = accounts.deposit_asset(client_info['address'], asset, int(amount))
    return f"deposit_success {asset} {new_balance}"

@on("withdraw_asset")
@protected
async def withdraw_asset(websocket, client_info, asset, amount):
    """ We are currently on testnet, so we just subtract the amount from the balance """
    try:
        new_balance = accounts.withdraw_asset(client_info['address'], asset, int(amount))
        return f"withdraw_success {asset} {new_balance}"
    except Exception as e:
        return f"withdraw_error {e}"

@on("cancel_order")
@protected
async def cancel_order(websocket, client_info, order_id):
    accounts.cancel_order(client_info['address'], order_id)
    return f"Order {order_id} cancelled"

@on("get_open_orders")
@protected
async def get_open_orders(websocket, client_info):
    open_orders = accounts.get_open_orders(client_info['address'])
    return f"Open orders: {open_orders}"

@on("get_cancelled_orders")
@protected
async def get_cancelled_orders(websocket, client_info):
    cancelled_orders = accounts.get_cancelled_orders(client_info['address'])
    return f"Cancelled orders: {cancelled_orders}"

@on("get_account_info")
@protected
async def get_account_info(websocket, client_info):
    return f"account_info {accounts.get_account_info(client_info['address'])}"


# TODO: Add commands for creating and managing orders
# TODO: Add commands for getting market data
