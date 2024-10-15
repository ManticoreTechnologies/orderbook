# Orderbook

## Overview

This project implements a real-time order book system for managing buy and sell orders. It includes components for handling orders, a WebSocket server for real-time updates, and a database for persisting order data.

## Components

### 1. Order and OrderBook

- **Order**: Represents an individual order with attributes like `order_id`, `price`, `quantity`, and `side` (buy/sell). It includes methods for comparison and representation.
  
- **OrderBook**: Manages the collection of orders, separated into bids (buy orders) and asks (sell orders). It supports adding orders, matching orders, and broadcasting updates via WebSocket.

  - **Key Methods**:
    - `add_order`: Adds a new order to the order book and saves it to the database.
    - `match_orders`: Matches buy and sell orders based on price and quantity.
    - `load_orders`: Loads active orders from the database on startup.
    - `show_order_book`: Displays the current state of the order book.
    - `show_price_summary`: Provides a summary of prices and total quantities for asks and bids.

  Relevant code:
  ```python:orderbook.py
  startLine: 6
  endLine: 125
  ```

### 2. Real-time Simulation

- **realtime_orderbook.py**: Simulates a real-time order book by generating random orders and processing them. It uses a WebSocket server to broadcast updates.

  - **Key Functions**:
    - `generate_random_order`: Creates a random order with random price and quantity.
    - `simulate_realtime_orderbook`: Continuously generates and processes orders, broadcasting updates via WebSocket.

  Relevant code:
  ```python:realtime_orderbook.py
  startLine: 8
  endLine: 49
  ```

### 3. WebSocket Server

- **WebSocketServer**: A simple WebSocket server that handles client connections and broadcasts messages to all connected clients.

  - **Key Methods**:
    - `start`: Starts the WebSocket server.
    - `stop`: Stops the WebSocket server.
    - `broadcast`: Sends a message to all connected clients.

  Relevant code:
  ```python:websocket_server.py
  startLine: 5
  endLine: 59
  ```

### 4. Database Wrapper

- **dbwrapper.py**: Handles database operations for storing and retrieving order data using SQLite.

  - **Key Functions**:
    - `save_order_to_db`: Inserts or updates an order in the database.
    - `update_order_in_db`: Updates the quantity and status of an existing order.
    - `load_orders_from_db`: Loads active orders from the database.

  Relevant code:
  ```python:dbwrapper.py
  startLine: 1
  endLine: 41
  ```

### 5. WebSocket Client

- **websocket_client.py**: A simple WebSocket client that connects to the server and listens for messages.

  - **Key Function**:
    - `listen_to_orderbook`: Connects to the WebSocket server and prints received messages.

  Relevant code:
  ```python:websocket_client.py
  startLine: 1
  endLine: 24
  ```

## Getting Started

1. **Database Setup**: Ensure SQLite is installed and the `order_book.db` is accessible. The database schema is automatically created if it doesn't exist.

2. **Running the WebSocket Server**: Start the WebSocket server using `websocket_server.py`.

3. **Simulating the Order Book**: Run `realtime_orderbook.py` to start generating and processing orders.

4. **Listening to Updates**: Use `websocket_client.py` to connect to the WebSocket server and receive real-time updates.

## Dependencies

- Python 3.x
- `asyncio`
- `websockets`
- `sqlite3`
- `tabulate`

## License

This project is licensed under the MIT License.
