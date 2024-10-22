import random
import uuid
from orderbook import Order

def generate_random_order():
    order_type = random.choice(['buy', 'sell'])
    price = random.randint(95, 105)
    quantity = random.randint(1, 10)
    order_id = str(uuid.uuid4())
    user_id = random.choice(['user1', 'user2'])  # Example user IDs
    return Order(order_id, price, quantity, order_type, user_id)

def should_cancel_order():
    return random.random() < 0.1  # 10% chance to cancel an order

