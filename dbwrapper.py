import sqlite3
from datetime import datetime

def get_connection():
    """Create a new database connection."""
    return sqlite3.connect('order_book.db')

# Create table if not exists
conn = get_connection()
conn.execute('''CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    side TEXT CHECK(side IN ('buy', 'sell')) NOT NULL,
    status TEXT CHECK(status IN ('active', 'partially_filled', 'filled', 'cancelled')) NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);''')
conn.commit()
conn.close()

def current_timestamp():
    return datetime.now().isoformat()

def save_order_to_db(order):
    """Insert a new order into the database or update it if it already exists."""
    conn = get_connection()
    query = """INSERT OR REPLACE INTO orders (order_id, price, quantity, side, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)"""
    values = (order.order_id, order.price, order.quantity, order.side, 'active', current_timestamp(), current_timestamp())
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
    query = "SELECT order_id, price, quantity, side FROM orders WHERE status = 'active'"
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
