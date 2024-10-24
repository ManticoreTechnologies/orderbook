import heapq
import json
from tabulate import tabulate
from dbwrapper import get_connection, load_orders_from_db, save_order_to_db, save_ticker_to_db, update_order_in_db, delete_order_from_db, current_timestamp, load_accounts_from_db, save_account_to_db, load_account_from_db
from datetime import datetime, timedelta
from account import Account
import asyncio

class Order:
    def __init__(self, order_id, price, quantity, side, user_id, timestamp=None):
        self.order_id = order_id
        self.price = price
        self.quantity = quantity
        self.side = side
        self.user_id = user_id
        self.timestamp = timestamp or datetime.now()

    def __lt__(self, other):
        if self.side == 'sell':
            return self.price < other.price
        else:
            return self.price > other.price

    def __repr__(self):
        return f'Order({self.side}, id={self.order_id}, price={self.price}, qty={self.quantity}, time={self.timestamp}, user_id={self.user_id})'

class OrderBook:
    def __init__(self, websocket_server=None):
        self.bids = []  # Max-heap for bids
        self.asks = []  # Min-heap for asks
        self.order_map = {}  # To keep track of all active orders by order_id
        self.filled_orders_log = []
        self.accounts = {}  # To keep track of all accounts by user_id
        self.load_orders()  # Load active orders from the database
        self.load_accounts()  # Load accounts from the database
        self.websocket_server = websocket_server  # Assign WebSocket server instance

    async def add_order(self, order):
        # Retrieve account details from the database
        account_data = load_account_from_db(order.user_id)
        if account_data:
            user_id, username, balance = account_data
            account = Account(user_id, username, balance)
        else:
            raise ValueError(f"Account with user_id {order.user_id} not found.")

        order_cost = order.price * order.quantity

        if order.side == 'buy' and account.balance >= order_cost:
            account.update_balance(-order_cost)
            account.update_on_hold_balance(order_cost)
        elif order.side == 'sell':
            # Assuming the user has the quantity to sell
            pass
        else:
            print(f"Insufficient balance for user {order.user_id} to place order {order}")
            return

        if order.side == 'buy':
            heapq.heappush(self.bids, order)
        else:
            heapq.heappush(self.asks, order)

        save_order_to_db(order)
        self.order_map[order.order_id] = order
        await self.broadcast_update(f"New order added: {order}")

    async def cancel_order(self, order_id):
        # Strip any whitespace from the order_id
        order_id = order_id.strip()

        # Debugging: Print the order_id and the keys in the order_map
        print(f"Attempting to cancel order with ID: '{order_id}'")
        print(f"Current order_map keys: {list(self.order_map.keys())}")

        # Ensure all keys are stripped of whitespace
        if order_id in (key.strip() for key in self.order_map.keys()):
            order = self.order_map.pop(order_id)
            if order.side == 'buy':
                self.bids = [o for o in self.bids if o.order_id != order_id]
                heapq.heapify(self.bids)
            else:
                self.asks = [o for o in self.asks if o.order_id != order_id]
                heapq.heapify(self.asks)

            # Update the order status in the database to 'cancelled'
            conn = get_connection()
            query = "UPDATE orders SET status = 'cancelled', updated_at = ? WHERE order_id = ?"
            conn.execute(query, (current_timestamp(), order_id))
            conn.commit()
            conn.close()

            print(f"Cancelled {order}")
            await self.broadcast_update(f"Order cancelled: {order}")
        else:
            print(f"Order with ID '{order_id}' not found.")

    async def broadcast_update(self, message):
        if self.websocket_server:
            await self.websocket_server.broadcast(message)
        else:
            print("WebSocket server not initialized.")

    async def match_orders(self):
        ticker_price = None
        total_matched_quantity = 0  # Track total matched quantity for this call
        
        while self.bids and self.asks and self.bids[0].price >= self.asks[0].price:
            highest_bid = heapq.heappop(self.bids)
            lowest_ask = heapq.heappop(self.asks)

            matched_quantity = min(highest_bid.quantity, lowest_ask.quantity)
            total_matched_quantity += matched_quantity  # Accumulate matched quantity

            # Determine the transaction price based on order timestamps
            if highest_bid.timestamp <= lowest_ask.timestamp:
                transaction_price = highest_bid.price
            else:
                transaction_price = lowest_ask.price

            # Record the trade in the trade history
            conn = get_connection()
            trade_query = """INSERT INTO trade_history (user_id, order_id, price, quantity, side, taker, timestamp)
                             VALUES (?, ?, ?, ?, ?, ?, ?)"""
            
            # the  maker is  the oldest trade
            if highest_bid.timestamp <= lowest_ask.timestamp:
                conn.execute(trade_query, (highest_bid.user_id, highest_bid.order_id, transaction_price, matched_quantity, highest_bid.side, True, current_timestamp()))
                conn.execute(trade_query, (lowest_ask.user_id, lowest_ask.order_id, transaction_price, matched_quantity, lowest_ask.side, False, current_timestamp()))
            else:
                conn.execute(trade_query, (highest_bid.user_id, highest_bid.order_id, transaction_price, matched_quantity, highest_bid.side, False, current_timestamp()))
                conn.execute(trade_query, (lowest_ask.user_id, lowest_ask.order_id, transaction_price, matched_quantity, lowest_ask.side, True, current_timestamp()))
            conn.commit()
            conn.close()

            # Update account balances
            highest_bid_account = self.accounts.get(highest_bid.user_id)
            lowest_ask_account = self.accounts.get(lowest_ask.user_id)

            if highest_bid_account and lowest_ask_account:
                highest_bid_account.update_on_hold_balance(-transaction_price * matched_quantity)
                lowest_ask_account.update_balance(transaction_price * matched_quantity)

            if highest_bid.quantity > lowest_ask.quantity:
                highest_bid.quantity -= lowest_ask.quantity
                self.filled_orders_log.append(f"Filled: {lowest_ask, highest_bid}")
                heapq.heappush(self.bids, highest_bid)
                update_order_in_db(highest_bid)  # Update the remaining quantity
                await self.broadcast_update(f"Filled: {lowest_ask, highest_bid}")
            elif highest_bid.quantity < lowest_ask.quantity:
                lowest_ask.quantity -= highest_bid.quantity
                self.filled_orders_log.append(f"Filled: {[highest_bid, lowest_ask]}")
                heapq.heappush(self.asks, lowest_ask)
                update_order_in_db(lowest_ask)
                await self.broadcast_update(f"Filled: {[highest_bid, lowest_ask]}")
            else:
                self.filled_orders_log.append(f"Fulfilled: {highest_bid, lowest_ask}")
                await self.broadcast_update(f"Filled: {highest_bid, lowest_ask}")

            # Update the ticker price to the transaction price
            ticker_price = transaction_price

            if highest_bid.quantity == 0:
                update_order_in_db(highest_bid)
            if lowest_ask.quantity == 0:
                update_order_in_db(lowest_ask)

        # Save the ticker to the database once after all matches
        if total_matched_quantity > 0 and ticker_price is not None:
            save_ticker_to_db({'price': ticker_price, 'quantity': total_matched_quantity})

    def load_orders(self):
        """Restore active orders from the database on startup."""
        orders = load_orders_from_db()
        for order_id, user_id, price, quantity, side in orders:
            print(f"Loading order: {order_id}, {price}, {quantity}, {side}, {user_id}")  # Debug print
            order = Order(order_id=order_id, price=price, quantity=quantity, side=side, user_id=user_id)
            if side == 'buy':
                heapq.heappush(self.bids, order)
            else:
                heapq.heappush(self.asks, order)
            self.order_map[order_id] = order
        print(f"Restored {len(orders)} orders from the database.")
        # Uncomment the line below if you want to broadcast the restored orders
        # await self.broadcast_update(f"Restored {len(orders)} orders from the database.")

    async def show_order_book(self):
        asks_table = [[ask.order_id, ask.price, ask.quantity] for ask in sorted(self.asks, key=lambda o: o.price)]
        bids_table = [[bid.order_id, bid.price, bid.quantity] for bid in sorted(self.bids, key=lambda o: -o.price)]

        asks_output = tabulate(asks_table, headers=["Order ID", "Price", "Quantity"], tablefmt="grid")
        bids_output = tabulate(bids_table, headers=["Order ID", "Price", "Quantity"], tablefmt="grid")

        #print("Current Asks:")
        #print(asks_output)
        #print("Current Bids:")
        #print(bids_output)

        await self.broadcast_update(f'Current Asks:{json.dumps(asks_table)}')
        await self.broadcast_update(f'Current Bids:{json.dumps(bids_table)}')

        #print("\nFilled Orders Log:")
        #for log in self.filled_orders_log:
        #    print(log)
        #    await self.broadcast_update(log)

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

    def get_latest_ticker(self):
        """Retrieve the latest ticker information."""
        conn = get_connection()
        query = "SELECT timestamp, price, quantity FROM tickers ORDER BY id DESC LIMIT 1"
        ticker = conn.execute(query).fetchone()
        conn.close()
        if ticker:
            return f"Latest Ticker: Time: {ticker[0]}, Price: {ticker[1]}, Quantity: {ticker[2]}"
        return "No ticker data available."

    def get_ticker_history(self):
        """Retrieve the ticker history in ascending order by timestamp."""
        conn = get_connection()
        query = "SELECT timestamp, price, quantity FROM tickers ORDER BY timestamp ASC"
        tickers = conn.execute(query).fetchall()
        conn.close()
        return tickers

    def update_user_balance(self, user_id, amount):
        conn = get_connection()
        query = "UPDATE users SET balance = balance + ? WHERE user_id = ?"
        conn.execute(query, (amount, user_id))
        conn.commit()
        conn.close()

    def get_trade_history(self):
        conn = get_connection()
        query = "SELECT * FROM trade_history WHERE taker = 1 ORDER BY timestamp DESC LIMIT 20"
        trades = conn.execute(query).fetchall()
        conn.close()
        return trades

    def load_accounts(self):
        """Restore accounts from the database on startup."""
        accounts = load_accounts_from_db()
        for user_id, username, balance in accounts:
            self.accounts[user_id] = Account(user_id, username, balance)
        print(f"Restored {len(accounts)} accounts from the database.")

    def save_account(self, account):
        """Save an account to the database."""
        save_account_to_db(account)
        print(f"Saved account: {account}")

    async def broadcast_trade_history(self):
        if self.websocket_server:
            trade_history = self.get_trade_history()
            await self.websocket_server.broadcast(f"Trade History: {json.dumps(trade_history)}")
        else:
            print("WebSocket server not initialized.")

    def calculate_ohlc(self, resolution):
        """Calculate OHLC data for a given resolution using taker trade history only."""
        #print(f"Calculating OHLC for resolution: {resolution}")
        end_time = datetime.now()

        if 'second' in resolution:
            seconds = int(resolution.split()[0])
            start_time = end_time - timedelta(seconds=seconds)
        elif 'minute' in resolution:
            minutes = int(resolution.split()[0])
            start_time = end_time.replace(second=0, microsecond=0) - timedelta(minutes=minutes)
        elif 'hour' in resolution:
            hours = int(resolution.split()[0])
            start_time = end_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours)
        elif 'day' in resolution:
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        else:
            raise ValueError("Unsupported resolution")

        conn = get_connection()
        query = "SELECT timestamp FROM ohlc WHERE resolution = ? ORDER BY timestamp DESC LIMIT 1"
        latest_ohlc = conn.execute(query, (resolution,)).fetchone()
        conn.close()

        if latest_ohlc:
            latest_timestamp = datetime.fromisoformat(latest_ohlc[0])
            if latest_timestamp >= start_time:
                print(f"Skipping OHLC update for {resolution}, latest timestamp: {latest_timestamp}")
                return None

        conn = get_connection()
        query = """
        SELECT price, quantity, timestamp FROM trade_history
        WHERE taker = 1 AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
        """
        trades = conn.execute(query, (start_time.isoformat(), end_time.isoformat())).fetchall()
        conn.close()

        if not trades:
            #print(f"No trades found for {resolution} between {start_time} and {end_time}")
            conn = get_connection()
            latest_trade_query = """
            SELECT price, quantity, timestamp FROM trade_history
            WHERE taker = 1
            ORDER BY timestamp DESC LIMIT 1
            """
            latest_trade = conn.execute(latest_trade_query).fetchone()
            conn.close()

            if not latest_trade:
                #print(f"No latest trade found for {resolution}")
                return None

            open_price = high_price = low_price = close_price = latest_trade[0]
            volume = latest_trade[1]
        else:
            open_price = trades[0][0]
            high_price = trades[0][0]
            low_price = trades[0][0]
            close_price = trades[-1][0]
            volume = 0

            for trade in trades:
                price = trade[0]
                quantity = trade[1]
                high_price = max(high_price, price)
                low_price = min(low_price, price)
                volume += quantity

        print(f"Calculated OHLC for {resolution}: Open={open_price}, High={high_price}, Low={low_price}, Close={close_price}, Volume={volume}")
        return {
            'resolution': resolution,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'timestamp': current_timestamp()
        }

    async def update_ohlc_data(self):
        #print("Updating OHLC data")
        resolutions = ['15 second', '1 minute', '5 minute', '15 minute', '30 minute', '1 hour', '4 hour', '8 hour', '1 day']
        ohlc_list = []
        for resolution in resolutions:
            ohlc_data = self.calculate_ohlc(resolution)
            if ohlc_data:
                self.save_ohlc_to_db(ohlc_data)
                ohlc_list.append(ohlc_data)
        await self.broadcast_ohlc(ohlc_list)

    def save_ohlc_to_db(self, ohlc_data):
        """Save or update OHLC data in the database."""
        print(f"Saving OHLC data to DB for resolution: {ohlc_data['resolution']}, timestamp: {ohlc_data['timestamp']}")
        conn = get_connection()
        
        query = "SELECT id FROM ohlc WHERE resolution = ? AND timestamp = ?"
        result = conn.execute(query, (ohlc_data['resolution'], ohlc_data['timestamp'])).fetchone()

        if result:
            print(f"Updating existing OHLC entry for resolution: {ohlc_data['resolution']}, timestamp: {ohlc_data['timestamp']}")
            query = """UPDATE ohlc SET open = ?, high = ?, low = ?, close = ?, volume = ?
                       WHERE id = ?"""
            values = (ohlc_data['open'], ohlc_data['high'], ohlc_data['low'], ohlc_data['close'], ohlc_data['volume'], result[0])
        else:
            print(f"Inserting new OHLC entry for resolution: {ohlc_data['resolution']}, timestamp: {ohlc_data['timestamp']}")
            query = """INSERT INTO ohlc (resolution, open, high, low, close, volume, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)"""
            values = (ohlc_data['resolution'], ohlc_data['open'], ohlc_data['high'], ohlc_data['low'], ohlc_data['close'], ohlc_data['volume'], ohlc_data['timestamp'])

        conn.execute(query, values)
        conn.commit()
        conn.close()

    async def broadcast_ohlc(self, ohlc_list):
        """Broadcast a list of OHLC data to WebSocket clients."""
        if self.websocket_server:
            pass
            #await self.websocket_server.broadcast(f"OHLC Data: {json.dumps(ohlc_list)}")
        else:
            print("WebSocket server not initialized.")

    def load_ohlc_from_db(self, resolution, limit=100):
        conn = get_connection()
        query = """
        SELECT open, high, low, close, volume, timestamp FROM ohlc
        WHERE resolution = ? ORDER BY timestamp DESC LIMIT ?
        """
        result = conn.execute(query, (resolution, limit)).fetchall()
        conn.close()
        if result:
            return [
                {
                    'open': row[0],
                    'high': row[1],
                    'low': row[2],
                    'close': row[3],
                    'volume': row[4],
                    'timestamp': row[5]
                }
                for row in result
            ]
        return None

    def get_taker_trade_history(self):
        """Retrieve the trade history for takers only."""
        conn = get_connection()
        query = "SELECT * FROM trade_history WHERE taker = 1 ORDER BY timestamp DESC"
        trades = conn.execute(query).fetchall()
        conn.close()
        return trades












