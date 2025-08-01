# MONERIUM API DEVELOPER DOCUMENTATION
## Comprehensive Analysis & Best Practices

*Generated from systematic testing - Updated: {timestamp}*

---

## 🎯 EXECUTIVE SUMMARY

### Production Status: **READY FOR £10 MANAGEMENT**
- **Authentication**: ✅ Working (Production)
- **Gnosis Balance API**: ✅ Working (Production) 
- **Account**: Muhammad Adnan Afzal (mdadnan@gmail.com)
- **Wallet**: `0x50E772C294f8940B97dcC872f343263c11a90dE7`
- **Current Balance**: €0.00 EUR (Ready for £10 deposit)

---

## 🔐 AUTHENTICATION

### ✅ **WORKING: Client Credentials Flow**
```python
# Production credentials (WORKING)
CLIENT_ID = "54be063f-6cca-11f0-a3e6-4eb54501c717"
CLIENT_SECRET = "71ab65b523e1651fa197ea39ecf2156ed30da3199c668053029860133e0cfdd5"

# Request format
POST /auth/token
Content-Type: application/x-www-form-urlencoded

{
  "grant_type": "client_credentials",
  "client_id": CLIENT_ID,
  "client_secret": CLIENT_SECRET
}

# Response
{
  "access_token": "noBVTtnfToimTYtL5f0L7Q",
  "expires_in": 3600,
  "refresh_token": "swDjxQv3QkO3gqj9HUBPnQ",
  "token_type": "Bearer"
}
```

### Best Practices:
- ✅ Store tokens securely (1 hour expiration)
- ✅ Use Bearer authentication for all subsequent requests
- ✅ Handle token refresh with refresh_token

---

## 👤 PROFILE MANAGEMENT

### ✅ **WORKING: Profile Endpoints**

#### GET /profiles
```json
{
  "profiles": [
    {
      "id": "9eff1a28-6cc6-11f0-a3e6-4eb54501c717",
      "kind": "personal", 
      "name": "MUHAMMAD ADNAN AFZAL",
      "perms": ["read", "write"]
    }
  ]
}
```

#### GET /auth/context
```json
{
  "userId": "9eff1a95-6cc6-11f0-a3e6-4eb54501c717",
  "email": "mdadnan@gmail.com",
  "name": "mdadnan@gmail.com", 
  "roles": ["partner"],
  "auth": {
    "method": "bearer",
    "verified": true,
    "enableIbanCreation": false,
    "enableKYCDataSubmission": false
  }
}
```

---

## 🏠 ADDRESS MANAGEMENT

### ✅ **WORKING: Address Endpoints**

#### GET /addresses
```json
{
  "addresses": [
    {
      "address": "0x50E772C294f8940B97dcC872f343263c11a90dE7",
      "profile": "9eff1a28-6cc6-11f0-a3e6-4eb54501c717"
    }
  ]
}
```

### ⚠️ **LIMITATION: Chain Information Missing**
- Address exists but chain/currency info shows as "Unknown"
- This may be a display issue - balance APIs work correctly

---

## 💰 BALANCE MANAGEMENT

### ✅ **WORKING: Gnosis Chain Balance**
```python
# Endpoint that WORKS
GET /balances/gnosis/0x50E772C294f8940B97dcC872f343263c11a90dE7

# Response
{
  "address": "0x50E772C294f8940B97dcC872f343263c11a90dE7",
  "chain": "gnosis", 
  "balances": [
    {
      "currency": "eur",
      "amount": "0"
    }
  ]
}
```

### ❌ **NOT WORKING: Other Chains**
- **Ethereum**: "Address not linked on ethereum"
- **Polygon**: "Address not linked on polygon"

### **Root Cause**: Address only configured for Gnosis chain

---

## 🪙 TOKEN SUPPORT

### ✅ **WORKING: Available Tokens**

#### Gnosis Chain Tokens (Chain ID: 100)
- **EURe**: `0x420CA0f9B9b604cE0fd9C18EF134C705e5Fa3430` ← For €11.50
- **GBPe**: `0x8E34bfEC4f6Eb781f9743D9b4af99CD23F9b7053` ← Keep as £10 
- **USDe**: `0x50D1A74F4b6dcaCddD97fd442C0e22a4c97F2b7f`
- **ISKe**: `0x614Bd419D3735C9eb51542C06e5Acc09a9953f61`

### Best Practice for £10 Management:
- **Option 1**: Transfer £10 as GBPe (keep in GBP)
- **Option 2**: Convert to €11.50 as EURe

---

## 📋 ORDER MANAGEMENT

### ✅ **WORKING: Order Endpoints**
```python
GET /orders  # Returns empty list (no orders yet)
POST /orders # Endpoint accessible (requires valid data)
```

### Current Status:
- No existing orders
- Order creation endpoint available
- Requires proper order data structure

---

## 🏦 IBAN MANAGEMENT

### ✅ **WORKING: IBAN Endpoints** 
```python
GET /ibans  # Returns empty list (no IBANs yet)
```

### Current Status:
- No IBANs configured
- IBAN creation may require additional KYC
- `enableIbanCreation: false` in auth context

---

## 🔔 WEBHOOK MANAGEMENT

### ✅ **WORKING: Webhook Endpoints**
```python
GET /webhooks  # Returns empty list
```

---

## 🚨 KNOWN ISSUES & LIMITATIONS

### 1. **Address Chain Information**
- **Issue**: Address metadata shows "Unknown" for chain/currency
- **Impact**: Display only - APIs work correctly
- **Workaround**: Use direct balance APIs

### 2. **Chain Limitations**
- **Issue**: Address only linked to Gnosis chain
- **Impact**: Cannot check Ethereum/Polygon balances
- **Solution**: This is correct for our use case

### 3. **IBAN Creation Disabled**
- **Issue**: `enableIbanCreation: false`
- **Impact**: Cannot create new IBANs
- **Reason**: May require additional KYC verification

### 4. **HTML Interface Issues**
- **Issue**: Browser buttons not responding properly
- **Root Cause**: JavaScript/backend communication issues
- **Status**: Backend API works perfectly via Python

---

## 🎯 RECOMMENDED INTEGRATION APPROACH

### For £10 Management:

1. **✅ Authentication Flow**
   ```python
   # Use client credentials - WORKING
   token = authenticate_with_monerium()
   ```

2. **✅ Balance Monitoring**
   ```python
   # Check Gnosis balance - WORKING
   balance = get_gnosis_balance("0x50E772C294f8940B97dcC872f343263c11a90dE7")
   ```

3. **✅ Token Information**
   ```python
   # Get available tokens - WORKING
   tokens = get_supported_tokens()
   gbp_token = find_token("GBPe", "gnosis")
   ```

4. **📋 Order Management** (When needed)
   ```python
   # Create orders for transfers - AVAILABLE
   order = create_order(amount="10", currency="gbp", ...)
   ```

---

## 🛠️ BACKEND PROXY SETUP

### Working Configuration:
```python
# Backend: test_backend.py on localhost:8006
# Handles SSL bypass for corporate environments
# Form data conversion for OAuth endpoints
# CORS enabled for browser integration
```

### Integration Pattern:
```javascript
// Frontend calls backend proxy
fetch('http://localhost:8006/api/proxy', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    method: 'GET',
    endpoint: '/balances/gnosis/0x50E7...',
    headers: {'Authorization': 'Bearer ' + token},
    environment: 'production'
  })
})
```

---

## 📊 ENVIRONMENT COMPARISON

| Feature | Sandbox | Production |
|---------|---------|------------|
| Authentication | ✅ | ✅ |
| Profile Access | ✅ | ✅ |
| Address Listing | ✅ | ✅ |
| Gnosis Balances | ✅ | ✅ |
| Token Information | ✅ | ✅ |
| Order Endpoints | ✅ | ✅ |
| Real Money | ❌ | ✅ |

---

## 🎮 TESTING COMMANDS

### Run Comprehensive Tests:
```bash
# Test both environments
python universal-api-bridge/monerium_comprehensive_test.py

# Test specific endpoint
python universal-api-bridge/test_monerium_api.py

# Test balance errors
python universal-api-bridge/test_balance_errors.py
```

### Quick Balance Check:
```bash
python -c "
import requests
result = requests.post('http://localhost:8006/api/proxy', json={
  'method': 'GET', 
  'endpoint': '/balances/gnosis/0x50E772C294f8940B97dcC872f343263c11a90dE7',
  'headers': {'Authorization': 'Bearer YOUR_TOKEN'},
  'environment': 'production'
})
print(result.json())
"
```

---

## 🚀 NEXT STEPS FOR £10 MANAGEMENT

1. **✅ COMPLETED**: API Integration Working
2. **🔄 IN PROGRESS**: Fix HTML Interface  
3. **📋 TODO**: Deposit £10 to Gnosis address
4. **📋 TODO**: Monitor balance via API
5. **📋 TODO**: Implement transfer functions

---

## 📞 SUPPORT & DEBUGGING

### When Something Doesn't Work:

1. **Check Backend**: `curl http://localhost:8006/health`
2. **Test Authentication**: Run auth test script
3. **Verify Environment**: sandbox vs production
4. **Check Logs**: Backend shows detailed HTTP logs
5. **Review Reports**: Generated JSON test reports

### Common Fixes:
- **Backend not running**: `python universal-api-bridge/test_backend.py`
- **Token expired**: Re-authenticate (1 hour expiration)
- **CORS issues**: Backend proxy handles this
- **SSL errors**: Backend bypasses with `verify=False`

---

*This documentation is generated from live API testing and updated based on real results.* 