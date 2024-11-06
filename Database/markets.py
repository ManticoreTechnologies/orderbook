
""" markets.py

    For all the functions that handle the markets data

"""

""" Imports """
from datetime import datetime
from Database.get_connection import get_connection

""" Database name """
database_name = "manticore_markets"

""" Table structure 

    We will have the manticore_markets database for handling all the market data
    We will have the following tables:
    - markets : to store all the markets data, this will be the main table
        - market_id : the unique identifier for the market
        - market_name : the name of the market
        - base_asset : the base asset of the market
        - quote_asset : the quote asset of the market
        - status : the status of the market
        - created_at : the date and time the market was created
        - description : the description of the market
        - tick_size : the tick size of the market

    - a database for each market to store the bids, asks, trades, and other data

"""

""" Default markets are defined here, other markets are payed for by users 
    To create a new market, any user can pay a special order to create it
    We will have a link on the exchange to submit this special market creation order
    We collect the entire amount of the order as our fee for creating the market
    Xeggex charges $5000 per market, but this is way too high for us
    We will charge $500 per market, and offer special promotions from time to time
    Xeggex needs to implement each new market, we will have an automated system to do this
    We can do this because we are focusing solely on the Evrmore ecosystem, only supporting EVR and evrmore assets
"""

""" The default market I have chosen is INFERNA/EVR
    This can be empty, but since INFERNA is the native exchange token, it makes sense to have it
"""

default_markets = [
    {"market_name": "INFERNA/EVR", "base_currency": "INFERNA", "quote_currency": "EVR", "description": "INFERNA to EVR exchange market", "tick_size": 0.00001},
]

""" Creating the markets table
    This table will store all the markets data
    If the table does not exist, we will create it
"""
def create_market_table():
    """Create the markets table if it doesn't exist."""
    conn = get_connection(database_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS markets (
        market_id INTEGER PRIMARY KEY AUTOINCREMENT,
        market_name TEXT NOT NULL UNIQUE,
        base_currency TEXT NOT NULL,
        quote_currency TEXT NOT NULL,
        status TEXT CHECK(status IN ('active', 'inactive')) NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL,
        description TEXT,
        tick_size REAL
    );''')
    conn.commit()
    conn.close()

""" Purging the markets table 
    This is used to reset ALL the markets data
    This should only be done in emergencies or testing
    Use purge_market to delete a single market
"""
def purge_markets():
    """Delete all markets from the database."""
    conn = get_connection(database_name)
    conn.execute("DELETE FROM markets")
    conn.commit()
    conn.close()

def purge_market(market_name):
    """Delete a market from the database."""
    conn = get_connection(database_name)
    conn.execute("DELETE FROM markets WHERE market_name = ?", (market_name,))
    conn.commit()
    conn.close()

""" Adding a market to the database 

    When we add a market, we need to create a new database for it
"""
def add_market(base_asset, quote_asset, description, tick_size):

    """ Connect to the database """
    conn = get_connection(database_name)

    """ Get the cursor """
    cursor = conn.cursor()

    """ Try to select the market """
    cursor.execute("SELECT * FROM markets WHERE market_name = ?", (base_asset + '/' + quote_asset,))

    """ Fetch the result """
    existing_market = cursor.fetchone()

    """ Check if the market already exists """
    if existing_market:
        print(f"Market {base_asset}/{quote_asset} already exists")
        return False
    elif not existing_market:

        print(f"Market {base_asset}/{quote_asset} does not exist, creating it")

        """ Create the market dictionary """
        market_dict = {
            'market_name': base_asset + '/' + quote_asset,
            'base_currency': base_asset,
            'quote_currency': quote_asset,
            'created_at': datetime.now().isoformat(),
            'description': description,
            'tick_size': tick_size
        }
        
        """ Insert the market into the database """
        cursor.execute(
            """
            INSERT INTO markets 
            (market_name, base_currency, quote_currency, created_at, description, tick_size) 
            VALUES 
            (:market_name, :base_currency, :quote_currency, :created_at, :description, :tick_size)
            """, 
            market_dict
        )

        """ Commit the changes """
        conn.commit()

        return True

    """ Close the connection """
    conn.close()

""" Get all the markets from the database """
def get_all_markets():
    """Fetch all markets from the database and return them as a dictionary keyed by name."""
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets")
    rows = cursor.fetchall()
    markets = {row[1]: dict(zip([col[0] for col in cursor.description], row)) for row in rows}
    conn.close()
    return markets

""" Get the information for a single market """
def get_market_info(market_name):
    """Fetch a market from the database and return it as a dictionary."""
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets WHERE market_name = ?", (market_name,))
    row = cursor.fetchone()
    if row:
        return dict(zip([col[0] for col in cursor.description], row))
    else:
        return None

""" Create the markets table 
    This will create the markets table if it does not exist
"""
create_market_table()

""" Add the supported markets to the database 
    if they are not already there 
"""
for market in default_markets:
    market_dict = {
        'market_name': market['market_name'],
        'base_currency': market['base_currency'],
        'quote_currency': market['quote_currency'],
        'created_at': datetime.now().isoformat(),
        'description': market['description'],
        'tick_size': market['tick_size']
    }
    add_market(market_dict['base_currency'], market_dict['quote_currency'], market_dict['description'], market_dict['tick_size'])


if __name__ == "__main__":
    
    print(get_market_info('INFERNA/EVR'))
    print(get_market_info('INFERNA/EVR'))
