"""
This module handles the accounts database table
It will be used to store the user accounts and their balances
It should also store the users active, on-hold and closed orders
"""

# Import the sqlite3 module
from datetime import datetime
import json
import sqlite3

from rpc import get_new_address

db_name = "accounts"

from Database.get_connection import get_connection

# Get the database connection
conn = get_connection(db_name)


# Create the accounts table if it doesn't exist 
# id is a uuid4 string
# address is a string that stores the public evrmore address of the user (one account per address)
# Balances is a JSON string that stores the balances of the user
# Orders is a JSON string that stores the orders of the user
conn.execute('''CREATE TABLE IF NOT EXISTS accounts (
    address TEXT PRIMARY KEY,
    balances TEXT NOT NULL,
    orders TEXT NOT NULL,
    deposit_addresses TEXT NOT NULL,
    session_token TEXT,
    session_created TEXT
);''')


# Commit the changes and close the connection
conn.commit()
conn.close()


# Define all the helper functions here


""" Managing accounts"""
def create_account(address):
    print(f"Creating account for {address}")
    conn = get_connection(db_name)
    try:
        conn.execute("INSERT INTO accounts (address, balances, orders, deposit_addresses) VALUES (?, '{}', '{}', '{}')", (address,))
        conn.commit()
    except sqlite3.IntegrityError as e:
        if "unique constraint failed" in str(e):
            print("Account already registered")
            raise Exception("Account already registered")
    finally:
        conn.close()

# Load a single account from the database by address, return a named dict
def get_account(address):

    """Load a single account from the database by address and return a named dict."""

    # Get the database connection
    conn = get_connection(db_name)

    # Set the row factory to sqlite3.Row to access columns by name
    conn.row_factory = sqlite3.Row

    # Select the user from the database by address
    query = "SELECT * FROM accounts WHERE address = ?"

    # Execute the query
    account_row = conn.execute(query, (address,)).fetchone()
    
    # Close the connection
    conn.close()
    
    # If account doesn't exist, create it
    if not account_row:
        create_account(address)
        return get_account(address)  # Re-fetch the newly created account

    # Convert the row to a dictionary
    account = dict(account_row)

    # Convert the balances and orders to dictionaries
    account['balances'] = json.loads(account['balances'])
    account['orders'] = json.loads(account['orders'])   
    
    # Return the account
    return account

def get_balance(address, asset):
    account = get_account(address)
    try:
        return account['balances'][asset]
    except KeyError:
        return 0

def get_all_balances(address):
    account = get_account(address)
    return account['balances']

# Deposit an asset to the account
def deposit_asset(address, asset, amount):

    """ While in testnet, we just add the amount to the balance """
    account = get_account(address)
    if asset not in account['balances']:
        account['balances'][asset] = 0
    account['balances'][asset] = int(account['balances'][asset]) + int(amount)
    conn = get_connection(db_name)
    conn.execute("UPDATE accounts SET balances = ? WHERE address = ?", (json.dumps(account['balances']), address))
    conn.commit()
    conn.close()

def withdraw_asset(address, asset, amount):

    """ While in testnet, we just subtract the amount from the balance, if the amount withdrawn would make the balance negative, we raise an exception """

    account = get_account(address)
    current_balance = int(account['balances'][asset])
    if current_balance < int(amount):
        raise ValueError("Insufficient balance for withdrawal")
    account['balances'][asset] = current_balance - int(amount)
    conn = get_connection(db_name)
    conn.execute("UPDATE accounts SET balances = ? WHERE address = ?", (json.dumps(account['balances']), address))
    conn.commit()
    conn.close()

# Add a deposit address to the account
def get_new_deposit_address(account_address, assetName):
    deposit_address = get_new_address()
    conn = get_connection(db_name)
    current_addresses = conn.execute("SELECT deposit_addresses FROM accounts WHERE address = ?", (account_address,)).fetchone()[0]
    if current_addresses:
        updated_addresses = json.loads(current_addresses)
        if assetName in updated_addresses:
            updated_addresses[assetName].append(deposit_address)
        else:
            updated_addresses[assetName] = [deposit_address]
        updated_addresses = json.dumps(updated_addresses)
    else:
        updated_addresses = json.dumps({assetName: [deposit_address]})
    conn.execute("UPDATE accounts SET deposit_addresses = ? WHERE address = ?", (updated_addresses, account_address))
    conn.commit()
    conn.close()

    # Return the deposit address
    return deposit_address


""" Retrieving orders """
order_db = "orders"
def get_order_by_id(order_id):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order

def get_all_orders(address):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE address = ?", (address,))
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    orders = [dict(zip(headers, row)) for row in rows]
    market_orders = {}
    for order in orders:
        market = order['market']
        if market not in market_orders:
            market_orders[market] = []
        market_orders[market].append(order)
    conn.close()
    return market_orders

def get_partially_filled_orders(address):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE address = ? AND status = 'partially filled'", (address,))
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_filled_orders(address):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE address = ? AND status = 'filled'", (address,))
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_open_orders(address):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE address = ? AND status = 'open'", (address,))
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_cancelled_orders(address):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE address = ? AND status = 'cancelled'", (address,))
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    cancelled_orders = [dict(zip(headers, row)) for row in rows]
    market_orders = {}
    for order in cancelled_orders:
        market = order['market']
        if market not in market_orders:
            market_orders[market] = []
        market_orders[market].append(order)
    conn.close()
    return market_orders


""" Cancelling orders """

def cancel_all_orders(address):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'cancelled' WHERE address = ?", (address,))
    conn.commit()
    conn.close()

def cancel_all_orders_for_market(address, market):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'cancelled' WHERE address = ? AND market = ?", (address, market))
    conn.commit()
    conn.close()

def cancel_order(address, order_id):
    conn = get_connection(order_db)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'cancelled' WHERE address = ? AND id = ?", (address, order_id))
    conn.commit()
    conn.close()

""" Session management """
def set_session_token(address, session_token):
    print(f"Setting session token for {address}: {session_token}")
    conn = get_connection(db_name)
    conn.execute("UPDATE accounts SET session_token = ?, session_created = ? WHERE address = ?", (session_token, datetime.now().isoformat(), address))
    conn.commit()
    conn.close()

    session_data = get_session_token(address)
    print(f"Session data: {session_data}")

def get_session_token(address):
    conn = get_connection(db_name)
    print(f"Getting session token for {address}")
    account = get_account(address)
    print(f"Account: {account}")
    session_data = conn.execute("SELECT session_token, session_created FROM accounts WHERE address = ?", (address,)).fetchone()
    print(f"Session data: {session_data}")
    conn.close()
    if session_data:
        return {"session_token": session_data[0], "session_created": session_data[1]}
    else:
        return None