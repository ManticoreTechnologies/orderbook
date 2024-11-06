# Import the Cdp class from the cdp module
import json
import os
from cdp import Cdp, Wallet, WalletData, Address

# Configure API credentials from JSON file
Cdp.configure_from_json("./cdp_api_key.json")

def create_wallet():
    return Wallet.create()#network_id="base-mainnet")

def load_wallet():
    # Check if my_seed.json exists
    if not os.path.exists("my_seed.json"):
        # Create a new wallet if my_seed.json does not exist
        wallet = Wallet.create()
        # Export the data required to re-instantiate the wallet. The data contains the seed and the ID of the wallet.
        data = wallet.export_data()
        
        # Save the data to a file
        with open("my_seed.json", "w") as file:
            json.dump(data.to_dict(), file)
        print("Wallet created and seed saved.")
    else:
        # Load the wallet data if my_seed.json exists
        with open("my_seed.json", "r") as file:
            fetch_data = json.load(file)
        imported_wallet = Wallet.import_data(WalletData.from_dict(fetch_data))
        print("Wallet loaded from existing seed.")

    return imported_wallet

def new_usdc_address():
    wallet = load_wallet()
    new_address = wallet.create_address()
    return new_address

def get_usdc_balance(address):
    wallet = load_wallet()
    wallet.balances

