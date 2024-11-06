"""

    accounts.py

    For all the functions that handle the accounts data
    Accounts are identified by a public evrmore address provided by the user

"""

# We will save all the accounts data into this database
database_name = "manticore_accounts" 

# Import the get_connection function
from datetime import datetime, timedelta
from Database.get_connection import get_connection
import rpc

# Get the connection to the database
database_connection = get_connection(database_name)

# Read the supported assets from the config file
from HelperX import generate_unique_id, read_config_file, create_table
import json
config = read_config_file('TradeX.conf')
supported_assets = json.loads(config["Accounts"]["supported_assets"])

class AccountExistsException(Exception):
    """ Exception raised for errors in the input salary. """
    pass

""" 
    Tables in the database
    Each table has a common primary key, which is the address of the account
    To allow for scaling, we will use multiple tables instead of one big table
    We can add new tables by editing the create_tables function

    accounts: Stores basic account information (address, profile_ipfs, created)
    authentication: Stores the authentication data (address, session token, challenge, etc)
    addresses: Stores the deposit addresses for an account (usdc, evr, etc)
    balances: Stores the balances for an account (usdc, evr, etc)
    orders: Stores all the orders for an account (open, filled, cancelled)

"""


""" 
    Create the accounts table 

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

"""
    Create the authentication table

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

"""
    Create the addresses table

    address: The public evrmore address of the user
    **supported assets**
    evr: The evrmore address for the user
    usdm: The usdm address for the user
    ... any other assets we support in the future

    * The supported assets are defined in the TradeX.conf file
"""

create_table(database_connection.cursor(), "addresses", supported_assets)


"""
    Create the balances table

    address: The public evrmore address of the user
    **supported assets**
    evr: The evrmore balance for the user
    usdm: The usdm balance for the user
    ... any other assets we support in the future

    * The balances are all in satoshis (10^-8, the smallest unit of evrmore)
"""
create_table(database_connection.cursor(), "balances", supported_assets)


""" 
    Create the orders table

    address: The public evrmore address of the user
    order_id: The id of the order (unique identifier)
    order_type: The type of the order (market or limit)
    order_status: The status of the order (open, filled, cancelled)
    order_created: The date and time the order was created
    order_filled: The date and time the order was filled
    order_price: The price of the order (in satoshis)
    order_quantity: The quantity of the order (in satoshis)
    order_market: The market of the order (e.g. evr/usdm)
    order_side: The side of the order (bid or ask)
    order_fee: The fee of the order (in satoshis)
    
"""

database_connection.execute(
    '''CREATE TABLE IF NOT EXISTS orders (
        address TEXT,
        order_id TEXT,
        order_type TEXT,
        order_status TEXT,
        order_created TEXT,
        order_filled TEXT,
        order_price REAL,
        order_quantity REAL,
        order_market TEXT,
        order_side TEXT,
        order_fee REAL,
        PRIMARY KEY (address, order_id)
    );''')


# Commit the changes to the database
database_connection.commit()



""" 
    Creating and purging accounts
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
        raise AccountExistsException(f"Account already exists for address: {address}")

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

    # Initialize the authentication table with null values
    database_connection.execute("INSERT INTO authentication (address) VALUES (?)", (address,))

    """ orders table """

    # Dont touch the orders table, it holds all orders for any account
    # Orders will be selected by the address and/or order_id

    """ Any other initializations if needed """
    # none needed at this time

    # Commit the changes to the database
    database_connection.commit()

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


def purge_all_accounts():
    
    database_connection.execute("DELETE FROM accounts")
    database_connection.execute("DELETE FROM addresses")
    database_connection.execute("DELETE FROM balances")
    database_connection.execute("DELETE FROM authentication")
    database_connection.execute("DELETE FROM orders")
    database_connection.commit()

    print("All accounts have been purged")
    

""" 
    Account table functions

    get_profile_ipfs: Get the profile ipfs for an account
    get_birthday: Get the birthday for an account (The date and time the account was created)

"""

def get_profile_ipfs(address):
    return database_connection.execute("SELECT profile_ipfs FROM accounts WHERE address = ?", (address,)).fetchone()[0]

def get_birthday(address):
    return database_connection.execute("SELECT created FROM accounts WHERE address = ?", (address,)).fetchone()[0]


""" 
    Address table functions

    get_deposit_address_for_asset: Get the deposit address for an asset
"""

def get_deposit_address_for_asset(address, asset):
    return database_connection.execute(f"SELECT {asset} FROM addresses WHERE address = ?", (address,)).fetchone()[0]

""" 
    Balances table functions

    get_balance_for_asset: Get the balance for an asset
"""

def get_balance_for_asset(address, asset):
    return database_connection.execute(f"SELECT {asset} FROM balances WHERE address = ?", (address,)).fetchone()[0]

""" 
    Orders table functions

    add_order: Add an order to the orders table
    get_order_by_id: Get an order by its id
    get_all_orders: Get all orders for an account
    get_all_orders_for_market: Get all orders for a market
    get_all_open_orders: Get all open orders for an account
    get_all_cancelled_orders: Get all cancelled orders for an account
    get_all_filled_orders: Get all filled orders for an account
    cancel_order: Cancel an order, set the status to cancelled
    cancel_all_orders: Cancel all orders for an account, set the status to cancelled
    purge_order: Purge an order, delete it from the orders table
    purge_orders: Purge all orders for an account, delete them from the orders table
    purge_all_orders: Purge all orders from the orders table
    
"""

def add_order(address, type, side, market, price, quantity, fee):

    """ 
        We currently dont support market orders, only limit orders
    """

    # Check if the order type is valid
    if type not in ["limit"]:
        raise ValueError(f"Invalid order type: {type}")

    # Create unique order id
    order_id = generate_unique_id()

    # Get the current date and time
    created = datetime.now().isoformat()

    # Add the order to the orders table
    database_connection.execute(
        """
        INSERT INTO orders 
        (address, order_id, order_type, order_status, order_created, order_filled, order_price, order_quantity, order_market, order_side, order_fee) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            address, 
            order_id, 
            type, 
            "open", 
            created, 
            None, 
            price, 
            quantity, 
            market, 
            side, 
            fee
        )
    )


    # Commit the changes to the database
    database_connection.commit()

    # Return the order id to the caller
    return order_id

def get_order_by_id(address, order_id):
    return database_connection.execute("SELECT * FROM orders WHERE address = ? AND order_id = ?", (address, order_id)).fetchone()

def get_all_orders(address):
    return database_connection.execute("SELECT * FROM orders WHERE address = ?", (address,)).fetchall()

def get_all_orders_for_market(address, market):
    return database_connection.execute("SELECT * FROM orders WHERE address = ? AND order_market = ?", (address, market)).fetchall()

def get_all_open_orders(address):
    return database_connection.execute("SELECT * FROM orders WHERE address = ? AND order_status = 'open'", (address,)).fetchall()

def get_all_cancelled_orders(address):
    return database_connection.execute("SELECT * FROM orders WHERE address = ? AND order_status = 'cancelled'", (address,)).fetchall()

def get_all_filled_orders(address):
    return database_connection.execute("SELECT * FROM orders WHERE address = ? AND order_status = 'filled'", (address,)).fetchall()

def cancel_order(address, order_id):
    try:
        # First, check if the order_id belongs to this address
        existing_order = database_connection.execute("SELECT 1 FROM orders WHERE address = ? AND order_id = ?", (address, order_id)).fetchone()
        if existing_order:
            database_connection.execute("UPDATE orders SET order_status = 'cancelled' WHERE address = ? AND order_id = ?", (address, order_id))
            database_connection.commit()
        else:
            print(f"Order {order_id} does not belong to {address}")
            return False
    except Exception as e:
        print(f"Error cancelling order {order_id} for {address}: {e}")
        return False
    return True

def cancel_all_orders(address):
    try:
        database_connection.execute("UPDATE orders SET order_status = 'cancelled' WHERE address = ?", (address,))
        database_connection.commit()
    except Exception as e:
        print(f"Error cancelling all orders for {address}: {e}")
        return False
    return True

def purge_order(address, order_id):
    try:
        # First, check if the order_id belongs to this address
        existing_order = database_connection.execute("SELECT 1 FROM orders WHERE address = ? AND order_id = ?", (address, order_id)).fetchone()
        if existing_order:
            database_connection.execute("DELETE FROM orders WHERE address = ? AND order_id = ?", (address, order_id))
            database_connection.commit()
        else:
            print(f"Order {order_id} does not belong to {address}")
            return False
    except Exception as e:
        print(f"Error purging order {order_id} for {address}: {e}")
        return False
    return True

def purge_orders(address):
    try:
        database_connection.execute("DELETE FROM orders WHERE address = ?", (address,))
        database_connection.commit()
    except Exception as e:
        print(f"Error purging orders for {address}: {e}")
        return False
    return True

def purge_all_orders():
    try:
        database_connection.execute("DELETE FROM orders")
        database_connection.commit()
    except Exception as e:
        print(f"Error purging all orders: {e}")
        return False
    return True

""" 
    Authentication table functions

    set_session_token: Set the session token for an account
    get_session_token: Get the session token for an account
    remove_session_token: Remove the session token for an account
"""

def set_session_token(address, session_token):
    print(f"Setting session token for {address}")
    database_connection.execute("INSERT INTO authentication (address, session_token, session_created) VALUES (?, ?, ?)", (address, session_token, datetime.now()))
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



""" Test the functions """
if __name__ == "__main__":
    # Test the purge account function
    try:

        # Try to initialize the account for this random address
        init_account("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz")

    # If the account already exists, try printing the profile ipfs
    except AccountExistsException:
        # Test all the functions
        #print(get_profile_ipfs("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz"))
        #print(get_birthday("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz"))
        #print(get_deposit_address_for_asset("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz", "evr"))
        #print(get_balance_for_asset("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz", "evr"))
        #print(add_order("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz", "limit", "bid", "evr/usdm", 10000, 1, 0.1))
        #print(cancel_order("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz", "30831f2c-9e6e-48b1-bcb6-a8029398b236"))
        #print(purge_order("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz", "30831f2c-9e6e-48b1-bcb6-a8029398b236"))
        #print(purge_orders("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz"))
        #print(purge_all_orders())
        # Test the session token functions  
        #set_session_token("EVZWQcGh9q9UPmT7t7UfeZs8TsWd3VJmFh", "1234567890")
        #print(get_session_token("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz"))
        #remove_session_token("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz")
        #print(validate_session_token("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz", "1234567890"))
        # Then purge the account
        #purge_account("evr1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsz")
        purge_all_accounts()
        pass