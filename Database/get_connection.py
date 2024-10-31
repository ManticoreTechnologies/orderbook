import sqlite3


def get_connection(db_name):
    """Create a new database connection."""
    return sqlite3.connect(f'{db_name}.db')