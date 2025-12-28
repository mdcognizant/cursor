#!/usr/bin/env python3
"""
Comprehensive API Error Debugging Script
Tests both NewsData.io and Currents API for errors and provides detailed diagnostics
"""

import requests
import json
import time
from datetime import datetime
import traceback

# API Configuration
NEWSDATA_API_KEY = "pub_05c05ef3d5044b3fa7a3ab3b04d479e4"
CURRENTS_API_KEY = "zWhKbzWClaobXOpN0VDGF62kNkBh6Kbgdx-ki2AUIEoAGnah"

NEWSDATA_ENDPOINT = "https://newsdata.io/api/1/latest"
CURRENTS_ENDPOINT = "https://api.currentsapi.services/v1/latest-news"

def test_newsdata_api():
    """Test NewsData.io API and identify specific errors"""
    print("🔍 TESTING NEWSDATA.IO API")
    print("=" * 50)
    
    try:
        # Test basic endpoint
        url = f"{NEWSDATA_ENDPOINT}?apikey={NEWSDATA_API_KEY}&language=en&size=5"
        print(f"📞 Testing URL: {url.replace(NEWSDATA_API_KEY, 'API_KEY_HIDDEN')}")
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        print(f"⏱️ Response Time: {response_time:.2f}ms")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Got {len(data.get('results', []))} articles")
            print(f"📰 Total Available: {data.get('totalResults', 'N/A')}")
            print(f"🔄 Next Page: {data.get('nextPage', 'N/A')}")
            
            # Test first article structure
            if data.get('results'):
                article = data['results'][0]
                print(f"📄 Sample Article:")
                print(f"   Title: {article.get('title', 'N/A')[:50]}...")
                print(f"   Source: {article.get('source_id', 'N/A')}")
                print(f"   Image: {article.get('image_url', 'N/A')}")
                print(f"   Published: {article.get('pubDate', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ ERROR - Status {response.status_code}")
            print(f"📝 Response Text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ ERROR: Request timeout (>30 seconds)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"🌐 CONNECTION ERROR: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🚫 REQUEST ERROR: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"📄 JSON DECODE ERROR: {e}")
        print(f"📝 Raw Response: {response.text[:200]}")
        return False
    except Exception as e:
        print(f"💥 UNEXPECTED ERROR: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def test_currents_api():
    """Test Currents API and identify specific errors"""
    print("\n🔍 TESTING CURRENTS API")
    print("=" * 50)
    
    try:
        # Test basic endpoint
        url = f"{CURRENTS_ENDPOINT}?apiKey={CURRENTS_API_KEY}&language=en&limit=5"
        print(f"📞 Testing URL: {url.replace(CURRENTS_API_KEY, 'API_KEY_HIDDEN')}")
        
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        print(f"⏱️ Response Time: {response_time:.2f}ms")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Got {len(data.get('news', []))} articles")
            print(f"📄 Status: {data.get('status', 'N/A')}")
            
            # Test first article structure
            if data.get('news'):
                article = data['news'][0]
                print(f"📄 Sample Article:")
                print(f"   Title: {article.get('title', 'N/A')[:50]}...")
                print(f"   Source: {article.get('author', 'N/A')}")
                print(f"   Image: {article.get('image', 'N/A')}")
                print(f"   Published: {article.get('published', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ ERROR - Status {response.status_code}")
            print(f"📝 Response Text: {response.text}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"🔒 SSL ERROR: {e}")
        print("💡 This is a known issue with Currents API SSL certificates")
        return False
    except requests.exceptions.Timeout:
        print("⏰ ERROR: Request timeout (>30 seconds)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"🌐 CONNECTION ERROR: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🚫 REQUEST ERROR: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"📄 JSON DECODE ERROR: {e}")
        print(f"📝 Raw Response: {response.text[:200]}")
        return False
    except Exception as e:
        print(f"💥 UNEXPECTED ERROR: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def test_rate_limits():
    """Test for rate limiting issues"""
    print("\n🚦 TESTING RATE LIMITS")
    print("=" * 50)
    
    print("📊 Testing NewsData.io rate limits...")
    for i in range(3):
        print(f"   Request {i+1}/3...")
        url = f"{NEWSDATA_ENDPOINT}?apikey={NEWSDATA_API_KEY}&language=en&size=1"
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code} | Headers: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
        except Exception as e:
            print(f"   Error: {e}")
        time.sleep(1)

def test_browser_compatibility():
    """Test CORS and browser compatibility issues"""
    print("\n🌐 TESTING BROWSER COMPATIBILITY")
    print("=" * 50)
    
    # Test with browser-like headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site'
    }
    
    print("🔍 Testing with browser headers...")
    url = f"{NEWSDATA_ENDPOINT}?apikey={NEWSDATA_API_KEY}&language=en&size=1"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ Browser-like request: {response.status_code}")
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        print(f"🌐 CORS Headers: {cors_headers}")
        
    except Exception as e:
        print(f"❌ Browser compatibility issue: {e}")

def generate_error_report():
    """Generate comprehensive error report"""
    print("\n📋 GENERATING COMPREHENSIVE ERROR REPORT")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'newsdata_test': test_newsdata_api(),
        'currents_test': test_currents_api(),
        'environment': {
            'python_version': requests.__version__,
            'requests_version': requests.__version__
        }
    }
    
    # Test rate limits
    test_rate_limits()
    
    # Test browser compatibility
    test_browser_compatibility()
    
    print(f"\n📊 FINAL REPORT")
    print("=" * 30)
    print(f"✅ NewsData.io Working: {report['newsdata_test']}")
    print(f"✅ Currents API Working: {report['currents_test']}")
    
    if not report['newsdata_test'] and not report['currents_test']:
        print("🚨 CRITICAL: Both APIs are failing!")
        print("💡 Recommendations:")
        print("   1. Check internet connection")
        print("   2. Verify API keys are still valid")
        print("   3. Check if you've exceeded daily limits")
        print("   4. Try again in a few minutes")
    elif not report['newsdata_test']:
        print("⚠️ WARNING: NewsData.io is failing")
        print("💡 Using Currents API as fallback")
    elif not report['currents_test']:
        print("⚠️ INFO: Currents API has known SSL issues")
        print("💡 NewsData.io is working fine")
    else:
        print("🎉 SUCCESS: Both APIs are working!")
    
    # Save report
    with open('api_error_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: api_error_report.json")

if __name__ == "__main__":
    print("🔧 COMPREHENSIVE API ERROR DEBUGGING")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    
    generate_error_report()
    
    print(f"\n✅ Debugging complete!") 