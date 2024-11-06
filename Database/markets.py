
""" markets.py

    For all the functions that handle the markets data

"""

""" Imports """
from Database.get_connection import get_connection
from HelperX import generate_unique_id
from datetime import datetime

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

    - orders: to store all the orders data for any market
        - address: the public evrmore address of the user
        - order_id: the id of the order (unique identifier)
        - order_type: the type of the order (market or limit)
        - order_status: the status of the order (open, filled, cancelled)
        - order_created: the date and time the order was created
        - order_filled: the date and time the order was filled
        - order_price: the price of the order (in satoshis)
        - order_quantity: the quantity of the order (in satoshis)
        - order_market: the market of the order (e.g. evr/usdm)
        - order_side: the side of the order (bid or ask)
        - order_fee: the fee of the order (in satoshis)

"""

""" Market table """
def create_market_table():
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

def purge_market_table():
    """ Purge the markets table 
        This will delete all the markets from the markets table
        Esentially nuking the entire exchange of markets
    """
    conn = get_connection(database_name)
    conn.execute("DELETE FROM markets")
    conn.commit()
    conn.close()

""" Order table """
def create_order_table():
    conn = get_connection(database_name)
    conn.execute(
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
    conn.execute('CREATE INDEX IF NOT EXISTS idx_order_created ON orders (order_created);')
    conn.commit()
    conn.close()

def purge_order_table():
    """ Purge the orders table 
        This will delete all the orders from the orders table
        Esentially nuking the entire exchange of orders
    """
    conn = get_connection(database_name)
    conn.execute("DELETE FROM orders")
    conn.commit()
    conn.close()

""" Managing markets 

    This will create a new market if it does not exist
    Otherwise it will return False

    Whenever a user pays to list a new market, they must provide the base and quote asset
    They must also provide a description and tick size
"""
def create_new_market(base_asset, quote_asset, description, tick_size):
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

def purge_market(market_name):
    """ Purge a single market from the markets table """
    conn = get_connection(database_name)
    conn.execute("DELETE FROM markets WHERE market_name = ?", (market_name,))
    conn.commit()
    conn.close()

def purge_markets():
    """ Purge all the markets from the markets table 
        Also purges the orders table, this nukes the entire exchange of markets and orders
        Resetting it to a clean state
    """
    purge_market_table()
    purge_order_table()

""" Managing orders

    Users can create new orders and cancel them, but they cannot be deleted
    This allows us to keep track of all the orders for a user
    
    The accounts.py file contains functions for managing orders that use these functions
    this way all the order management is in one place and we can keep things consistent

    create_new_order: Add an order to the orders table
    cancel_order: Cancel an order, set the status to cancelled
    purge_order: Purge an order, delete it from the orders table
    purge_orders: Purge all orders for an account, delete them from the orders table
    purge_all_orders: Purge all orders from the orders table
"""

def create_new_order(address, type, side, market, price, quantity, fee):
    """ This method allows a user to create a new order 
        We currently dont support market orders, only limit orders
    """

    """ Check if the order type is valid """
    if type not in ["limit"]:
        raise ValueError(f"Invalid order type: {type}")
    
    """ Create a unique order id """
    order_id = generate_unique_id()

    """ Get the current date and time """
    created = datetime.now().isoformat()

    """ Open a database connection """
    conn = get_connection(database_name)

    """ Insert the order into the database """
    conn.execute(
        """
        INSERT INTO orders 
        (address, order_id, order_type, order_status, order_created, order_filled, order_price, order_quantity, order_market, order_side, order_fee) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (address, order_id, type, "open", created, None, price, quantity, market, side, fee)
    )

    """ Commit the changes """
    conn.commit()

    """ Close the connection """
    conn.close()

def cancel_order(address, order_id):
    """ Allows a user to cancel an order for their account """
    
    """ Open a database connection """
    conn = get_connection(database_name)

    """ Check if the order belongs to the address """
    existing_order = conn.execute("SELECT 1 FROM orders WHERE address = ? AND order_id = ?", (address, order_id)).fetchone()
    
    """ If the order does not exist then it doesn't belong to the address, return False """
    if not existing_order:
        print(f"Order {order_id} does not belong to {address}")
        return False
    
    """ Otherwise, update the order status to cancelled """
    try:
        conn.execute("UPDATE orders SET order_status = 'cancelled' WHERE address = ? AND order_id = ?", (address, order_id))
        conn.commit()
    except Exception as e:
        print(f"Error cancelling order {order_id} for {address}: {e}")
        return False
    return True

def cancel_all_orders(address):
    """ Cancel all orders for an address """
    conn = get_connection(database_name)
    conn.execute("UPDATE orders SET order_status = 'cancelled' WHERE address = ?", (address,))
    conn.commit()
    conn.close()

def cancel_all_bids(address):
    """ Cancel all bids for an address """
    conn = get_connection(database_name)
    conn.execute("UPDATE orders SET order_status = 'cancelled' WHERE address = ? AND order_side = 'bid'", (address,))
    conn.commit()
    conn.close()

def cancel_all_asks(address):
    """ Cancel all asks for an address """
    conn = get_connection(database_name)
    conn.execute("UPDATE orders SET order_status = 'cancelled' WHERE address = ? AND order_side = 'ask'", (address,))
    conn.commit()
    conn.close()

def purge_order(address, order_id):
    """ Purge an order from the orders table """
    conn = get_connection(database_name)
    conn.execute("DELETE FROM orders WHERE address = ? AND order_id = ?", (address, order_id))
    conn.commit()
    conn.close()

def purge_orders(address):
    """ Purge all orders for an address from the orders table """
    conn = get_connection(database_name)
    conn.execute("DELETE FROM orders WHERE address = ?", (address,))
    conn.commit()
    conn.close()

def purge_all_orders():
    """ Purge all orders from the orders table """
    purge_order_table()

""" Retrieving market data """

def list_all_markets():
    """ List all the markets in the markets table """
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets")
    rows = cursor.fetchall()
    markets = {row[1]: dict(zip([col[0] for col in cursor.description], row)) for row in rows}
    conn.close()
    return markets

def get_market_info(market_name):
    """ Get the information for a single market """
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets WHERE market_name = ?", (market_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(zip([col[0] for col in cursor.description], row))

def get_market_status(market_name):
    """ Get the status of a single market """
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM markets WHERE market_name = ?", (market_name,))
    status = cursor.fetchone()
    conn.close()
    return status[0]

def get_market_orders(market_name):
    """ Get all the orders for a single market """
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_market = ?", (market_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_open_orders(market_name):
    """ Get all the open orders for a single market """
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_market = ? AND order_status = 'open'", (market_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_open_bids(market_name):
    """ Get all the open bids for a single market 
        This should return a sorted list of bids by creation date, the oldest first
        This is useful for matching bids to asks, in a FIFO manner
    """
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_market = ? AND order_status = 'open' AND order_side = 'bid' ORDER BY order_created", (market_name,))
    rows = cursor.fetchall()
    bids = [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    conn.close()
    return bids

def get_open_asks(market_name):
    """ Get all the open asks for a single market """
    conn = get_connection(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_market = ? AND order_status = 'open' AND order_side = 'ask'", (market_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows

""" Create the required tables

    -markets
    -orders

"""
create_market_table()
create_order_table()


""" Setup new markets here, run this file to add new markets to the database """
if __name__ == "__main__":


    print(list_all_markets())

    def add_new_market():
        markets_to_add = [
            {"market_name": "INFERNA/EVR", "base_currency": "INFERNA", "quote_currency": "EVR", "description": "INFERNA to EVR exchange market", "tick_size": 0.00001},
        ]
        for market in markets_to_add:
            create_new_market(market['base_currency'], market['quote_currency'], market['description'], market['tick_size'])

    add_new_market()

    print(get_market_status('INFERNA/EVR'))

    #create_new_order('0x0000000000000000000000000000000000000000', 'limit', 'bid', 'INFERNA/EVR', 1, 1, 0)
    purge_all_orders()
    print(get_open_bids('INFERNA/EVR'))