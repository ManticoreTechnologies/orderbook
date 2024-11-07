""" accounts.py

    For all the functions that handle the accounts data
    Accounts are identified by a public evrmore address provided by the user

"""

""" Imports"""
from Database import markets
from HelperX import generate_unique_id, read_config_file, create_table
from Database.get_connection import get_connection
from datetime import datetime, timedelta
import json
import rpc

""" Database name 
    I am calling this database manticore_accounts
    This is where we will store all the accounts data
"""
database_name = "manticore_accounts" 

""" Get the connection to the database """
database_connection = get_connection(database_name)

""" Configuration 
    Read the supported assets from the TradeX.conf file 
    This will be updated when we add support for more markets
    This could stay separate from crating new markets but we should sync them
"""
config = read_config_file('TradeX.conf')
supported_assets = json.loads(config["Accounts"]["supported_assets"])

""" Custom exception 

    This exception is raised when an account already exists
"""
class AccountExistsException(Exception):
    """ Exception raised for errors in the input salary. """
    pass

""" Tables in the database
    Each table has a common primary key, which is the address of the account
    To allow for scaling, we will use multiple tables instead of one big table
    We can add new tables by editing the create_tables function

    accounts: Stores basic account information (address, profile_ipfs, created)
    authentication: Stores the authentication data (address, session token, challenge, etc)
    addresses: Stores the deposit addresses for an account (usdc, evr, etc)
    balances: Stores the balances for an account (usdc, evr, etc)
    orders: Stores all the orders for an account (open, filled, cancelled)

"""

""" Create the accounts table 

    address: The public evrmore address of the user
    profile_ipfs: The ipfs hash of the user's profile picture
    created: The date and time the account was created (the first time the user logged in)

    * Manticore users do not have a password, nor do they "create" an account.
    * Users simply authenticate by signing a challenge sent by the server
"""

database_connection.execute(
    '''CREATE TABLE IF NOT EXISTS accounts (
        address TEXT PRIMARY KEY,
        profile_ipfs TEXT,
        created TEXT
    );''')

""" Create the authentication table

    address: The public evrmore address of the user
    session_token: The session token for the user
    session_created: The date and time the session was created

    * The session token is a cookie that is used to allow a user to stay authenticated
    * The session token expires after a set amount of time, and the user will have to authenticate again
    * The only opsec risk of the session token is cookie theft, which is why it expires. How can we identify if the session token is stolen?
    * ______________
"""

database_connection.execute(
    '''CREATE TABLE IF NOT EXISTS authentication (
        address TEXT PRIMARY KEY,
        session_token TEXT,
        session_created TEXT
    );''')

""" Create the addresses table

    address: The public evrmore address of the user
    **supported assets**
    evr: The evrmore address for the user
    usdm: The usdm address for the user
    ... any other assets we support in the future

    * The supported assets are defined in the TradeX.conf file
"""

create_table(database_connection.cursor(), "addresses", supported_assets)

""" Create the balances table

    address: The public evrmore address of the user
    **supported assets**
    evr: The evrmore balance for the user
    usdm: The usdm balance for the user
    ... any other assets we support in the future

    * The balances are all in satoshis (10^-8, the smallest unit of evrmore)
"""

create_table(database_connection.cursor(), "balances", supported_assets)




# Commit the changes to the database
database_connection.commit()

""" Creating and purging accounts
"""

""" Initialize a user account """
def init_account(address):
    
    """ 
        Initialize a user account, for first time users 
        
        We have multiple tables to update

        accounts: address, profile_ipfs, created

        For the accounts table, we need to add the address, profile_ipfs, and created
        
        - address is the public evrmore address of the user
        - profile_ipfs will be set to our logo for each new account (QmU75ZCSdsm8nE5BEEqUu12t6d3MTs8t2HxmwckytsaGzX)
        - created will be the current date and time (isoformat)

        addresses: address, evr, usdc

        For the addresses table, we need to add the new deposit addresses for the user
        - address is the public evrmore address of the user
        - evr is the evrmore deposit address for the user
        - ... any other assets we support in the future

        balances: address, evr, usdc

        For the balances table, we need to add the new balances for the user
        - address is the public evrmore address of the user
        - evr is the evrmore balance for the user
        - ... any other assets we support in the future

    """

    # First things first, check if address is already in accounts
    if database_connection.execute("SELECT 1 FROM accounts WHERE address = ?", (address,)).fetchone():
        return False
        # I dont think we should raise an exception here, as the user may be trying to log in
        #raise AccountExistsException(f"Account already exists for address: {address}")

    """ account table """

    # Let us know we have a new user
    print(f"Welcome to Manticore, {address}!")

    # Set the profile ipfs to our logo for each new account
    profile_ipfs = "QmU75ZCSdsm8nE5BEEqUu12t6d3MTs8t2HxmwckytsaGzX"

    # Get the current date and time to remember this grand event!
    created = datetime.now().isoformat()

    # Let the developer know we should remember this special day
    print(f"Your birthday is {created}, we will remember it forever!")

    # Add the new account to the accounts table
    database_connection.execute("INSERT INTO accounts (address, profile_ipfs, created) VALUES (?, ?, ?)", (address, profile_ipfs, created))

    """ addresses table """

    # Create a new evrmore deposit address for the user, this is also used for all other assets on the evrmore blockchain
    evr_deposit_address = rpc.get_new_address()

    # Create the query using loop then execute full query
    query = "INSERT INTO addresses (address"
    for asset in supported_assets:
        query += f", {asset}"
    query += ") VALUES (?, "
    for _ in supported_assets:
        query += "?, "
    query = query.rstrip(", ") + ");"
    database_connection.execute(query, (address, *([evr_deposit_address] * len(supported_assets))))

    """ balances table """

    # Update the balances for the user
    query = "INSERT OR IGNORE INTO balances (address"
    for asset in supported_assets:
        query += f", {asset}"
    query += ") VALUES (?, "
    for _ in supported_assets:
        query += "0, "
    query = query.rstrip(", ") + ");"
    database_connection.execute(query, (address,))


    """ authentication table """
    # Theres really no need to initialize the authentication table, as it will be created when the user logs in
    # Initialize the authentication table with null values
    #database_connection.execute("INSERT INTO authentication (address) VALUES (?)", (address,))

    """ orders table """

    # Dont touch the orders table, it holds all orders for any account
    # Orders will be selected by the address and/or order_id

    """ Any other initializations if needed """
    # none needed at this time

    # Commit the changes to the database
    database_connection.commit()

    return True

""" Purge an account """
def purge_account(address):

    """ In order to purge an account, we need to delete all the data associated with the account 
        This includes:
        - accounts table
        - addresses table
        - balances table
        - authentication table
        - orders table
    """

    # Delete the account from the accounts table    
    database_connection.execute("DELETE FROM accounts WHERE address = ?", (address,))

    # Delete the account from the addresses table
    database_connection.execute("DELETE FROM addresses WHERE address = ?", (address,))

    # Delete the account from the balances table
    database_connection.execute("DELETE FROM balances WHERE address = ?", (address,))

    # Delete the account from the authentication table
    database_connection.execute("DELETE FROM authentication WHERE address = ?", (address,))

    # Delete the account from the orders table
    database_connection.execute("DELETE FROM orders WHERE address = ?", (address,))

    # Commit the changes to the database
    database_connection.commit()

""" Purge all accounts """
def purge_all_accounts():
    
    database_connection.execute("DELETE FROM accounts")
    database_connection.execute("DELETE FROM addresses")
    database_connection.execute("DELETE FROM balances")
    database_connection.execute("DELETE FROM authentication")
    database_connection.execute("DELETE FROM orders")
    database_connection.commit()

    print("All accounts have been purged")
    

""" Account table functions

    get_profile_ipfs: Get the profile ipfs for an account
    get_birthday: Get the birthday for an account (The date and time the account was created)

"""

def get_profile_ipfs(address):
    return database_connection.execute("SELECT profile_ipfs FROM accounts WHERE address = ?", (address,)).fetchone()[0]

def get_birthday(address):
    return database_connection.execute("SELECT created FROM accounts WHERE address = ?", (address,)).fetchone()[0]


""" Address table functions

    get_deposit_address_for_asset: Get the deposit address for an asset
"""

def get_deposit_address_for_asset(address, asset):
    return database_connection.execute(f"SELECT {asset} FROM addresses WHERE address = ?", (address,)).fetchone()[0]

""" Balances table functions

    get_balance_for_asset: Get the balance for an asset
    get_all_balances: Get all the balances for an account
"""

def get_balance_for_asset(address, asset):
    return database_connection.execute(f"SELECT {asset} FROM balances WHERE address = ?", (address,)).fetchone()[0]

def get_all_balances(address):
    balances = database_connection.execute(f"SELECT * FROM balances WHERE address = ?", (address,)).fetchall()
    columns = [description[1] for description in database_connection.execute("PRAGMA table_info(balances)").fetchall()]
    # Skip the first column (address) in the dictionary comprehension
    return {column: balance for column, balance in zip(columns[1:], balances[0][1:])}

""" Authentication table functions

    set_session_token: Set the session token for an account
    get_session_token: Get the session token for an account
    remove_session_token: Remove the session token for an account
    validate_session_token: Validate the session token for an account
    purge_session_token: Remove the session token for an account
    purge_all_session_tokens: Remove all session tokens
"""

def set_session_token(address, session_token):
    print(f"Setting session token for {address}")
    database_connection.execute("INSERT OR REPLACE INTO authentication (address, session_token, session_created) VALUES (?, ?, ?)", (address, session_token, datetime.now()))
    database_connection.commit()

def get_session_token(address):
    return database_connection.execute("SELECT session_token, session_created FROM authentication WHERE address = ?", (address,)).fetchone()

def remove_session_token(address):
    database_connection.execute("UPDATE authentication SET session_token = NULL, session_created = NULL WHERE address = ?", (address,))
    database_connection.commit()

def validate_session_token(address, session_token):
    session_data = database_connection.execute("SELECT session_token, session_created FROM authentication WHERE address = ?", (address,)).fetchone()
    if session_data and session_data[0] == session_token:
        session_created = datetime.fromisoformat(session_data[1])
        time_diff = datetime.now() - session_created
        remaining_time = timedelta(hours=12) - time_diff
        if remaining_time > timedelta(0):
            return True, remaining_time
        else:
            database_connection.execute("UPDATE authentication SET session_token = NULL, session_created = NULL WHERE address = ?", (address,))
            database_connection.commit()
            return False, None
    return False, None

def purge_session_token(address):
    database_connection.execute("DELETE FROM authentication WHERE address = ?", (address,))
    database_connection.commit()

def purge_all_session_tokens():
    database_connection.execute("DELETE FROM authentication")
    database_connection.commit()

""" Order management """

def place_order(address, type, side, market, price, quantity, fee):
    markets.create_new_order(address, type, side, market, price, quantity, fee)

def cancel_order(address, order_id):
    markets.cancel_order(address, order_id)

def get_open_orders(address):
    return markets.get_open_orders(address)

def get_cancelled_orders(address):
    return markets.get_cancelled_orders(address)

def get_account_info(address):
    cursor = database_connection.execute("SELECT * FROM accounts WHERE address = ?", (address,))
    row = cursor.fetchone()
    if row:
        return json.dumps({description[0]: value for value, description in zip(row, cursor.description)})
    else:
        return None

""" Deposit and Withdrawal functions """

def deposit_asset(address, asset, amount):
    """ While on testnet, we just add the amount to the balance """
    database_connection.execute(f"UPDATE balances SET {asset} = {asset} + ? WHERE address = ?", (amount, address))
    database_connection.commit()
    return get_balance_for_asset(address, asset)
def withdraw_asset(address, asset, amount):
    """ While on testnet, we just subtract the amount from the balance """  
    database_connection.execute(f"UPDATE balances SET {asset} = {asset} - ? WHERE address = ?", (amount, address))
    database_connection.commit()
    return get_balance_for_asset(address, asset)