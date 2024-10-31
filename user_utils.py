from .dbwrapper import register_account

def register_simulation_users():
    users = [
        {"user_id": "user1", "username": "User One", "password": "password1", "balance": 1000000.0},
        {"user_id": "user2", "username": "User Two", "password": "password2", "balance": 1000000.0},
        {"user_id": "user3", "username": "User Three", "password": "password3", "balance": 1000000.0}
    ]
    for user in users:
        register_account(user["user_id"], user["username"], user["password"], user["balance"])
        print(f"Registered user: {user['user_id']} with balance: {user['balance']}")