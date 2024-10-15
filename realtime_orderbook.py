import asyncio
import time
import random
import uuid
from orderbook import OrderBook, Order
from websocket_server import WebSocketServer  # Assuming you have a WebSocket server setup

def generate_random_order():
    order_type = random.choice(['buy', 'sell'])
    price = random.randint(95, 105)
    quantity = random.randint(1, 10)
    order_id = str(uuid.uuid4())
    return Order(order_id, price, quantity, order_type)

async def simulate_realtime_orderbook():
    # Initialize WebSocket server (replace with your actual WebSocket server setup)
    websocket_server = WebSocketServer(port=8765)  # Replace port with the one you need
    websocket_server.start()  # Start the server in another thread or asynchronously if needed

    # Create an instance of OrderBook with WebSocket support
    order_book = OrderBook(websocket_server=websocket_server)

    try:
        while True:
            # Generate a random order
            new_order = generate_random_order()
            print(f"New order: {new_order}")

            # Add the order to the order book
            await order_book.add_order(new_order)

            # Attempt to match orders
            order_book.match_orders()

            # Show the current state of the order book
            #order_book.show_order_book()

            # Show the price summary
            #order_book.show_price_summary()

            # Wait for a short period to simulate real-time
            time.sleep(1)

    except KeyboardInterrupt:
        print("Simulation stopped.")
        websocket_server.stop()  # Ensure you stop the WebSocket server properly

if __name__ == "__main__":
    asyncio.run(simulate_realtime_orderbook())
