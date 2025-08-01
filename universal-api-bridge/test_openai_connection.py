#!/usr/bin/env python3
"""
Test OpenAI Connection with SSL Configuration
"""

import httpx
from openai import OpenAI
import ssl

def test_openai_connection():
    print("🧪 Testing OpenAI Connection with SSL configuration...")
    
    api_key = "YOUR_OPENAI_API_KEY_HERE"
    
    try:
        # Create HTTP client with SSL configuration
        print("🔧 Creating HTTP client with SSL disabled...")
        http_client = httpx.Client(
            verify=False,  # Disable SSL verification
            timeout=30.0
        )
        
        # Initialize OpenAI client
        print("🤖 Initializing OpenAI client...")
        client = OpenAI(
            api_key=api_key,
            http_client=http_client
        )
        
        # Test API call
        print("📡 Making test API call...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello from MCP Gateway!' in one sentence."}],
            max_tokens=50,
            temperature=0.7
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ SUCCESS! OpenAI Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED! Error: {str(e)}")
        return False
    finally:
        # Close HTTP client
        if 'http_client' in locals():
            http_client.close()

if __name__ == "__main__":
    success = test_openai_connection()
    if success:
        print("\n🎉 OpenAI connection test PASSED!")
        print("💡 The MCP Gateway should now work correctly.")
    else:
        print("\n💥 OpenAI connection test FAILED!")
        print("🔍 Check your network/firewall settings.") 
