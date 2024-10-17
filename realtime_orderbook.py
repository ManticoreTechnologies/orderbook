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

def should_cancel_order():
    return random.random() < 0.1  # 10% chance to cancel an order

async def process_message(message, order_book):
    # Example message: "Place Order: buy 5 @ 100"
    try:
        if message.startswith("Place Order:"):
            _, order_details = message.split(":", 1)
            side, qty_price = order_details.strip().split(" ", 1)
            quantity, price = map(int, qty_price.split(" @ "))
            order_id = str(uuid.uuid4())
            new_order = Order(order_id, price, quantity, side)
            await order_book.add_order(new_order)
            print(f"Order placed: {new_order}")
            return order_id
    except Exception as e:
        print(f"Failed to process message: {message}, error: {e}")
    return None

async def simulate_realtime_orderbook():
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
            if random.random() < 0.1: # Add order every 25 seconds
                new_order = generate_random_order()
                await order_book.add_order(new_order)
                print(f"New order: {new_order}")

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

if __name__ == "__main__":
    asyncio.run(simulate_realtime_orderbook())
