import asyncio
import time
import random
from websocket_server import WebSocketServer
from orderbook import OrderBook
from order_utils import generate_random_order
from message_handler import process_message
from user_utils import register_simulation_users
# TODO: Add RPC script for calling verifymessage
# TODO: Add authentication to websocket for users, use a nonced signed message
# TODO: Add a held balance to the accounts
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
            if random.random() < 0.5:  # Add order every 25 seconds
                new_order = generate_random_order()
                await order_book.add_order(new_order)

            # Attempt to match orders
            await order_book.match_orders()

            # broadcast trade history
            await order_book.broadcast_trade_history()

            # Show the current state of the order book
            await order_book.show_order_book()

            # Wait for a short period to simulate real-time
            time.sleep(1)

    except KeyboardInterrupt:
        print("Simulation stopped.")
        websocket_server.stop()  # Ensure you stop the WebSocket server properly

if __name__ == "__main__":
    asyncio.run(simulate_realtime_orderbook())
