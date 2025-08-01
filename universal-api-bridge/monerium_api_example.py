import requests
import json

# === CONFIGURATION SECTION ===
# These values come from your registered Monerium app.
# If you're using your own account (personal app), use CLIENT CREDENTIALS GRANT.
# Authorization Code Flow is only required if your app accesses data on behalf of other users.

CLIENT_ID = "your_client_id"  # Issued by Monerium when you register your app
CLIENT_SECRET = "your_client_secret"  # Keep this secret! Used for client_credentials flow

# Your primary wallet address (must already be linked to your Monerium profile)
PRIMARY_WALLET_ADDRESS = "0xYourPrimaryWallet"

# Your secondary wallet address (you'll add this via API)
SECONDARY_WALLET_ADDRESS = "0xYourNewWallet"  # You control this wallet too

# Optional: An external IBAN (e.g. Revolut or HSBC, must be in your name)
RECIPIENT_IBAN = "GBxxYourIban"
RECIPIENT_NAME = "Your Full Legal Name"

# Choose the correct API base URL:
API_BASE_URL = "https://api.monerium.app"  # Use https://api.monerium.dev for sandbox/testing

# Blockchain details
CHAIN = "ethereum"
NETWORK = "sepolia"  # Use "mainnet" in production

# === STEP 1: CLIENT CREDENTIALS AUTH (Machine-to-Machine) ===
def get_access_token():
    """
    Authenticate using the OAuth2 client_credentials flow.
    This is used when your app is acting as itself (e.g., managing your own wallets).
    If you were building an app for others, you'd use Authorization Code Flow.
    """
    url = f"{API_BASE_URL}/auth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",  # Auth flow type
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET  # Needed here
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# === STEP 2: GET PROFILE ID ===
def get_profile_id(token):
    """
    Retrieve your profile ID (required for placing orders).
    Each verified Monerium user has a unique profile ID.
    """
    url = f"{API_BASE_URL}/auth/context"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["profiles"][0]

# === STEP 3: VIEW ALL IBANs LINKED TO YOUR ACCOUNT ===
def get_ibans(token):
    url = f"{API_BASE_URL}/ibans"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# === STEP 4: CHECK TOKEN BALANCE FOR A WALLET ===
def get_balance(token, wallet_address):
    url = f"{API_BASE_URL}/balances/{CHAIN}/{wallet_address}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# === STEP 5: PLACE ORDER TO MOVE MONEY (EXTERNAL OR INTERNAL) ===
def place_order(token, profile_id, amount_gbp, to_iban=None, to_wallet=None, to_name=None):
    """
    Send money either to:
      - an external IBAN (e.g., Revolut, HSBC), or
      - another wallet address that belongs to you (internal transfer)
    """
    url = f"{API_BASE_URL}/orders"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    if to_iban:
        # External bank transfer
        counterpart = {
            "identifier": {
                "standard": "iban",
                "iban": to_iban
            },
            "details": {
                "name": to_name
            }
        }
    elif to_wallet:
        # Internal wallet-to-wallet transfer (must be added to your profile first)
        counterpart = {
            "identifier": {
                "standard": "wallet",
                "wallet": to_wallet
            },
            "details": {
                "name": to_name or "My Secondary Wallet"
            }
        }
    else:
        raise ValueError("Must specify either to_iban or to_wallet.")

    data = {
        "amount": f"{amount_gbp:.2f}",
        "currency": "gbp",
        "chain": CHAIN,
        "network": NETWORK,
        "counterpart": counterpart,
        "message": "Internal transfer" if to_wallet else "Withdrawal to IBAN",
        "wallet": PRIMARY_WALLET_ADDRESS,
        "profile": profile_id,
        "signature": ""  # Required only for mainnet, not sandbox
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

# === STEP 6: ADD A NEW WALLET ADDRESS TO YOUR PROFILE ===
def add_wallet_address(token, new_wallet_address):
    """
    Registers another wallet address under your Monerium profile.
    Once added, you can transfer GBPe between your own wallets.
    """
    url = f"{API_BASE_URL}/addresses"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "address": new_wallet_address,
        "chain": CHAIN,
        "network": NETWORK,
        "kind": "personal"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # 1. Authenticate with client credentials
    token = get_access_token()
    print("✅ Access token received.")

    # 2. Get your Monerium profile ID
    profile_id = get_profile_id(token)
    print(f"✅ Profile ID: {profile_id}")

    # 3. Get all IBANs issued to you
    ibans = get_ibans(token)
    print(f"✅ Your Monerium IBANs:\n{json.dumps(ibans, indent=2)}")

    # 4. Get current balance in your primary wallet
    balance = get_balance(token, PRIMARY_WALLET_ADDRESS)
    print(f"✅ Balance in primary wallet:\n{json.dumps(balance, indent=2)}")

    # 5. OPTIONAL: Add your secondary wallet to Monerium profile
    add_wallet_result = add_wallet_address(token, SECONDARY_WALLET_ADDRESS)
    print(f"✅ Secondary wallet added:\n{json.dumps(add_wallet_result, indent=2)}")

    # 6. Transfer £5 from your primary to your secondary wallet (internal Monerium transfer)
    transfer_result = place_order(
        token=token,
        profile_id=profile_id,
        amount_gbp=5.00,
        to_wallet=SECONDARY_WALLET_ADDRESS
    )
    print(f"✅ Internal wallet transfer result:\n{json.dumps(transfer_result, indent=2)}")

    # 7. OPTIONAL: Withdraw £5 to your Revolut or bank account
    # withdraw_result = place_order(
    #     token=token,
    #     profile_id=profile_id,
    #     amount_gbp=5.00,
    #     to_iban=RECIPIENT_IBAN,
    #     to_name=RECIPIENT_NAME
    # )
    # print(f"✅ Withdrawal result:\n{json.dumps(withdraw_result, indent=2)}") 