#!/usr/bin/env python3
"""Simple validation test for Universal API Bridge error handling and helpful messages."""

import sys
import os
import time
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_validators():
    """Test the validation functions."""
    print("🧪 Testing Validation Functions")
    print("-" * 40)
    
    try:
        from universal_api_bridge.utils import Validators
        
        # Test valid service names
        valid_names = ["user-service", "ai-model", "api", "db-cache"]
        for name in valid_names:
            result = Validators.validate_service_name(name)
            assert result.is_valid, f"'{name}' should be valid"
            print(f"✅ Valid service name: '{name}'")
        
        # Test invalid service names  
        invalid_names = ["", "user service", "user@service", "-invalid"]
        for name in invalid_names:
            result = Validators.validate_service_name(name)
            assert not result.is_valid, f"'{name}' should be invalid"
            print(f"❌ Invalid service name: '{name}' - {result.errors[0]}")
            if result.suggestions:
                print(f"💡 Suggestion: {result.suggestions[0]}")
        
        # Test valid endpoints
        valid_endpoints = ["localhost:50051", "127.0.0.1:8080", "api-server:9000"]
        for endpoint in valid_endpoints:
            result = Validators.validate_endpoint(endpoint)
            assert result.is_valid, f"'{endpoint}' should be valid"
            print(f"✅ Valid endpoint: '{endpoint}'")
        
        # Test invalid endpoints
        invalid_endpoints = ["", "localhost", "localhost:abc", ":50051"]
        for endpoint in invalid_endpoints:
            result = Validators.validate_endpoint(endpoint)
            assert not result.is_valid, f"'{endpoint}' should be invalid"
            print(f"❌ Invalid endpoint: '{endpoint}' - {result.errors[0]}")
        
        print("✅ All validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def test_helpful_messages():
    """Test the helpful message generation."""
    print("\n🧪 Testing Helpful Messages")
    print("-" * 40)
    
    try:
        from universal_api_bridge.utils import HelpfulMessages
        
        # Test service registration help
        help_info = HelpfulMessages.service_registration_help("invalid@service")
        assert "common_causes" in help_info
        assert "solutions" in help_info
        assert "examples" in help_info
        assert len(help_info["solutions"]) > 0
        print(f"✅ Service registration help: {len(help_info['solutions'])} solutions provided")
        
        # Test connection help
        conn_help = HelpfulMessages.connection_help("localhost:50051", "Connection refused")
        assert "troubleshooting_steps" in conn_help
        assert "diagnostic_commands" in conn_help
        assert len(conn_help["troubleshooting_steps"]) > 0
        print(f"✅ Connection help: {len(conn_help['troubleshooting_steps'])} troubleshooting steps")
        
        # Test performance help
        perf_help = HelpfulMessages.performance_help("latency", 100.0, 10.0)
        assert "optimization_tips" in perf_help
        assert "configuration_suggestions" in perf_help
        assert perf_help["impact"] in ["High", "Medium", "Low"]
        print(f"✅ Performance help: Impact level '{perf_help['impact']}' detected")
        
        print("✅ All helpful message tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Helpful message test failed: {e}")
        return False


def test_error_formatting():
    """Test error formatting for users."""
    print("\n🧪 Testing Error Formatting")
    print("-" * 40)
    
    try:
        from universal_api_bridge.utils import format_error_for_user
        
        # Test connection error formatting
        error = ConnectionError("Connection to localhost:50051 failed")
        formatted = format_error_for_user(error, "testing connection")
        
        assert "error" in formatted
        assert "troubleshooting" in formatted["error"]
        assert len(formatted["error"]["troubleshooting"]["solutions"]) > 0
        print(f"✅ Connection error formatted with {len(formatted['error']['troubleshooting']['solutions'])} solutions")
        
        # Test timeout error formatting  
        error = TimeoutError("Operation timed out after 30 seconds")
        formatted = format_error_for_user(error, "making API request")
        
        solutions = formatted["error"]["troubleshooting"]["solutions"]
        timeout_solution_found = any("timeout" in solution.lower() for solution in solutions)
        assert timeout_solution_found, "Should provide timeout-specific solutions"
        print("✅ Timeout error formatted with timeout-specific solutions")
        
        print("✅ All error formatting tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error formatting test failed: {e}")
        return False


def test_integration_guide():
    """Test integration guide generation."""
    print("\n🧪 Testing Integration Guide")
    print("-" * 40)
    
    try:
        from universal_api_bridge.utils import create_integration_guide
        
        guide = create_integration_guide("user-service", "localhost:50051")
        
        assert "service" in guide
        assert "integration_steps" in guide
        assert "example_calls" in guide
        assert "tips" in guide
        
        assert guide["service"] == "user-service"
        assert len(guide["integration_steps"]) >= 3
        assert len(guide["tips"]) >= 3
        
        print(f"✅ Integration guide generated with {len(guide['integration_steps'])} steps")
        print(f"   📋 First step: {guide['integration_steps'][0]['title']}")
        print(f"   💡 First tip: {guide['tips'][0]}")
        
        print("✅ Integration guide test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration guide test failed: {e}")
        return False


async def test_bridge_basic_functionality():
    """Test basic bridge functionality with validation."""
    print("\n🧪 Testing Bridge Basic Functionality")
    print("-" * 40)
    
    try:
        from universal_api_bridge import UniversalBridge, BridgeConfig
        from universal_api_bridge.exceptions import ConfigurationError
        
        # Create bridge with test configuration
        config = BridgeConfig()
        config.mcp.max_services = 5
        bridge = UniversalBridge(config)
        
        # Test valid service registration
        result = bridge.register_service("test-service", "localhost:50051")
        assert result["success"] is True
        assert result["service_name"] == "test-service"
        assert "integration_guide" in result
        print(f"✅ Valid service registered: {result['service_name']}")
        print(f"   📊 Service count: {result['service_count']}/{result['max_services']}")
        print(f"   🔗 Connectivity: {result['connectivity_status']}")
        
        # Test invalid service name
        try:
            bridge.register_service("invalid service name", "localhost:50051")
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError as e:
            print(f"❌ Invalid service name properly rejected: {str(e)[:60]}...")
        
        # Test invalid endpoint
        try:
            bridge.register_service("test-service-2", "invalid-endpoint")
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError as e:
            print(f"❌ Invalid endpoint properly rejected: {str(e)[:60]}...")
        
        print("✅ Bridge basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Bridge functionality test failed: {e}")
        return False


def test_configuration_validation():
    """Test configuration validation."""
    print("\n🧪 Testing Configuration Validation")
    print("-" * 40)
    
    try:
        from universal_api_bridge.config import create_massive_scale_config
        
        # Test massive scale configuration
        config = create_massive_scale_config(10000)
        
        assert config.mcp.max_services == 10000
        assert config.frontend.max_connections >= 100000
        assert config.performance.enable_aggressive_caching is True
        print(f"✅ Massive scale config created for {config.mcp.max_services:,} services")
        print(f"   🔗 Max connections: {config.frontend.max_connections:,}")
        print(f"   ⚡ Performance mode: {config.performance.enable_aggressive_caching}")
        
        # Test validation
        issues = config.validate_massive_scale()
        print(f"   ⚠️ Configuration issues: {len(issues)}")
        
        for issue in issues[:3]:  # Show first 3 issues
            print(f"      • {issue}")
        
        print("✅ Configuration validation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


async def run_all_tests():
    """Run all validation tests."""
    print("🌟 Universal API Bridge - Validation Test Suite")
    print("Testing error handling, validation, and helpful messages")
    print("=" * 70)
    
    start_time = time.time()
    test_results = []
    
    # Run all tests
    tests = [
        ("Validators", test_validators),
        ("Helpful Messages", test_helpful_messages),
        ("Error Formatting", test_error_formatting),
        ("Integration Guide", test_integration_guide),
        ("Bridge Functionality", test_bridge_basic_functionality),
        ("Configuration Validation", test_configuration_validation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        test_start = time.time()
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            test_time = time.time() - test_start
            
            if success:
                passed_tests += 1
                status = "PASSED"
                print(f"✅ {test_name} test completed in {test_time*1000:.1f}ms")
            else:
                status = "FAILED"
                print(f"❌ {test_name} test failed in {test_time*1000:.1f}ms")
            
            test_results.append({
                "name": test_name,
                "status": status,
                "time_ms": test_time * 1000
            })
            
        except Exception as e:
            test_time = time.time() - test_start
            print(f"❌ {test_name} test crashed in {test_time*1000:.1f}ms: {e}")
            test_results.append({
                "name": test_name,
                "status": "CRASHED",
                "time_ms": test_time * 1000,
                "error": str(e)
            })
    
    # Print summary
    total_time = time.time() - start_time
    success_rate = (passed_tests / total_tests) * 100
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {total_tests - passed_tests} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Time: {total_time*1000:.1f}ms")
    
    # Show individual test results
    print(f"\n📋 Detailed Results:")
    for result in test_results:
        status_emoji = {"PASSED": "✅", "FAILED": "❌", "CRASHED": "💥"}[result["status"]]
        print(f"   {status_emoji} {result['name']}: {result['status']} ({result['time_ms']:.1f}ms)")
        if "error" in result:
            print(f"      Error: {result['error'][:60]}...")
    
    # Final verdict
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Universal API Bridge validation system is working correctly.")
        print("   • Comprehensive error handling ✅")
        print("   • Helpful validation messages ✅") 
        print("   • User-friendly error formatting ✅")
        print("   • Integration guidance ✅")
        print("   • Configuration validation ✅")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed. Please review and fix issues.")
        return False


async def main():
    """Main test runner."""
    try:
        success = await run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 