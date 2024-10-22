import asyncio
import time
import random
import uuid
import json
from dbwrapper import register_account
from orderbook import OrderBook, Order
from websocket_server import WebSocketServer  # Assuming you have a WebSocket server setup

def generate_random_order():
    order_type = random.choice(['buy', 'sell'])
    price = random.randint(95, 105)
    quantity = random.randint(1, 10)
    order_id = str(uuid.uuid4())
    user_id = random.choice(['user1', 'user2'])  # Example user IDs
    return Order(order_id, price, quantity, order_type, user_id)

def should_cancel_order():
    return random.random() < 0.1  # 10% chance to cancel an order

async def process_message(message, order_book):
    try:
        print(f"Received message: {message}")  # Log received message

        if message.startswith("Register Account:"):
            _, account_details = message.split(":", 1)
            user_id, username, password = account_details.strip().split(",")
            register_account(user_id, username, password)
            return f"Account registered for user_id: {user_id}"
        
        if message == "get_latest_ticker":
            return "Latest Ticker: " + order_book.get_latest_ticker()
        
        if message == "get_tickers":
            tickers = order_book.get_ticker_history()
            return "Tickers: " + json.dumps([{
                "timestamp": ticker[0],
                "price": ticker[1],
                "quantity": ticker[2]
            } for ticker in tickers])
        
        if message.startswith("Place Order:"):
            _, order_details = message.split(":", 1)
            try:
                parts = order_details.strip().split(" ", 2)
                if len(parts) != 3:
                    raise ValueError("Order details do not have the expected number of parts.")
                
                side, qty_price_user = parts[0], parts[1] + " " + parts[2]
                quantity, price_user = qty_price_user.split(" @ ")
                price, user_id = price_user.split(" by ")
                
                quantity = int(quantity)
                price = int(price)
                
            except ValueError as e:
                print(f"Error parsing order details: {order_details}, error: {e}")
                return "Invalid order format. Please use 'Place Order: <side> <quantity> @ <price> by <user_id>'."

            order_id = str(uuid.uuid4())
            new_order = Order(order_id, price, quantity, side, user_id)
            await order_book.add_order(new_order)
            print(f"Order placed: {new_order}")
            
            return f"Order ID: {order_id}"

        if message.startswith("Cancel Order:"):
            print("Received cancel order message")
            _, order_id = message.split(":", 1)
            await order_book.cancel_order(order_id)
            print(f"Order cancelled: {order_id}")
            return f"Cancelled Order ID: {order_id}"

        if message.startswith("Get Trade History:"):
            _, user_id = message.split(":", 1)
            trades = order_book.get_trade_history(user_id)
            return "Trade History: " + json.dumps(trades)

    except Exception as e:
        print(f"Failed to process message: {message}, error: {e}")
    return None

async def simulate_realtime_orderbook():
    # Register users for the simulation
    register_simulation_users()

    # Initialize WebSocket server with a message callback
    websocket_server = WebSocketServer(
        port=8765,
        message_callback=lambda message: process_message(message, order_book)
    )
    websocket_server.start()

    # Create an instance of OrderBook with WebSocket support
    order_book = OrderBook(websocket_server=websocket_server)

    try:
        while True:
            # Generate a random order

            # Add the order to the order book
            if random.random() < 0.5: # Add order every 25 seconds
                new_order = generate_random_order()
                await order_book.add_order(new_order)

            # Randomly cancel an order
            #if should_cancel_order() and order_book.order_map:
            #    order_id_to_cancel = random.choice(list(order_book.order_map.keys()))
            #    await order_book.cancel_order(order_id_to_cancel)

            # Attempt to match orders
            await order_book.match_orders()

            # Show the current state of the order book
            await order_book.show_order_book()

            # Show the price summary
            #order_book.show_price_summary()

            # Wait for a short period to simulate real-time
            time.sleep(1)

    except KeyboardInterrupt:
        print("Simulation stopped.")
        websocket_server.stop()  # Ensure you stop the WebSocket server properly

def register_simulation_users():
    users = [
        {"user_id": "user1", "username": "User One", "password": "password1", "balance": 1000000.0},
        {"user_id": "user2", "username": "User Two", "password": "password2", "balance": 1000000.0},
        {"user_id": "user3", "username": "User Three", "password": "password3", "balance": 1000000.0}
    ]
    for user in users:
        register_account(user["user_id"], user["username"], user["password"], user["balance"])
        print(f"Registered user: {user['user_id']} with balance: {user['balance']}")

if __name__ == "__main__":
    asyncio.run(simulate_realtime_orderbook())
