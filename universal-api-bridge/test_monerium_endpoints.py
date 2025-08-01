import requests
import json

token = 'noBVTtnfToimTYtL5f0L7Q'

# Test other key endpoints
endpoints = [
    '/ibans',
    '/orders', 
    '/auth/context',
    '/tokens'
]

for endpoint in endpoints:
    print(f'=== TESTING {endpoint} ===')
    body = {
        'method': 'GET',
        'endpoint': endpoint,
        'headers': {'Authorization': f'Bearer {token}'},
        'environment': 'production'
    }
    
    response = requests.post('http://localhost:8006/api/proxy', json=body)
    result = response.json()
    
    print(f'Status: {result.get("status_code")}')
    if result.get('success'):
        print(f'✅ Data: {json.dumps(result["data"], indent=2)}')
    else:
        print(f'❌ Error: {result.get("data", {})}')
    print() 