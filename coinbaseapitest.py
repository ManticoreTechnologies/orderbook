import os
import json
from cdp import Cdp, Wallet, WalletData

# Configure API credentials from JSON file
Cdp.configure_from_json("./cdp_api_key.json")

# Check if my_seed.json exists
if not os.path.exists("my_seed.json"):
    # Create a new wallet if my_seed.json does not exist
    wallet = Wallet.create(network_id="base-mainnet")
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

# Create a new address every run
new_address = imported_wallet.create_address()
print(f"New address created: {new_address}")

prin
