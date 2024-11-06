

import jsonrpclib
from HelperX import read_config_file

# Connect to local RPC at port 8819 with credentials
config = read_config_file('TradeX.conf')
server = jsonrpclib.Server(f'https://api.developer.coinbase.com/rpc/v1/base-sepolia/zoAesXIPYv52UVNCScYxe4wIMsfMWJ44')
def get_transaction(txid):
    return server.eth_getTransactionByHash(txid)
def get_transaction_receipt(txid):
    return server.eth_getTransactionReceipt(txid)