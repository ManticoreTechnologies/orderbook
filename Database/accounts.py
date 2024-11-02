"""
This module handles the accounts database table
It will be used to store the user accounts and their balances
It should also store the users active, on-hold and closed orders
"""

# Import the sqlite3 module
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
    deposit_addresses TEXT NOT NULL
);''')


# Commit the changes and close the connection
conn.commit()
conn.close()


# Define all the helper functions here

# Create a new account
def create_account(address):
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

# Load all accounts from the database, return a list of tuples
def load_accounts_from_db():

    """Load all accounts from the database."""
    
    # Get the database connection
    conn = get_connection(db_name)

    # Select all the users from the database
    query = "SELECT * FROM accounts"

    # Execute the query
    accounts = conn.execute(query).fetchall()

    # Close the connection
    conn.close()

    # Return the accounts
    return accounts


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

# Deposit an asset to the account
def deposit_asset(address, asset, amount):

    """ While in testnet, we just add the amount to the balance """

    account = get_account(address)
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

# Test the functions
if __name__ == "__main__":
    create_account("0x1234567890abcdef", "{}", "{}")
    print(get_account("0x1234567890abcdef"))