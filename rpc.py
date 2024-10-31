import jsonrpclib
from HelperX import read_config_file

# Connect to local RPC at port 8819 with credentials
config = read_config_file('TradeX.conf')
server = jsonrpclib.Server(f'http://{config["RPC"]["rpc_user"]}:{config["RPC"]["rpc_password"]}@localhost:{config["RPC"]["rpc_port"]}')

# Make verifymessage method with error handling
def verify_message(address, signature, message):
    try:
        return server.verifymessage(address, signature, message)
    except jsonrpclib.jsonrpc.ProtocolError:
        return False
    except Exception:
        return False

def sign_message(address, message):
    try:
        return server.signmessage(address, message)
    except jsonrpclib.jsonrpc.ProtocolError:
        return False
    except Exception:
        return False
    
def get_new_address():
    try:
        return server.getnewaddress()
    except jsonrpclib.jsonrpc.ProtocolError:
        return False
    except Exception:
        return False

if __name__ == "__main__":
    print(verify_message("EdsY3uu7tteVKCr7FdkrWs26t75LBwy4wQ", "IJj0ts/lK0TPUmSO7RBshfYkC+qyZnFFcrMqnj9ggI+8LS5QQ2zcwaqgM3WtN1G0JOssT3OorzAgaFQHnT3AN/8=", "message"))
