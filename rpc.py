import requests
from HelperX import read_config_file

# Connect to local RPC at port 8819 with credentials
config = read_config_file('TradeX.conf')
auth = (config["RPC"]["rpc_user"], config["RPC"]["rpc_password"])
url = f'http://localhost:{config["RPC"]["rpc_port"]}'

# Make verifymessage method with error handling
def verify_message(address, signature, message):
    try:
        response = requests.post(url, auth=auth, json={"method": "verifymessage", "params": [address, signature, message]})
        response.raise_for_status()
        print(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"RequestException: {e}")
        return False

def sign_message(address, message):
    try:
        response = requests.post(url, auth=auth, json={"method": "signmessage", "params": [address, message]})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return False
    
def get_new_address():
    try:
        response = requests.post(url, auth=auth, json={"method": "getnewaddress"})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return False
    
def get_balance(address):
    try:
        response = requests.post(url, auth=auth, json={"method": "getaddressbalance", "params": [address]})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return False

if __name__ == "__main__":
    print(verify_message("EdsY3uu7tteVKCr7FdkrWs26t75LBwy4wQ", "IJj0ts/lK0TPUmSO7RBshfYkC+qyZnFFcrMqnj9ggI+8LS5QQ2zcwaqgM3WtN1G0JOssT3OorzAgaFQHnT3AN/8=", "message"))
