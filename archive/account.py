# Do we need this?
import sqlite3

# To get the database connection and current timestamp
from dbwrapper import get_connection, current_timestamp

class Account:

    # Initialize the account with the user_id, username, and balance
    def __init__(self, user_id, username, balance):
        
        # The user id is set when registered
        # Registration will be done by posting the address and a nonced signature to the server
        self.user_id = user_id

        # The username is not neccessary and should be removed now
        self.username = username

        # Each account will need balance ledgers for all supported currencies/assets
        self.balance = balance

        self.on_hold_balance = 0.0  # Initialize on_hold_balance

    # Add any other methods needed for account management

    # Get the balance of the account
    def get_balance(self):
        conn = get_connection()
        query = "SELECT balance FROM users WHERE user_id = ?"
        result = conn.execute(query, (self.user_id,)).fetchone()
        conn.close()
        return result[0] if result else 0.0

    # Get the on-hold balance of the account
    def get_on_hold_balance(self):
        conn = get_connection()
        query = "SELECT SUM(price * quantity) FROM orders WHERE user_id = ? AND status = 'active'"
        result = conn.execute(query, (self.user_id,)).fetchone()
        conn.close()
        return result[0] if result else 0.0

    def update_balance(self, amount):
        conn = get_connection()
        query = "UPDATE users SET balance = balance + ? WHERE user_id = ?"
        conn.execute(query, (amount, self.user_id))
        conn.commit()
        conn.close()
        self.balance += amount

    def update_on_hold_balance(self, amount):
        self.on_hold_balance += amount

    def get_trade_history(self):
        conn = get_connection()
        query = "SELECT * FROM trade_history WHERE user_id = ? ORDER BY timestamp ASC"
        trades = conn.execute(query, (self.user_id,)).fetchall()
        conn.close()
        return trades

    def add_trade(self, order_id, price, quantity):
        conn = get_connection()
        query = """INSERT INTO trade_history (user_id, order_id, price, quantity, timestamp)
                   VALUES (?, ?, ?, ?, ?)"""
        conn.execute(query, (self.user_id, order_id, price, quantity, current_timestamp()))
        conn.commit()
        conn.close()
