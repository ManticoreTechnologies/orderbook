import heapq
from tabulate import tabulate
from dbwrapper import load_orders_from_db, save_order_to_db, update_order_in_db
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
        await self.broadcast_order(order)

    async def broadcast_order(self, order):
        if self.websocket_server:
            message = f"New order added: {order}"
            await self.websocket_server.broadcast(message)
        else:
            print("WebSocket server not initialized.")

    def match_orders(self):
        while self.bids and self.asks and self.bids[0].price >= self.asks[0].price:
            highest_bid = heapq.heappop(self.bids)
            lowest_ask = heapq.heappop(self.asks)

            if highest_bid.quantity > lowest_ask.quantity:
                highest_bid.quantity -= lowest_ask.quantity
                self.filled_orders_log.append(f"Filled {lowest_ask} with {highest_bid}")
                heapq.heappush(self.bids, highest_bid)
                update_order_in_db(highest_bid)  # Update the remaining quantity
            elif highest_bid.quantity < lowest_ask.quantity:
                lowest_ask.quantity -= highest_bid.quantity
                self.filled_orders_log.append(f"Filled {highest_bid} with {lowest_ask}")
                heapq.heappush(self.asks, lowest_ask)
                update_order_in_db(lowest_ask)
            else:
                self.filled_orders_log.append(f"Fully filled {highest_bid} with {lowest_ask}")

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

    def show_order_book(self):
        asks_table = [[ask.order_id, ask.price, ask.quantity] for ask in sorted(self.asks, key=lambda o: o.price)]
        bids_table = [[bid.order_id, bid.price, bid.quantity] for bid in sorted(self.bids, key=lambda o: -o.price)]

        print("Current Asks:")
        print(tabulate(asks_table, headers=["Order ID", "Price", "Quantity"], tablefmt="grid"))
        print("Current Bids:")
        print(tabulate(bids_table, headers=["Order ID", "Price", "Quantity"], tablefmt="grid"))

        print("\nFilled Orders Log:")
        for log in self.filled_orders_log:
            print(log)

    def show_price_summary(self):
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

        print("\nORDER BOOK SUMMARY")
        print("Asks (Sell Orders):")
        print(tabulate(ask_rows, headers=["Price", "Total Quantity"], tablefmt="grid"))

        print("\nBids (Buy Orders):")
        print(tabulate(bid_rows, headers=["Price", "Total Quantity"], tablefmt="grid"))
