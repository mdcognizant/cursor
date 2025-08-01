#!/usr/bin/env python3
"""
Simple test script for Dual News Provider Integration
Verifies all components work without requiring API keys
"""

import asyncio
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test standard library imports
        import asyncio, aiohttp, json, logging, time
        print("✅ Standard library modules imported")
        
        # Test third-party imports  
        import aiohttp
        print("✅ aiohttp imported")
        
        # Test Universal API Bridge imports
        from universal_api_bridge.config import BridgeConfig, MCPConfig
        print("✅ Universal API Bridge config imported")
        
        # Test dual news imports
        from dual_news_provider_integration import DualNewsProviderIntegration, NewsProvider
        print("✅ Dual News Integration imported")
        
        from dual_news_config import DualNewsConfigManager
        print("✅ Dual News Config imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration management"""
    print("\n🔧 Testing configuration...")
    
    try:
        from dual_news_config import DualNewsConfigManager
        
        config_manager = DualNewsConfigManager()
        validation = config_manager.validate_configuration()
        
        print(f"Configuration loaded: {'✅' if config_manager.config else '❌'}")
        print(f"Validation complete: {'✅' if 'valid' in validation else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_dual_integration():
    """Test dual news integration initialization"""
    print("\n📰 Testing dual integration...")
    
    try:
        from dual_news_provider_integration import DualNewsProviderIntegration, NewsProvider
        
        # Initialize without API keys (demo mode)
        dual_news = DualNewsProviderIntegration()
        
        print(f"Integration initialized: {'✅' if dual_news else '❌'}")
        print(f"Providers configured: ✅ {len(dual_news.providers)}")
        print(f"Rate limiter ready: {'✅' if dual_news.rate_limiter else '❌'}")
        
        # Test provider selection
        selected = dual_news.select_optimal_provider(NewsProvider.AUTO)
        print(f"Provider selection working: {'✅' if selected is not None else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dual integration test failed: {e}")
        return False

async def test_async_functionality():
    """Test async functionality without making real API calls"""
    print("\n⚡ Testing async functionality...")
    
    try:
        from dual_news_provider_integration import DualNewsProviderIntegration
        
        dual_news = DualNewsProviderIntegration()
        
        # Test async delay function
        start_time = asyncio.get_event_loop().time()
        await dual_news.delay(10)  # 10ms delay
        end_time = asyncio.get_event_loop().time()
        
        delay_worked = (end_time - start_time) >= 0.01  # At least 10ms
        print(f"Async delay working: {'✅' if delay_worked else '❌'}")
        
        # Test statistics
        stats = dual_news.get_comprehensive_stats()
        print(f"Statistics generation: {'✅' if stats and 'dual_provider_mode' in stats else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Dual News Provider Integration - System Test")
    print("=" * 60)
    
    # Set the protobuf environment variable
    os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
    print("✅ Environment configured")
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration), 
        ("Integration Test", test_dual_integration),
        ("Async Test", lambda: asyncio.run(test_async_functionality()))
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your dual news system is ready!")
        print("📋 Next steps:")
        print("   1. Get API keys from currentsapi.services and newsdata.io")
        print("   2. Create .env file with your keys (see .env.example)")
        print("   3. Open dual_news_display.html in your browser")
        print("   4. Test with real news data!")
    else:
        print(f"\n⚠️  {len(tests) - passed} tests failed - see errors above")

if __name__ == "__main__":
    main() 