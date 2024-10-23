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
            # Generate a random order more frequently
            if random.random() < 0.8:  # Increase the probability to add orders more frequently
                new_order = generate_random_order()
                await order_book.add_order(new_order)

            # Attempt to match orders
            await order_book.match_orders()

            # Broadcast trade history
            await order_book.broadcast_trade_history()

            # Show the current state of the order book
            await order_book.show_order_book()

            # Update OHLC data
            await order_book.update_ohlc_data()
            
            # Wait for a shorter period to simulate real-time
            time.sleep(0.5)  # Decrease the sleep time to make the simulation faster

    except KeyboardInterrupt:
        print("Simulation stopped.")
        websocket_server.stop()  # Ensure you stop the WebSocket server properly

if __name__ == "__main__":
    asyncio.run(simulate_realtime_orderbook())
