import requests
import json

# Test balance with your specific address
address = '0x50E772C294f8940B97dcC872f343263c11a90dE7'
token = 'noBVTtnfToimTYtL5f0L7Q'  # Your current token

for chain in ['gnosis', 'ethereum', 'polygon']:
    print(f'Testing {chain} balance for {address}...')
    
    body = {
        'method': 'GET',
        'endpoint': f'/balances/{chain}/{address}',
        'headers': {'Authorization': f'Bearer {token}'},
        'environment': 'production'
    }
    
    response = requests.post('http://localhost:8006/api/proxy', json=body)
    result = response.json()
    
    print(f'  Status: {result.get("status_code", "Unknown")}')
    if result.get('success'):
        print(f'  ✅ Data: {result["data"]}')
    else:
        print(f'  ❌ Error: {json.dumps(result, indent=2)}')
    print() 