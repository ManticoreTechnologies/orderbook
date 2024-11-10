import random
import uuid
from orderbook import Order

# Global variable to track the current trend direction
trend_direction = random.choice([-1, 1])  # -1 for downward, 1 for upward

# Increase the trend strength
trend_strength = 2  # Adjust this value to control the trend strength

def generate_random_order():
    global trend_direction
    
    # Adjust the price range based on the trend direction
    base_price = 100
    price = random.randint(base_price - 2, base_price + 2) + trend_direction * trend_strength
    
    # Randomly change the trend direction more frequently
    if random.random() < 0.4:  # 40% chance to change trend direction
        trend_direction *= -1
    
    order_type = random.choice(['buy', 'sell'])
    quantity = random.randint(5, 20)  # Increase the quantity for a thicker order book
    order_id = str(uuid.uuid4())
    user_id = random.choice(['user1', 'user2'])  # Example user IDs
    return Order(order_id, price, quantity, order_type, user_id)

def should_cancel_order():
    return random.random() < 0.1  # 10% chance to cancel an order
