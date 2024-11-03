# Asyncio is used to start the websocket server
import asyncio
from datetime import datetime, timedelta

# Websockets is used to create the websocket server
import websockets

# Import the logger from LogX.py
from Database.accounts import get_session_token, set_session_token
from LogX import logger, log_received, log_sent

# Import secrets to generate a challenge
import secrets

from rpc import verify_message

# Dictionary to store event handlers
event_handlers = {}

# Dictionary to store client information
clients_info = {}

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
    
    session_data = get_session_token(address)   
    print(f"Session data: {session_data}")
    # Check if the user session is valid and not expired
    if session_data and session_data["session_token"] == user_session:
        session_created = datetime.fromisoformat(session_data["session_created"])
        time_diff = datetime.now() - session_created
        if time_diff <= timedelta(hours=12):
            remaining_time = timedelta(hours=12) - time_diff
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Session remaining time: {hours} hours, {minutes} minutes, {seconds} seconds")
            set_authenticated(websocket, True)
            return f"session_restored {remaining_time}"
        else:
            return "Session expired"
    else:
        return "Invalid session"

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
    # Decorator to make a command protected
    async def wrapper(websocket, *args, **kwargs):
        # Check if the websocket is in the clients_info dictionary
        try:
            client_info = clients_info[websocket]
        except KeyError:
            return "You are not authenticated. Please authenticate yourself with the 'auth' command."

        # Check if the client is authenticated
        if not client_info.get("authenticated", False):
            # Return a coroutine that yields the error message
            return await asyncio.sleep(0, result="You are not authenticated. Please authenticate yourself with the 'auth' command.")

        # Call the original function if authenticated
        return await func(websocket, client_info, *args, **kwargs)
    return wrapper

def onclose(websocket):
    """Handle the closing of a WebSocket connection."""
    logger.info(f"Connection closed for client: {id(websocket)}")
    remove_client(websocket)

# This will be the websocket server for all of TradeX
# It will be used to send and receive messages from the TradeX clients
async def hello(websocket, path):
    try:
        while True:
            message = await websocket.recv()
            if message != "ping":
                log_received(f"Received message: {message}")

            # Split the message into command and arguments
            parts = message.split()
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
    logger.info("WebSocket server started on ws://localhost:8765")
    await start_server.wait_closed()

def run_server():
    """Run the WebSocket server."""
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped manually")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    run_server()
