import sqlite3
from datetime import datetime
import json

def get_connection():
    """Create a new database connection."""
    return sqlite3.connect('order_book.db')

# Create table if not exists
conn = get_connection()
conn.execute('''CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    side TEXT CHECK(side IN ('buy', 'sell')) NOT NULL,
    status TEXT CHECK(status IN ('active', 'partially_filled', 'filled', 'cancelled')) NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);''')
conn.commit()
conn.close()

# Create tickers table if not exists
conn = get_connection()
conn.execute('''CREATE TABLE IF NOT EXISTS tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL
);''')
conn.commit()
conn.close()

# Add user accounts table
conn = get_connection()
conn.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    balance REAL NOT NULL
);''')
conn.commit()
conn.close()

# Add trade history table
conn = get_connection()
conn.execute('''CREATE TABLE IF NOT EXISTS trade_history (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    side TEXT CHECK(side IN ('buy', 'sell')) NOT NULL,
    taker BOOLEAN NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);''')
conn.commit()
conn.close()

def create_ohlc_table():
    conn = get_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS ohlc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resolution TEXT NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume INTEGER NOT NULL,
        timestamp TEXT NOT NULL
    );''')
    conn.commit()
    conn.close()

# Call this function to create the new table
create_ohlc_table()

def current_timestamp():
    return datetime.now().isoformat()

def save_order_to_db(order):
    """Insert a new order into the database or update it if it already exists."""
    conn = get_connection()
    query = """INSERT OR REPLACE INTO orders (order_id, user_id, price, quantity, side, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    values = (order.order_id, order.user_id, order.price, order.quantity, order.side, 'active', current_timestamp(), current_timestamp())
    conn.execute(query, values)
    conn.commit()
    conn.close()

def update_order_in_db(order):
    """Update an existing order's quantity and status."""
    conn = get_connection()
    query = """UPDATE orders SET quantity = ?, status = ?, updated_at = ? WHERE order_id = ?"""
    values = (order.quantity, 'partially_filled' if order.quantity > 0 else 'filled', current_timestamp(), order.order_id)
    conn.execute(query, values)
    conn.commit()
    conn.close()

def load_orders_from_db():
    """Load active orders from the database."""
    conn = get_connection()
    query = "SELECT order_id, user_id, price, quantity, side FROM orders WHERE status = 'active'"
    orders = conn.execute(query).fetchall()
    conn.close()
    return orders

def delete_order_from_db(order_id):
    """Delete an order from the database by order_id."""
    conn = get_connection()
    query = "DELETE FROM orders WHERE order_id = ?"
    conn.execute(query, (order_id,))
    conn.commit()
    conn.close()

def save_ticker_to_db(ticker_data):
    """Save ticker information to the database."""
    conn = get_connection()
    query = """INSERT INTO tickers (timestamp, price, quantity) VALUES (?, ?, ?)"""
    values = (current_timestamp(), ticker_data['price'], ticker_data['quantity'])
    conn.execute(query, values)
    conn.commit()
    conn.close()

def save_account_to_db(account):
    """Insert or update an account in the database."""
    conn = get_connection()
    query = """INSERT OR REPLACE INTO users (user_id, username, balance)
               VALUES (?, ?, ?)"""
    values = (account.user_id, account.username, account.balance)
    conn.execute(query, values)
    conn.commit()
    conn.close()

def load_accounts_from_db():
    """Load all accounts from the database."""
    conn = get_connection()
    query = "SELECT user_id, username, balance FROM users"
    accounts = conn.execute(query).fetchall()
    conn.close()
    return accounts

def load_account_from_db(user_id):
    """Load a single account from the database by user_id."""
    conn = get_connection()
    query = "SELECT user_id, username, balance FROM users WHERE user_id = ?"
    account = conn.execute(query, (user_id,)).fetchone()
    conn.close()
    return account

def register_account(user_id, username, password, balance):
    """Register a new account in the database."""
    conn = get_connection()
    query = """INSERT INTO users (user_id, username, password, balance)
               VALUES (?, ?, ?, ?)"""
    try:
        conn.execute(query, (user_id, username, password, balance))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Account with user_id {user_id} already exists.")
    finally:
        conn.close()

def save_ohlc_to_db(ohlc_data):
    """Save OHLC data to the database as a JSON string."""
    conn = get_connection()
    query = "SELECT ohlc_data FROM ohlc WHERE resolution = ? ORDER BY timestamp DESC LIMIT 1"
    result = conn.execute(query, (ohlc_data['resolution'],)).fetchone()

    if result:
        # Load existing OHLC data list
        ohlc_list = json.loads(result[0])
    else:
        # Start a new list if no data exists
        ohlc_list = []

    # Append the new OHLC data
    ohlc_list.append({
        'open': ohlc_data['open'],
        'high': ohlc_data['high'],
        'low': ohlc_data['low'],
        'close': ohlc_data['close'],
        'volume': ohlc_data['volume'],
        'timestamp': ohlc_data['timestamp']
    })

    # Serialize the updated OHLC list to a JSON string
    ohlc_json = json.dumps(ohlc_list)

    # Update the database with the new OHLC list
    query = """INSERT OR REPLACE INTO ohlc (resolution, ohlc_data, timestamp)
               VALUES (?, ?, ?)"""
    values = (ohlc_data['resolution'], ohlc_json, ohlc_data['timestamp'])
    conn.execute(query, values)
    conn.commit()
    conn.close()
