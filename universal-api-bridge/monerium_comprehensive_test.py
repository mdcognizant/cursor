#!/usr/bin/env python3
"""
COMPREHENSIVE MONERIUM API TEST SUITE
=====================================

This script systematically tests ALL Monerium API endpoints to understand:
- What works vs what doesn't
- Sandbox vs Production differences  
- Authentication requirements
- Error patterns
- Best practices

Run this as a developer to understand the API before building integrations.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configuration
CLIENT_ID = "54be063f-6cca-11f0-a3e6-4eb54501c717"
CLIENT_SECRET = "71ab65b523e1651fa197ea39ecf2156ed30da3199c668053029860133e0cfdd5"
BACKEND_URL = "http://localhost:8006"

class MoneriumTester:
    def __init__(self, environment: str = "sandbox"):
        self.environment = environment
        self.access_token = None
        self.results = {
            "environment": environment,
            "test_time": datetime.now().isoformat(),
            "authentication": {},
            "endpoints": {},
            "errors": [],
            "working_features": [],
            "broken_features": [],
            "limitations": []
        }
        
    def log_result(self, category: str, endpoint: str, status: str, details: Dict[str, Any]):
        """Log test results for documentation"""
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][endpoint] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        # Categorize results
        if status == "SUCCESS":
            self.results["working_features"].append(f"{category}.{endpoint}")
        elif status == "FAILED":
            self.results["broken_features"].append(f"{category}.{endpoint}")
        elif status == "LIMITED":
            self.results["limitations"].append(f"{category}.{endpoint}: {details.get('reason', 'Unknown')}")

    def call_api(self, method: str, endpoint: str, headers: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Call Monerium API via backend proxy"""
        proxy_data = {
            "method": method,
            "endpoint": endpoint,
            "headers": headers or {},
            "data": data,
            "environment": self.environment
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/proxy",
                headers={"Content-Type": "application/json"},
                json=proxy_data,
                timeout=30
            )
            
            if response.ok:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "status_code": 0
            }

    def test_authentication(self):
        """Test all authentication flows"""
        print("\n🔐 TESTING AUTHENTICATION")
        print("=" * 50)
        
        # Test 1: Client Credentials
        print("1. Testing Client Credentials Flow...")
        auth_result = self.call_api(
            "POST",
            "/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }
        )
        
        if auth_result.get("success") and auth_result.get("data", {}).get("access_token"):
            self.access_token = auth_result["data"]["access_token"]
            print(f"   ✅ SUCCESS: Got token {self.access_token[:20]}...")
            self.log_result("authentication", "client_credentials", "SUCCESS", {
                "token_received": True,
                "expires_in": auth_result["data"].get("expires_in"),
                "token_type": auth_result["data"].get("token_type")
            })
        else:
            print(f"   ❌ FAILED: {auth_result.get('error', 'Unknown error')}")
            self.log_result("authentication", "client_credentials", "FAILED", auth_result)
            return False
        
        # Test 2: Token validation
        print("2. Testing Token Validation...")
        context_result = self.call_api(
            "GET",
            "/auth/context",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        if context_result.get("success"):
            print(f"   ✅ Token valid - User: {context_result['data'].get('name', 'Unknown')}")
            self.log_result("authentication", "token_validation", "SUCCESS", context_result["data"])
        else:
            print(f"   ❌ Token validation failed: {context_result.get('error')}")
            self.log_result("authentication", "token_validation", "FAILED", context_result)
        
        return True

    def test_core_endpoints(self):
        """Test core API endpoints"""
        print("\n📋 TESTING CORE ENDPOINTS")
        print("=" * 50)
        
        if not self.access_token:
            print("❌ Cannot test - no access token")
            return
        
        core_endpoints = [
            ("GET", "/profiles", "Get user profiles"),
            ("GET", "/addresses", "Get linked addresses"),
            ("GET", "/ibans", "Get IBAN accounts"),
            ("GET", "/orders", "Get orders"),
            ("GET", "/tokens", "Get supported tokens"),
            ("GET", "/webhooks", "Get webhooks")
        ]
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        for method, endpoint, description in core_endpoints:
            print(f"Testing {endpoint} - {description}")
            result = self.call_api(method, endpoint, headers)
            
            if result.get("success"):
                data = result.get("data", {})
                if isinstance(data, dict):
                    # Count items if it's a list response
                    for key in ["profiles", "addresses", "ibans", "orders", "webhooks"]:
                        if key in data:
                            count = len(data[key]) if isinstance(data[key], list) else "unknown"
                            print(f"   ✅ SUCCESS: Found {count} {key}")
                            break
                    else:
                        # For tokens endpoint
                        if isinstance(data, list):
                            print(f"   ✅ SUCCESS: Found {len(data)} tokens")
                        else:
                            print(f"   ✅ SUCCESS: Got data")
                elif isinstance(data, list):
                    print(f"   ✅ SUCCESS: Found {len(data)} items")
                else:
                    print(f"   ✅ SUCCESS: Got response")
                
                self.log_result("core_endpoints", endpoint, "SUCCESS", {
                    "data_type": str(type(data)),
                    "response": data
                })
            else:
                error_msg = result.get("data", {}).get("message", result.get("error", "Unknown"))
                print(f"   ❌ FAILED: {error_msg}")
                self.log_result("core_endpoints", endpoint, "FAILED", result)

    def test_balance_endpoints(self):
        """Test balance checking for different chains"""
        print("\n💰 TESTING BALANCE ENDPOINTS")
        print("=" * 50)
        
        if not self.access_token:
            print("❌ Cannot test - no access token")
            return
        
        # Get addresses first
        headers = {"Authorization": f"Bearer {self.access_token}"}
        addresses_result = self.call_api("GET", "/addresses", headers)
        
        if not addresses_result.get("success"):
            print("❌ Cannot get addresses for balance testing")
            self.log_result("balance_endpoints", "prerequisite", "FAILED", 
                          {"reason": "Could not get addresses"})
            return
        
        addresses = addresses_result.get("data", {}).get("addresses", [])
        print(f"Found {len(addresses)} address(es) to test")
        
        chains_to_test = ["ethereum", "gnosis", "polygon", "arbitrum", "linea"]
        test_address = "0x50E772C294f8940B97dcC872f343263c11a90dE7"  # Known address
        
        for chain in chains_to_test:
            print(f"\nTesting {chain} balances...")
            
            # Test with known address
            balance_result = self.call_api(
                "GET",
                f"/balances/{chain}/{test_address}",
                headers
            )
            
            if balance_result.get("success"):
                balances = balance_result.get("data", {}).get("balances", [])
                print(f"   ✅ SUCCESS: {chain} - Found {len(balances)} balance(s)")
                for balance in balances:
                    currency = balance.get("currency", "unknown")
                    amount = balance.get("amount", "0")
                    print(f"      {currency.upper()}: {amount}")
                
                self.log_result("balance_endpoints", f"{chain}_balances", "SUCCESS", {
                    "address": test_address,
                    "balances": balances
                })
            else:
                error_msg = balance_result.get("data", {}).get("message", "Unknown error")
                if "not linked" in error_msg.lower():
                    print(f"   ⚠️  LIMITED: {chain} - Address not linked to this chain")
                    self.log_result("balance_endpoints", f"{chain}_balances", "LIMITED", {
                        "reason": "Address not linked to chain",
                        "error": error_msg
                    })
                else:
                    print(f"   ❌ FAILED: {chain} - {error_msg}")
                    self.log_result("balance_endpoints", f"{chain}_balances", "FAILED", balance_result)

    def test_wallet_linking(self):
        """Test wallet linking capabilities"""
        print("\n🔗 TESTING WALLET LINKING")
        print("=" * 50)
        
        if not self.access_token:
            print("❌ Cannot test - no access token")
            return
        
        # This is a read-only test - we won't actually link wallets
        print("1. Testing wallet link endpoint accessibility...")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test if we can access the link endpoint (should fail with validation error, not auth error)
        link_result = self.call_api(
            "POST",
            "/addresses",
            headers,
            {"address": "0x0000000000000000000000000000000000000000"}  # Invalid address for testing
        )
        
        if link_result.get("status_code") == 400:
            print("   ✅ Endpoint accessible (validation error expected)")
            self.log_result("wallet_linking", "link_endpoint", "SUCCESS", {
                "endpoint_accessible": True,
                "requires_valid_data": True
            })
        elif link_result.get("status_code") == 401:
            print("   ❌ Authentication issue")
            self.log_result("wallet_linking", "link_endpoint", "FAILED", {
                "reason": "Authentication failed"
            })
        else:
            print(f"   ⚠️  Unexpected response: {link_result.get('status_code')}")
            self.log_result("wallet_linking", "link_endpoint", "LIMITED", link_result)

    def test_order_creation(self):
        """Test order creation capabilities (read-only)"""
        print("\n📝 TESTING ORDER CREATION")
        print("=" * 50)
        
        if not self.access_token:
            print("❌ Cannot test - no access token")
            return
        
        print("1. Testing order endpoint accessibility...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test with minimal invalid data to check endpoint accessibility
        order_result = self.call_api(
            "POST",
            "/orders",
            headers,
            {"amount": "0", "currency": "eur"}  # Invalid but structured data
        )
        
        status_code = order_result.get("status_code", 0)
        
        if status_code == 400:
            print("   ✅ Endpoint accessible (validation error expected)")
            self.log_result("order_creation", "create_order", "SUCCESS", {
                "endpoint_accessible": True,
                "requires_valid_data": True
            })
        elif status_code == 401:
            print("   ❌ Authentication issue")
            self.log_result("order_creation", "create_order", "FAILED", {
                "reason": "Authentication failed"
            })
        elif status_code == 403:
            print("   ⚠️  Forbidden - may require additional permissions")
            self.log_result("order_creation", "create_order", "LIMITED", {
                "reason": "Insufficient permissions"
            })
        else:
            print(f"   ⚠️  Unexpected response: {status_code}")
            self.log_result("order_creation", "create_order", "LIMITED", order_result)

    def test_special_features(self):
        """Test special Monerium features"""
        print("\n🎯 TESTING SPECIAL FEATURES")
        print("=" * 50)
        
        if not self.access_token:
            print("❌ Cannot test - no access token")
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test various endpoints that might exist
        special_endpoints = [
            ("GET", "/profile", "Single profile endpoint"),
            ("GET", "/me", "User info endpoint"),
            ("GET", "/account", "Account details"),
            ("GET", "/currencies", "Supported currencies"),
            ("GET", "/chains", "Supported chains"),
            ("GET", "/fees", "Fee structure"),
            ("GET", "/limits", "Account limits")
        ]
        
        for method, endpoint, description in special_endpoints:
            print(f"Testing {endpoint} - {description}")
            result = self.call_api(method, endpoint, headers)
            
            if result.get("success"):
                print(f"   ✅ SUCCESS: {description} works")
                self.log_result("special_features", endpoint, "SUCCESS", result["data"])
            elif result.get("status_code") == 404:
                print(f"   ⚠️  Not available: {description}")
                self.log_result("special_features", endpoint, "LIMITED", {"reason": "Endpoint not found"})
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown')}")
                self.log_result("special_features", endpoint, "FAILED", result)

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 GENERATING TEST REPORT")
        print("=" * 50)
        
        working = len(self.results["working_features"])
        broken = len(self.results["broken_features"])
        limited = len(self.results["limitations"])
        
        print(f"✅ Working Features: {working}")
        print(f"❌ Broken Features: {broken}")
        print(f"⚠️  Limited Features: {limited}")
        
        # Save detailed report
        report_filename = f"monerium_test_report_{self.environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"universal-api-bridge/{report_filename}", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📋 Detailed report saved: {report_filename}")
        
        return self.results

    def run_full_test_suite(self):
        """Run all tests"""
        print(f"\n🚀 STARTING COMPREHENSIVE MONERIUM API TEST")
        print(f"Environment: {self.environment.upper()}")
        print(f"Backend: {BACKEND_URL}")
        print("=" * 60)
        
        # Run all test suites
        if self.test_authentication():
            self.test_core_endpoints()
            self.test_balance_endpoints()
            self.test_wallet_linking()
            self.test_order_creation()
            self.test_special_features()
        
        return self.generate_report()

def main():
    """Main test runner"""
    print("🏦 MONERIUM API COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("This will test ALL aspects of the Monerium API")
    print("Both sandbox and production environments")
    print("=" * 60)
    
    # Test Sandbox First
    print("\n🧪 TESTING SANDBOX ENVIRONMENT")
    sandbox_tester = MoneriumTester("sandbox")
    sandbox_results = sandbox_tester.run_full_test_suite()
    
    print("\n" + "="*60)
    
    # Test Production
    print("\n💰 TESTING PRODUCTION ENVIRONMENT")
    prod_tester = MoneriumTester("production")
    prod_results = prod_tester.run_full_test_suite()
    
    # Compare results
    print("\n📊 ENVIRONMENT COMPARISON")
    print("=" * 60)
    print(f"Sandbox Working: {len(sandbox_results['working_features'])}")
    print(f"Production Working: {len(prod_results['working_features'])}")
    
    print("\nTest complete! Check the generated JSON reports for details.")

if __name__ == "__main__":
    main() 