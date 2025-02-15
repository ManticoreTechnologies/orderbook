# Import the on decorator from SocketX
import json
from Database import accounts, markets, assets
from rpc import get_asset_data
from SocketX import broadcast_to_subscribers, get_client_info, get_client_info_field, on, protected, update_client_info_field, broadcast

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

@on("get_asset_info")
async def get_asset_info(websocket, assets):
    """ Assets is list of asset names separated by commas """
    asset_data = get_asset_data(assets)
    return f"asset_info {json.dumps(asset_data)}"

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


@on("get_favorite_markets")
@protected
async def get_favorite_markets(websocket, client_info):
    return f"favorite_markets {accounts.get_favorite_markets(client_info['address'])}"

@on("favorite_market")
@protected
async def favorite_market(websocket, client_info, market_name):
    accounts.favorite_market(client_info['address'], market_name)
    return f"favorite_markets {accounts.get_favorite_markets(client_info['address'])}"

@on("unfavorite_market")
@protected
async def unfavorite_market(websocket, client_info, market_name):
    accounts.unfavorite_market(client_info['address'], market_name)
    return f"favorite_markets {accounts.get_favorite_markets(client_info['address'])}"

# TODO: Add commands for creating and managing orders
# TODO: Add commands for getting market data


""" Managing Profile """
@on("set_friendly_name")
@protected
async def set_friendly_name(websocket, client_info, friendly_name):
    accounts.set_friendly_name(client_info['address'], friendly_name)
    return f"friendly_name {friendly_name}"

@on("set_bio")
@protected
async def set_bio(websocket, client_info, bio):
    address = client_info['address']
    print(f"Updating bio for address {address} to: {bio}")
    accounts.set_bio(address, bio)
    return f"bio {bio}"


@on("set_trading_volume")
@protected
async def set_trading_volume(websocket, client_info, trading_volume):
    accounts.set_trading_volume(client_info['address'], trading_volume)
    return f"trading_volume {trading_volume}"

@on("set_status")
@protected
async def set_status(websocket, client_info, status):
    accounts.set_status(client_info['address'], status)
    return f"status {status}"

@on("set_profile_ipfs")
@protected
async def set_profile_ipfs(websocket, client_info, profile_ipfs):
    accounts.set_profile_ipfs(client_info['address'], profile_ipfs)
    return f"profile_ipfs {profile_ipfs}"

@on("set_favorite_assets")
@protected
async def set_favorite_assets(websocket, client_info, favorite_assets):
    accounts.set_favorite_assets(client_info['address'], favorite_assets)
    return f"favorite_assets {favorite_assets}"
    address = client_info['address']
    print(f"Updating profile IPFS for address {address} to: {profile_ipfs}")
    accounts.set_profile_ipfs(address, profile_ipfs)
    return f"profile_ipfs {profile_ipfs}"

# Get comments from the database, for a given asset. This is just for assets, NOT for user profiles
@on("get_asset_comments")
@protected
async def get_asset_comments(websocket, client_info, asset):
    comments = assets.get_asset_comments(asset)
    return f"asset_comments {comments}"

@on("add_asset_comment")
@protected
async def add_asset_comment(websocket, client_info, asset, address, comment):
    full_comment = assets.add_asset_comment(asset, address, comment)
    return_message = f"asset_comment_added {json.dumps(full_comment)}"
    await broadcast(return_message)
    return return_message

@on("update_asset_comment")
@protected
async def update_asset_comment(websocket, client_info, asset, comment_id, comment):
    assets.update_asset_comment(asset, comment_id, comment)
    return_message = f"asset_comment_updated {comment_id}"
    await broadcast(return_message)
    return return_message

@on("delete_asset_comment")
@protected
async def delete_asset_comment(websocket, client_info, comment_id):
    assets.delete_asset_comment(comment_id)
    return_message = f"asset_comment_deleted {comment_id}"
    await broadcast(return_message)
    return return_message




@on("get_townhall_comments")
@protected
async def get_townhall_comments(websocket, client_info):
    comments = assets.get_townhall_comments()
    return_message = f"townhall_comments {json.dumps(comments)}"
    await broadcast(return_message)
    return return_message

@on("add_townhall_comment")
@protected
async def add_townhall_comment(websocket, client_info, address, comment):
    full_comment = assets.add_townhall_comment(address, comment)
    return_message = f"townhall_comment_added {json.dumps(full_comment)}"
    await broadcast(return_message)
    return return_message

@on("update_townhall_comment")
@protected
async def update_townhall_comment(websocket, client_info, comment_id, comment):
    assets.update_townhall_comment(comment_id, comment)
    return_message = f"townhall_comment_updated {comment_id}"
    await broadcast(return_message)
    return return_message

@on("delete_townhall_comment")
@protected
async def delete_townhall_comment(websocket, client_info, comment_id):
    assets.delete_townhall_comment(comment_id)
    return_message = f"townhall_comment_deleted {comment_id}"
    await broadcast(return_message)
    return return_message



# Broadcast a message to all clients connected to the websocket
@on("broadcast_townhall_message")
@protected
async def broadcast_townhall_message(websocket, client_info, message):
    # Get the account of the address that sent the message
    address = client_info['address']
    account = json.loads(accounts.get_account_info(address))

    townhall_message = {
        "address": address,
        "friendly_name": account['friendly_name'],
        "ipfs": account['profile_ipfs'],
        "message": message
    }

    await broadcast_to_subscribers("townhall_message", f"townhall_message {json.dumps(townhall_message)}")
    return f"townhall_message {json.dumps(townhall_message)}"



