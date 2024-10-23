import json
import uuid
from dbwrapper import register_account
from orderbook import Order

async def process_message(message, order_book):
    try:
        if message.startswith("Register Account:"):
            _, account_details = message.split(":", 1)
            user_id, username, password = account_details.strip().split(",")
            register_account(user_id, username, password)
            return f"Account registered for user_id: {user_id}"
        
        if message == "get_latest_ticker":
            return "Latest Ticker: " + order_book.get_latest_ticker()
        
        #if message == "get_tickers":
        #    tickers = order_book.get_ticker_history()
        #    return "Tickers: " + json.dumps([{
        #        "timestamp": ticker[0],
        #        "price": ticker[1],
        #        "quantity": ticker[2]
        #    } for ticker in tickers])
        
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

        if message.startswith("get_trade_history"):
            trades = order_book.get_trade_history()
            return "Trade History: " + json.dumps(trades)

        if message.startswith("Check Balance:"):
            _, user_id = message.split(":", 1)
            user_id = user_id.strip()
            account = order_book.accounts.get(user_id)
            if account:
                balance = account.get_balance()
                return f"Balance for user {user_id}: {balance}"
            else:
                return f"Account with user_id {user_id} not found."

        if message.startswith("get_ohlc_data:"):
            _, resolution = message.split(":", 1)
            resolution = resolution.strip()
            ohlc_data = order_book.load_ohlc_from_db(resolution)
            if ohlc_data:
                return f"OHLC Data for {resolution}: {json.dumps(ohlc_data)}"
            else:
                return f"No OHLC data available for resolution: {resolution}"

    except Exception as e:
        print(f"Failed to process message: {message}, error: {e}")

    return None
