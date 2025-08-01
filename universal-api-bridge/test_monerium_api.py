#!/usr/bin/env python3
"""
Test Monerium API to understand account structure and balance issues
"""

import requests
import json
from datetime import datetime

# Your real Monerium credentials
CLIENT_ID = "54be063f-6cca-11f0-a3e6-4eb54501c717"
CLIENT_SECRET = "71ab65b523e1651fa197ea39ecf2156ed30da3199c668053029860133e0cfdd5"
BACKEND_URL = "http://localhost:8006"

def call_monerium_api(method, endpoint, headers=None, data=None):
    """Call Monerium API via our backend proxy"""
    proxy_data = {
        "method": method,
        "endpoint": endpoint,
        "headers": headers or {},
        "data": data,
        "environment": "production"  # Using REAL production API
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/proxy",
        headers={"Content-Type": "application/json"},
        json=proxy_data
    )
    
    if response.ok:
        return response.json()
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def main():
    print("🏦 MONERIUM API PRODUCTION TEST")
    print("=" * 50)
    
    # Step 1: Authenticate
    print("\n1️⃣ AUTHENTICATING...")
    auth_response = call_monerium_api(
        "POST", 
        "/auth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    
    if not auth_response or not auth_response.get("success"):
        print("❌ Authentication failed!")
        return
    
    access_token = auth_response["data"]["access_token"]
    print(f"✅ Got access token: {access_token[:20]}...")
    
    # Step 2: Get profiles
    print("\n2️⃣ GETTING PROFILES...")
    profiles_response = call_monerium_api(
        "GET",
        "/profiles",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if profiles_response and profiles_response.get("success"):
        profiles = profiles_response["data"]["profiles"]
        print(f"✅ Found {len(profiles)} profile(s)")
        for i, profile in enumerate(profiles):
            print(f"  Profile {i+1}: {profile.get('id', 'No ID')} - {profile.get('name', 'No Name')}")
            print(f"    State: {profile.get('state', 'Unknown')}")
    else:
        print("❌ Failed to get profiles")
        return
    
    # Step 3: Get addresses
    print("\n3️⃣ GETTING ADDRESSES...")
    addresses_response = call_monerium_api(
        "GET",
        "/addresses",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if addresses_response and addresses_response.get("success"):
        addresses = addresses_response["data"]["addresses"]
        print(f"✅ Found {len(addresses)} address(es)")
        for i, addr in enumerate(addresses):
            print(f"  Address {i+1}: {addr.get('address', 'No Address')}")
            print(f"    Chain: {addr.get('chain', 'Unknown')}")
            print(f"    Currency: {addr.get('currency', 'Unknown')}")
            print(f"    State: {addr.get('state', 'Unknown')}")
            print(f"    Profile: {addr.get('profile', 'Unknown')}")
    else:
        print("❌ Failed to get addresses")
        return
    
    # Step 4: Test Gnosis balances for each address
    print("\n4️⃣ TESTING GNOSIS BALANCES...")
    gnosis_addresses = [addr for addr in addresses if addr.get('chain') == 'gnosis']
    
    if not gnosis_addresses:
        print("⚠️ No Gnosis addresses found!")
        print("Available chains:")
        for addr in addresses:
            print(f"  - {addr.get('chain', 'Unknown')}: {addr.get('address', 'No Address')}")
    else:
        for addr in gnosis_addresses:
            address = addr.get('address')
            print(f"\n  Testing Gnosis balance for: {address}")
            balance_response = call_monerium_api(
                "GET",
                f"/balances/gnosis/{address}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if balance_response:
                print(f"    Status: {balance_response.get('status_code', 'Unknown')}")
                if balance_response.get("success"):
                    balances = balance_response["data"]
                    print(f"    ✅ Balance data: {json.dumps(balances, indent=2)}")
                else:
                    print(f"    ❌ Balance error: {json.dumps(balance_response, indent=2)}")
            else:
                print("    ❌ Failed to get balance response")
    
    # Step 5: Test other balance endpoints
    print("\n5️⃣ TESTING OTHER BALANCE ENDPOINTS...")
    chains_to_test = ['ethereum', 'polygon']
    
    for chain in chains_to_test:
        print(f"\n  Testing {chain} balances...")
        chain_addresses = [addr for addr in addresses if addr.get('chain') == chain]
        
        if chain_addresses:
            for addr in chain_addresses:
                address = addr.get('address')
                balance_response = call_monerium_api(
                    "GET",
                    f"/balances/{chain}/{address}",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if balance_response and balance_response.get("success"):
                    print(f"    ✅ {chain} balance for {address}: {balance_response['data']}")
                else:
                    print(f"    ❌ {chain} balance failed for {address}")
        else:
            print(f"    ⚠️ No {chain} addresses found")
    
    print("\n" + "=" * 50)
    print("🔍 ANALYSIS COMPLETE")

if __name__ == "__main__":
    main() 