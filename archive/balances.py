""" Instead of storing balances in a JSON string, we will store them in a separate table 
    This will allow us to add more flexibility to the system in the future
    This will also allow us to easily query balances and update them
    Balances are going to be updated semi frequently, so we don't want to have to parse a JSON string every time we want to update a balance
    We will also be able to easily add more assets in the future
"""

# Define the supported assets
supported_assets = ["usdc", "evr", "inferna", "usdt", "usdm"]

# Import the get_connection function
from Database.accounts import get_deposit_addresses, get_deposit_txids, get_wallet, save_deposit_txid
from Database.get_connection import get_connection
from WalletX import get_usdc_balance
from archive.cbrpc import get_transaction, get_transaction_receipt
import rpc

# Define the database name
db_name = "balances"

# Get the database connection
conn = get_connection(db_name)

# Create a cursor from the connection
cursor = conn.cursor()

# Create the balances table if it doesn't exist
# Each address must be unique and have a balance for each supported asset
# When a new asset is added to the supported_assets list, the table will need to be updated with more columns
# This is a dynamic table that will grow as new assets are added
# So use ALTER TABLE to add new columns

query = '''CREATE TABLE IF NOT EXISTS balances (
    address TEXT PRIMARY KEY
'''
for asset in supported_assets:
    query += f', {asset} REAL'
query += ');'
cursor.execute(query)

# Check existing columns in the balances table at the start
existing_columns_query = "PRAGMA table_info(balances);"
cursor.execute(existing_columns_query)
existing_columns = [row[1] for row in cursor.fetchall()]

# Add new columns for any new assets
for asset in supported_assets:
    if asset not in existing_columns:
        alter_table_query = f"ALTER TABLE balances ADD COLUMN {asset} REAL DEFAULT 0;"
        cursor.execute(alter_table_query)

# Check existing columns in the balances table at the end
cursor.execute(existing_columns_query)
existing_columns = [row[1] for row in cursor.fetchall()]

# Commit the changes
conn.commit()

""" Define the helper functions below, these will be used to update the balances table """

def update_balance(address, asset, amount):
    """ Update the balance for a given address and asset """
    query = f"UPDATE balances SET {asset} = {amount} WHERE address = '{address}';"
    cursor.execute(query)
    conn.commit()

def get_balance(address, asset):
    """ Get the balance for a given address and asset """
    query = f"SELECT {asset} FROM balances WHERE address = ?;"
    cursor.execute(query, (address,))
    return cursor.fetchone()[0]

def get_all_balances(address):
    """ Get all the balances for a given address """
    query = f"SELECT * FROM balances WHERE address = '{address}';"
    cursor.execute(query)
    return cursor.fetchall()

def scan_for_deposits(address):
    """ Scan the blockchain for deposits to the given address """

    # Get the coinbase wallet to check for usdc deposits
    wallet = get_wallet(address)
   # wallet.faucet("usdc")
    

    """ Handle usdc deposits first """
    # Get all the transactions for the wallet's default address
    transactions = list(wallet.default_address.transactions())
    processed_txids = get_deposit_txids(address) # These are the txids that have already been processed

    # Iterate through the transactions and update the balances table for any new deposits
    for transaction in transactions:
        print(wallet.default_address.historical_balances("usdc"))
        tx = get_transaction_receipt(transaction.transaction_hash)
        print(tx)
        if transaction.transaction_hash not in processed_txids:
            if str(transaction.status)=="complete":
                save_deposit_txid(address, transaction.transaction_hash)

    print(get_deposit_txids(address))


scan_for_deposits("1234567890")

