# Asyncio is used to start the websocket server
import asyncio
from datetime import datetime, timedelta

# Websockets is used to create the websocket server
import websockets

# Import the logger from LogX.py
from Database.accounts import get_session_token, init_account, remove_session_token, set_session_token, validate_session_token
from LogX import logger, log_received, log_sent

# Import secrets to generate a challenge
import secrets

from rpc import verify_message

import inspect

# Dictionary to store event handlers
event_handlers = {}

# Dictionary to store client information
clients_info = {}

# Dictionary to store subscriptions
subscriptions = {}

async def broadcast(message):
    for websocket in clients_info.keys():
        await websocket.send(message)

# Decorator to register an event handler
def on(event_name):
    """Decorator to register an event handler."""
    def decorator(func):
        event_handlers[event_name] = func
        return func
    return decorator

@on("ping")
async def ping(websocket):
    # simulate a delay
    return "pong"

@on("restore_session")
async def restore_session(websocket, address, user_session):
    # Set the address in the client info
    update_client_info_field(websocket, "address", address)
    # Get the session token from the database
    valid, time_diff = validate_session_token(address, user_session)
    if valid:
        set_authenticated(websocket, True)
        print(f"Session remaining time: {time_diff}")
        return f"session_restored {time_diff}"
    else:
        return "session_invalid"



@on("authorize")
async def authorize(websocket, address):
    # Create a challenge
    challenge = secrets.token_hex(16)
    update_client_info_field(websocket, "challenge", challenge)
    update_client_info_field(websocket, "address", address)
    update_client_info_field(websocket, "challenge_created", datetime.now().isoformat()) 
    # Get the client info challenge
    client_info = get_client_info(websocket)    
    return f"auth_challenge {client_info['challenge']}"

@on("authorize_challenge")
async def authorize_challenge(websocket, signature):
    """ Client can attempt to complete a challenge
        The server will verify the signature and if valid, will authenticate the client
        Challenges expire after 1 minute and can only be used once
    """

    # First check if the challenge is still valid, challenges expire after 1 minute
    client_info = get_client_info(websocket)
    challenge_created = datetime.fromisoformat(client_info["challenge_created"])
    if datetime.now() - challenge_created > timedelta(minutes=1):
        # Remove the challenge from the client's info
        update_client_info_field(websocket, "challenge", None)  
        return "Challenge expired. Please start over"
    
    # Verify the signature
    if verify_message(client_info["address"], signature, client_info["challenge"]):
        # Authenticate the client
        set_authenticated(websocket, True)
        # Return a user session token
        user_session = secrets.token_hex(16)
        set_session_token(client_info["address"], user_session)
        # Initialize the account if it doesn't exist
        init_account(client_info["address"])
        return f"authorized {client_info['address']} {user_session}"
    else:
        return "authorization_failed"
    
def add_client(websocket, client_info):
    clients_info[websocket] = client_info



def get_client_info(websocket):
    return clients_info.get(websocket, None)
def remove_client(websocket):
    if websocket in clients_info:
        del clients_info[websocket]
def is_authenticated(websocket):
    client_info = get_client_info(websocket)
    return client_info.get("authenticated", False)
def set_authenticated(websocket, authenticated):
    client_info = get_client_info(websocket)
    client_info["authenticated"] = authenticated
def update_client_info(websocket, client_info):
    clients_info[websocket] = client_info
def update_client_info_field(websocket, field, value):
    try:
        client_info = get_client_info(websocket)
        client_info[field] = value
    except Exception as e:
        # add the client to the clients_info dictionary
        add_client(websocket, {field: value})
def get_client_info_field(websocket, field):
    client_info = get_client_info(websocket)
    return client_info.get(field, None)

def protected(func):
    async def wrapper(websocket, *args, **kwargs):
        # Check if the websocket is authenticated
        try:
            client_info = clients_info[websocket]
            if not client_info.get("authenticated", False):
                return await asyncio.sleep(0, result="You are not authenticated. Please authenticate yourself with the 'auth' command.")
        except KeyError:
            return "You are not authenticated. Please authenticate yourself with the 'auth' command."

        # Get the expected argument names for the function (excluding 'websocket' and 'client_info')
        expected_args = inspect.signature(func).parameters
        required_args = list(expected_args.keys())[2:]  # Skip 'websocket' and 'client_info'

        # Pass only the required arguments to the function
        filtered_args = args[:len(required_args)]
        return await func(websocket, client_info, *filtered_args, **kwargs)
    return wrapper

def onclose(websocket):
    """Handle the closing of a WebSocket connection."""
    logger.info(f"Connection closed for client: {id(websocket)}")
    # Remove the client from all subscriptions
    for event_name in list(subscriptions.keys()):
        unsubscribe(websocket, event_name)
    # Remove the client from the clients_info dictionary
    remove_client(websocket)

# This will be the websocket server for all of TradeX
# It will be used to send and receive messages from the TradeX clients
import shlex

async def hello(websocket):
    try:
        while True:
            message = await websocket.recv()
            if message != "ping":
                log_received(f"Received message: {message}")

            # Use shlex to split the message into command and arguments
            parts = shlex.split(message)
            command = parts[0]
            args = parts[1:]

            # Check if there's a registered handler for the command
            if command in event_handlers:
                # Pass the arguments to the handler
                response = await event_handlers[command](websocket, *args)
                await websocket.send(response)
                if response != "pong":
                    log_sent(f"Sent response: {response}")
            else:
                warning_message = f"No handler for command: {command}"
                await websocket.send(warning_message)
                logger.warning(warning_message)

    except websockets.ConnectionClosed as e:
        logger.error(f"Connection closed: {e}")
        onclose(websocket)  # Call the onclose function

async def start_server():
    """Start the WebSocket server."""
    start_server = await websockets.serve(hello, "localhost", 8765)
    logger.info("WebSocket server started on localhost:8765")
    await start_server.wait_closed()

def run_server():
    """Run the WebSocket server."""
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped manually")
    except Exception as e:
        logger.error(f"Server error: {e}")

def subscribe(websocket, event_name):
    """Subscribe a websocket to an event."""
    if event_name not in subscriptions:
        subscriptions[event_name] = set()
    subscriptions[event_name].add(websocket)

def unsubscribe(websocket, event_name):
    """Unsubscribe a websocket from an event."""
    if event_name in subscriptions:
        subscriptions[event_name].discard(websocket)
        if not subscriptions[event_name]:  # Remove the event if no subscribers left
            del subscriptions[event_name]

async def broadcast_to_subscribers(event_name, message):
    """Broadcast a message to all subscribers of a specific event."""
    if event_name in subscriptions:
        for websocket in subscriptions[event_name]:
            await websocket.send(message)

@on("subscribe")
async def handle_subscribe(websocket, event_name):
    """Handle subscription requests."""
    subscribe(websocket, event_name)
    return f"Subscribed to {event_name}"

@on("unsubscribe")
async def handle_unsubscribe(websocket, event_name):
    """Handle unsubscription requests."""
    unsubscribe(websocket, event_name)
    return f"Unsubscribed from {event_name}"

if __name__ == "__main__":
    run_server()
