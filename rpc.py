import jsonrpclib

# Connect to local RPC at port 8819 with credentials
server = jsonrpclib.Server('http://user:shie9jurballs@localhost:8819')

# Make verifymessage method with error handling
def verify_message(address, signature, message):
    try:
        return server.verifymessage(address, signature, message)
    except jsonrpclib.jsonrpc.ProtocolError as e:
        return f"Error verifying message: {e}"

def sign_message(message, private_key):
    try:
        return server.signmessage(message, private_key)
    except jsonrpclib.jsonrpc.ProtocolError as e:
        return f"Error signing message: {e}"
