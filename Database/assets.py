""" accounts.py

    For all the functions that handle the accounts data
    Accounts are identified by a public evrmore address provided by the user

"""

""" Imports"""
from Database import markets
from Database.accounts import get_account_info
from HelperX import generate_unique_id, read_config_file, create_table
from Database.get_connection import get_connection
from datetime import datetime, timedelta
import json
import rpc

""" Database name 
    This will be the database for all the assets data
    This will be used to store the comments for each asset
    Every asset will have a table, with the asset as the primary key
"""
database_name = "manticore_assets" 

""" Get the connection to the database """
database_connection = get_connection(database_name)


""" Tables in the database
    Each table has a common primary key, which is the address of the account
    To allow for scaling, we will use multiple tables instead of one big table
    We can add new tables by editing the create_tables function

    asset_comments: Stores the comments for each asset

"""

""" Create the assets table 

    address: The public evrmore address of the user
    profile_ipfs: The ipfs hash of the user's profile picture
    created: The date and time the account was created (the first time the user logged in)

    * Manticore users do not have a password, nor do they "create" an account.
    * Users simply authenticate by signing a challenge sent by the server
"""

database_connection.execute(
    '''CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAM
    );''')


database_connection.execute(
    '''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT NOT NULL,
        friend_name TEXT NOT NULL,
        address TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
    );''')


def get_asset_comments(asset_name):
    comments = database_connection.execute("SELECT * FROM comments WHERE asset_name = ?", (asset_name,)).fetchall()
    
    # Convert the result into a list of dictionaries
    comments_list = [
        {
            "id": comment[0],
            "asset_name": comment[1],
            "friend_name": comment[2],
            "address": comment[3],
            "text": comment[4],
            "created_at": comment[5],
            "updated_at": comment[6]
        }
        for comment in comments
    ]
    
    return json.dumps(comments_list)

def add_asset_comment(asset_name, address, text):
    # Get freindly name
    account = json.loads(get_account_info(address))
    print(account)
    comment = {
        "asset_name": asset_name,
        "friend_name": account["friendly_name"],
        "address": address,
        "text": text
    }
    database_connection.execute("INSERT INTO comments (asset_name, friend_name, address, text) VALUES (?, ?, ?, ?)", (asset_name, account["friendly_name"], address, text))
    database_connection.commit()


    return comment
    
def update_asset_comment(comment_id, text):
    database_connection.execute("UPDATE comments SET text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (text, comment_id))
    database_connection.commit()
    return "success"

def delete_asset_comment(comment_id):
    database_connection.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    database_connection.commit()
    return "success"

def get_townhall_comments():
    return get_asset_comments("townhall")

def add_townhall_comment(address, text):
    return add_asset_comment("townhall", address, text)

def update_townhall_comment(comment_id, text):
    update_asset_comment(comment_id, text)

def delete_townhall_comment(comment_id):
    delete_asset_comment(comment_id)


# database_connection.execute(
#     '''CREATE TABLE IF NOT EXISTS authentication (
#     '''CREATE TABLE IF NOT EXISTS authentication (
#     '''CREATE TABLE IF NOT EXISTS authentication (
#         address TEXT PRIMARY KEY,
#         session_token TEXT,
#         session_created TEXT
#     );''')

# """ Create the addresses table

#     address: The public evrmore address of the user
#     **supported assets**
#     evr: The evrmore address for the user
#     usdm: The usdm address for the user
#     ... any other assets we support in the future

#     * The supported assets are defined in the TradeX.conf file
# """

# create_table(database_connection.cursor(), "addresses", supported_assets)

# """ Create the balances table

#     address: The public evrmore address of the user
#     **supported assets**
#     evr: The evrmore balance for the user
#     usdm: The usdm balance for the user
#     ... any other assets we support in the future

#     * The balances are all in satoshis (10^-8, the smallest unit of evrmore)
# """

# create_table(database_connection.cursor(), "balances", supported_assets)

