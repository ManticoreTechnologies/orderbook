""" This module handles the orders database table 
    Each order will have a unique id, which is a uuid4 string
    The address is the address of the account that placed the order
    The market is the market of the order
    The side is the side of the order (buy or sell)
    The type is the type of the order (market or limit)
    The amount is the amount of the order
    The remaining_amount is the amount of the order that is still open
    The filled_amount is the amount of the order that has been filled
    The price is the price of the order
    The status is the status of the order (open, filled, cancelled)
    The created_at is the date and time the order was created
    Orders may not be updated, only cancelled, partially filled, or fully filled
"""

# Import the sqlite3 module
from datetime import datetime
import sqlite3
import uuid

from Database.get_connection import get_connection

db_name = "orders"

conn = get_connection(db_name)

# Market is in format base_quote
conn.execute('''CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    address TEXT NOT NULL,
    market TEXT NOT NULL,
    side TEXT NOT NULL,
    type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    remaining_amount INTEGER NOT NULL,
    filled_amount INTEGER NOT NULL,
    price INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);''')

conn.commit()
conn.close()


# Define all the helper functions here
# Ideally we will only need to interact with the database through these functions

def place_order(address, market, side, type, amount, price):
    conn = get_connection(db_name)
    order_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO orders (id, address, market, side, type, amount, remaining_amount, filled_amount, price, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (order_id, address, market, side, type, amount, amount, 0, price, "open", created_at)
    )
    conn.commit()
    conn.close()
    return order_id

def cancel_order(order_id):
    conn = get_connection(db_name)
    conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()


def get_order(order_id):
    conn = get_connection(db_name)
    conn.row_factory = sqlite3.Row  # Set row factory to sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return dict(order) if order else None  # Convert to dict if order is found



""" Fill an order, return the remaining amount """
def fill_order(order_id, amount):
    # Update the order to reflect the filled amount
    order = get_order(order_id)
    current_remaining_amount = order[5]
    if amount > current_remaining_amount:
        raise ValueError("Insufficient remaining amount for order")
    filled_amount = amount
    remaining_amount = current_remaining_amount - amount
    conn = get_connection(db_name)
    conn.execute("UPDATE orders SET filled_amount = ?, remaining_amount = ?, status = ? WHERE id = ?", (filled_amount, remaining_amount, "filled" if remaining_amount == 0 else "partially filled", order_id))
    conn.commit()
    conn.close()
    return remaining_amount


""" Retrieving Orders """
def get_order_by_id(order_id):
    conn = get_connection(db_name)
    conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = conn.fetchone()
    conn.close()
    return order

def get_orders_by_market(market):
    conn = get_connection(db_name)
    conn.execute("SELECT * FROM orders WHERE market = ?", (market,))
    orders = conn.fetchall()
    conn.close()
    return orders

def get_orders_by_side(side):
    conn = get_connection(db_name)
    conn.execute("SELECT * FROM orders WHERE side = ?", (side,))
    orders = conn.fetchall()
    conn.close()
    return orders

def get_orders_by_market_and_side(market, side):
    conn = get_connection(db_name)
    conn.execute("SELECT * FROM orders WHERE market = ? AND side = ?", (market, side))
    orders = conn.fetchall()
    conn.close()
    return orders

""" Cancelling orders """
def cancel_all_orders():
    conn = get_connection(db_name)
    conn.execute("UPDATE orders SET status = 'cancelled'")
    conn.commit()
    conn.close()

def cancel_all_orders_for_market(market):
    conn = get_connection(db_name)
    conn.execute("UPDATE orders SET status = 'cancelled' WHERE market = ?", (market,))
    conn.commit()
    conn.close()
