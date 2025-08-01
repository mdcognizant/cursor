#!/usr/bin/env python3
"""
HTML INTERFACE DIAGNOSTIC TOOL
===============================

This script diagnoses why the monerium_api_tester.html buttons aren't working
by testing the backend connectivity and identifying potential issues.
"""

import requests
import json
import time
from datetime import datetime

def test_backend_connectivity():
    """Test if backend is running and accessible"""
    print("🔍 TESTING BACKEND CONNECTIVITY")
    print("=" * 50)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8006/health", timeout=5)
        if response.ok:
            print("✅ Backend is running on localhost:8006")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running on localhost:8006")
        print("   Solution: Run 'python universal-api-bridge/test_backend.py'")
        return False
    except Exception as e:
        print(f"❌ Backend test failed: {str(e)}")
        return False

def test_cors_headers():
    """Test CORS headers for browser compatibility"""
    print("\n🌐 TESTING CORS CONFIGURATION")
    print("=" * 50)
    
    try:
        # Test OPTIONS request (preflight)
        response = requests.options("http://localhost:8006/api/proxy")
        
        if response.ok:
            headers = response.headers
            print("✅ CORS OPTIONS request successful")
            print(f"   Access-Control-Allow-Origin: {headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
            print(f"   Access-Control-Allow-Methods: {headers.get('Access-Control-Allow-Methods', 'NOT SET')}")
            print(f"   Access-Control-Allow-Headers: {headers.get('Access-Control-Allow-Headers', 'NOT SET')}")
            
            if headers.get('Access-Control-Allow-Origin') == '*':
                print("✅ CORS properly configured for browser access")
                return True
            else:
                print("⚠️  CORS may be restrictive")
                return False
        else:
            print(f"❌ CORS OPTIONS failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ CORS test failed: {str(e)}")
        return False

def test_api_proxy_endpoint():
    """Test the API proxy endpoint that HTML should use"""
    print("\n🔌 TESTING API PROXY ENDPOINT")
    print("=" * 50)
    
    # Test authentication request (same as HTML would send)
    test_request = {
        "method": "POST",
        "endpoint": "/auth/token",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "data": {
            "grant_type": "client_credentials",
            "client_id": "54be063f-6cca-11f0-a3e6-4eb54501c717",
            "client_secret": "71ab65b523e1651fa197ea39ecf2156ed30da3199c668053029860133e0cfdd5"
        },
        "environment": "production"
    }
    
    try:
        response = requests.post(
            "http://localhost:8006/api/proxy",
            headers={"Content-Type": "application/json"},
            json=test_request,
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            if result.get("success") and result.get("data", {}).get("access_token"):
                print("✅ API Proxy working - authentication successful")
                print(f"   Token received: {result['data']['access_token'][:20]}...")
                return True
            else:
                print("❌ API Proxy failed - no token received")
                print(f"   Response: {result}")
                return False
        else:
            print(f"❌ API Proxy HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Proxy test failed: {str(e)}")
        return False

def test_html_interface_compatibility():
    """Test HTML interface specific requirements"""
    print("\n🌍 TESTING HTML INTERFACE COMPATIBILITY")
    print("=" * 50)
    
    # Test with same headers browser would send
    browser_headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "null",  # File:// origin
        "Accept": "application/json, text/plain, */*"
    }
    
    test_request = {
        "method": "GET",
        "endpoint": "/health", 
        "environment": "production"
    }
    
    try:
        response = requests.post(
            "http://localhost:8006/api/proxy",
            headers=browser_headers,
            json=test_request,
            timeout=5
        )
        
        if response.ok:
            print("✅ Browser-like request successful")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"❌ Browser-like request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Browser compatibility test failed: {str(e)}")
        return False

def analyze_potential_issues():
    """Analyze potential issues with HTML interface"""
    print("\n🔍 ANALYZING POTENTIAL ISSUES")
    print("=" * 50)
    
    issues = []
    solutions = []
    
    # Check if backend is running
    if not test_backend_connectivity():
        issues.append("Backend not running")
        solutions.append("Start backend: python universal-api-bridge/test_backend.py")
    
    # Check CORS
    if not test_cors_headers():
        issues.append("CORS configuration issue")
        solutions.append("Backend should have CORS enabled for '*' origin")
    
    # Check API proxy
    if not test_api_proxy_endpoint():
        issues.append("API proxy not working")
        solutions.append("Check backend logs for errors")
    
    # Check browser compatibility
    if not test_html_interface_compatibility():
        issues.append("Browser compatibility issue")
        solutions.append("Check browser console for JavaScript errors")
    
    print(f"\n📊 DIAGNOSIS RESULTS")
    print(f"Issues found: {len(issues)}")
    print(f"Solutions available: {len(solutions)}")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 RECOMMENDED SOLUTIONS:")
        for i, solution in enumerate(solutions, 1):
            print(f"   {i}. {solution}")
    else:
        print("\n✅ NO BACKEND ISSUES FOUND")
        print("The problem is likely in the HTML/JavaScript code.")
        print("\nNext steps:")
        print("1. Open browser developer console (F12)")
        print("2. Check for JavaScript errors")
        print("3. Verify API calls are being made")
        print("4. Check network tab for failed requests")

def main():
    """Run comprehensive HTML interface diagnosis"""
    print("🩺 MONERIUM HTML INTERFACE DIAGNOSTIC")
    print("=" * 60)
    print("Diagnosing why monerium_api_tester.html buttons aren't working...")
    print("=" * 60)
    
    # Run all tests
    backend_ok = test_backend_connectivity()
    cors_ok = test_cors_headers()
    proxy_ok = test_api_proxy_endpoint() 
    browser_ok = test_html_interface_compatibility()
    
    print(f"\n📋 SUMMARY")
    print("=" * 30)
    print(f"Backend Running: {'✅' if backend_ok else '❌'}")
    print(f"CORS Configured: {'✅' if cors_ok else '❌'}")
    print(f"API Proxy Working: {'✅' if proxy_ok else '❌'}")
    print(f"Browser Compatible: {'✅' if browser_ok else '❌'}")
    
    if all([backend_ok, cors_ok, proxy_ok, browser_ok]):
        print(f"\n🎉 BACKEND IS PERFECT!")
        print("The issue is in the HTML/JavaScript frontend.")
        print("Open the HTML file and check browser console for errors.")
    else:
        analyze_potential_issues()

if __name__ == "__main__":
    main() 