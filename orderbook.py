import heapq
from tabulate import tabulate
from dbwrapper import load_orders_from_db, save_order_to_db, update_order_in_db, delete_order_from_db
import asyncio

class Order:
    def __init__(self, order_id, price, quantity, side):
        self.order_id = order_id
        self.price = price
        self.quantity = quantity
        self.side = side

    def __lt__(self, other):
        if self.side == 'sell':
            return self.price < other.price
        else:
            return self.price > other.price

    def __repr__(self):
        return f'Order({self.side}, id={self.order_id}, price={self.price}, qty={self.quantity})'

class OrderBook:
    def __init__(self, websocket_server=None):
        self.bids = []  # Max-heap for bids
        self.asks = []  # Min-heap for asks
        self.order_map = {}  # To keep track of all active orders by order_id
        self.filled_orders_log = []
        self.load_orders()  # Load active orders from the database
        self.websocket_server = websocket_server  # Assign WebSocket server instance

    async def add_order(self, order):
        if order.side == 'buy':
            heapq.heappush(self.bids, order)
        else:
            heapq.heappush(self.asks, order)

        # Save order to database
        save_order_to_db(order)

        self.order_map[order.order_id] = order
        print(f"Added {order}")

        # Broadcast the new order via WebSocket
        await self.broadcast_update(f"New order added: {order}")

    async def cancel_order(self, order_id):
        if order_id in self.order_map:
            order = self.order_map.pop(order_id)
            if order.side == 'buy':
                self.bids = [o for o in self.bids if o.order_id != order_id]
                heapq.heapify(self.bids)
            else:
                self.asks = [o for o in self.asks if o.order_id != order_id]
                heapq.heapify(self.asks)

            # Remove order from database
            delete_order_from_db(order_id)

            print(f"Cancelled {order}")
            await self.broadcast_update(f"Order cancelled: {order}")
        else:
            print(f"Order with ID {order_id} not found.")

    async def broadcast_update(self, message):
        if self.websocket_server:
            await self.websocket_server.broadcast(message)
        else:
            print("WebSocket server not initialized.")

    async def match_orders(self):
        while self.bids and self.asks and self.bids[0].price >= self.asks[0].price:
            highest_bid = heapq.heappop(self.bids)
            lowest_ask = heapq.heappop(self.asks)

            if highest_bid.quantity > lowest_ask.quantity:
                highest_bid.quantity -= lowest_ask.quantity
                self.filled_orders_log.append(f"Filled {lowest_ask} with {highest_bid}")
                heapq.heappush(self.bids, highest_bid)
                update_order_in_db(highest_bid)  # Update the remaining quantity
                await self.broadcast_update(f"Filled {lowest_ask} with {highest_bid}")
            elif highest_bid.quantity < lowest_ask.quantity:
                lowest_ask.quantity -= highest_bid.quantity
                self.filled_orders_log.append(f"Filled {highest_bid} with {lowest_ask}")
                heapq.heappush(self.asks, lowest_ask)
                update_order_in_db(lowest_ask)
                await self.broadcast_update(f"Filled {highest_bid} with {lowest_ask}")
            else:
                self.filled_orders_log.append(f"Fully filled {highest_bid} with {lowest_ask}")
                await self.broadcast_update(f"Fully filled {highest_bid} with {lowest_ask}")

            if highest_bid.quantity == 0:
                update_order_in_db(highest_bid)
            if lowest_ask.quantity == 0:
                update_order_in_db(lowest_ask)

    def load_orders(self):
        """Restore active orders from the database on startup."""
        orders = load_orders_from_db()
        for order_id, price, quantity, side in orders:
            order = Order(order_id=order_id, price=price, quantity=quantity, side=side)
            if side == 'buy':
                heapq.heappush(self.bids, order)
            else:
                heapq.heappush(self.asks, order)
            self.order_map[order_id] = order
        print(f"Restored {len(orders)} orders from the database.")
        #await self.broadcast_update(f"Restored {len(orders)} orders from the database.")

    async def show_order_book(self):
        asks_table = [[ask.order_id, ask.price, ask.quantity] for ask in sorted(self.asks, key=lambda o: o.price)]
        bids_table = [[bid.order_id, bid.price, bid.quantity] for bid in sorted(self.bids, key=lambda o: -o.price)]

        asks_output = tabulate(asks_table, headers=["Order ID", "Price", "Quantity"], tablefmt="grid")
        bids_output = tabulate(bids_table, headers=["Order ID", "Price", "Quantity"], tablefmt="grid")

        print("Current Asks:")
        print(asks_output)
        print("Current Bids:")
        print(bids_output)

        await self.broadcast_update(f"Current Asks:\n{asks_output}")
        await self.broadcast_update(f"Current Bids:\n{bids_output}")

        print("\nFilled Orders Log:")
        for log in self.filled_orders_log:
            print(log)
            await self.broadcast_update(log)

    async def show_price_summary(self):
        ask_summary = {}
        bid_summary = {}

        for ask in self.asks:
            if ask.price in ask_summary:
                ask_summary[ask.price] += ask.quantity
            else:
                ask_summary[ask.price] = ask.quantity

        for bid in self.bids:
            if bid.price in bid_summary:
                bid_summary[bid.price] += bid.quantity
            else:
                bid_summary[bid.price] = bid.quantity

        ask_rows = [[price, total_quantity] for price, total_quantity in sorted(ask_summary.items(), reverse=True)]
        bid_rows = [[price, total_quantity] for price, total_quantity in sorted(bid_summary.items(), reverse=True)]

        ask_summary_output = tabulate(ask_rows, headers=["Price", "Total Quantity"], tablefmt="grid")
        bid_summary_output = tabulate(bid_rows, headers=["Price", "Total Quantity"], tablefmt="grid")

        print("\nORDER BOOK SUMMARY")
        print("Asks (Sell Orders):")
        print(ask_summary_output)
        print("\nBids (Buy Orders):")
        print(bid_summary_output)

        await self.broadcast_update(f"\nORDER BOOK SUMMARY\nAsks (Sell Orders):\n{ask_summary_output}")
        await self.broadcast_update(f"\nBids (Buy Orders):\n{bid_summary_output}")