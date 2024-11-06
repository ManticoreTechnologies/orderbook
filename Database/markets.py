import sqlite3
from datetime import datetime

def get_connection(db_name):
    """Create a new database connection."""
    return sqlite3.connect(f'{db_name}.db')

def create_market_table():
    """Create the markets table if it doesn't exist."""
    conn = get_connection('markets')
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

def add_market(market_dict):
    """Add a market to the database if it doesn't already exist."""
    conn = get_connection('markets')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets WHERE market_name = ?", (market_dict['market_name'],))
    existing_market = cursor.fetchone()
    if not existing_market:
        cursor.execute("INSERT INTO markets (market_name, base_currency, quote_currency, created_at, description, tick_size) VALUES (:market_name, :base_currency, :quote_currency, :created_at, :description, :tick_size)", market_dict)
        conn.commit()
    conn.close()

def get_all_markets():
    """Fetch all markets from the database and return them as a dictionary keyed by name."""
    conn = get_connection('markets')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets")
    rows = cursor.fetchall()
    markets = {row[1]: dict(zip([col[0] for col in cursor.description], row)) for row in rows}
    conn.close()
    return markets

def get_market_info(market_name):
    """Fetch a market from the database and return it as a dictionary."""
    conn = get_connection('markets')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets WHERE market_name = ?", (market_name,))
    row = cursor.fetchone()
    if row:
        return dict(zip([col[0] for col in cursor.description], row))
    else:
        return None


# Initialize the database connection and create the markets table
create_market_table()
""" Below are the supported markets """
supported_markets = [
    {"market_name": "EVR_USDC", "base_currency": "EVR", "quote_currency": "USDC", "description": "EVR to USDC exchange market", "tick_size": 0.0001},
    {"market_name": "INFERNA_EVR", "base_currency": "INFERNA", "quote_currency": "EVR", "description": "INFERNA to EVR exchange market", "tick_size": 0.00001},
]
""" Add the supported markets to the database if they are not already there """
for market in supported_markets:
    market_dict = {
        'market_name': market['market_name'],
        'base_currency': market['base_currency'],
        'quote_currency': market['quote_currency'],
        'created_at': datetime.now().isoformat(),
        'description': market['description'],
        'tick_size': market['tick_size']
    }
    add_market(market_dict)

