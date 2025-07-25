#!/usr/bin/env python3
"""Comprehensive test suite for Universal API Bridge validation and error handling."""

import asyncio
import pytest
import logging
import time
import socket
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import the components we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from universal_api_bridge.utils import (
    Validators, HelpfulMessages, ValidationResult, 
    with_retry, format_error_for_user, create_integration_guide
)
from universal_api_bridge.bridge import UniversalBridge
from universal_api_bridge.config import BridgeConfig, create_massive_scale_config
from universal_api_bridge.exceptions import (
    ConfigurationError, ServiceUnavailableError, BridgeError
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestValidators:
    """Test suite for validation functions."""
    
    def test_service_name_validation_valid_names(self):
        """Test valid service names pass validation."""
        valid_names = [
            "user-service",
            "ai-model",
            "order-svc-v2", 
            "api",
            "db-primary",
            "cache_redis",
            "ml_inference_v1"
        ]
        
        for name in valid_names:
            result = Validators.validate_service_name(name)
            assert result.is_valid, f"'{name}' should be valid: {result.errors}"
            print(f"✅ Valid service name: '{name}'")
    
    def test_service_name_validation_invalid_names(self):
        """Test invalid service names fail validation with helpful messages."""
        invalid_cases = [
            ("", "Service name cannot be empty"),
            ("a", "Service name must be at least 2 characters"),
            ("user service", "Service name cannot contain spaces"),
            ("user@service", "contains invalid characters"),
            ("-user-service", "cannot start or end with hyphens"),
            ("user-service-", "cannot start or end with hyphens"),
            ("user.service", "contains invalid characters"),
            ("x" * 64, "must be 63 characters or less")
        ]
        
        for name, expected_error_fragment in invalid_cases:
            result = Validators.validate_service_name(name)
            assert not result.is_valid, f"'{name}' should be invalid"
            
            error_found = any(expected_error_fragment.lower() in error.lower() 
                            for error in result.errors)
            assert error_found, f"Expected error containing '{expected_error_fragment}' for '{name}', got: {result.errors}"
            
            # Check that suggestions are provided
            assert len(result.suggestions) > 0, f"Should provide suggestions for '{name}'"
            print(f"❌ Invalid service name: '{name}' - {result.errors[0]}")
            print(f"💡 Suggestion: {result.suggestions[0]}")
    
    def test_endpoint_validation_valid_endpoints(self):
        """Test valid endpoints pass validation."""
        valid_endpoints = [
            "localhost:50051",
            "127.0.0.1:8080",
            "api-server:9000",
            "db.example.com:5432",
            "redis-cluster:6379"
        ]
        
        for endpoint in valid_endpoints:
            result = Validators.validate_endpoint(endpoint)
            assert result.is_valid, f"'{endpoint}' should be valid: {result.errors}"
            print(f"✅ Valid endpoint: '{endpoint}'")
    
    def test_endpoint_validation_invalid_endpoints(self):
        """Test invalid endpoints fail validation with helpful messages."""
        invalid_cases = [
            ("", "Endpoint cannot be empty"),
            ("localhost", "missing port number"), 
            ("localhost:abc", "Invalid port number"),
            ("localhost:0", "out of valid range"),
            ("localhost:99999", "out of valid range"),
            (":50051", "Host cannot be empty")
        ]
        
        for endpoint, expected_error_fragment in invalid_cases:
            result = Validators.validate_endpoint(endpoint)
            assert not result.is_valid, f"'{endpoint}' should be invalid"
            
            error_found = any(expected_error_fragment.lower() in error.lower() 
                            for error in result.errors)
            assert error_found, f"Expected error containing '{expected_error_fragment}' for '{endpoint}', got: {result.errors}"
            
            print(f"❌ Invalid endpoint: '{endpoint}' - {result.errors[0]}")
    
    def test_endpoint_connectivity_test(self):
        """Test endpoint connectivity testing."""
        # Test with a non-existent endpoint
        result = Validators.validate_endpoint_connectivity("nonexistent-host:50051", timeout=1.0)
        assert not result.is_valid, "Connection to non-existent host should fail"
        assert len(result.errors) > 0, "Should have connection errors"
        print(f"❌ Expected connection failure: {result.errors[0]}")
        
        # Test with invalid port
        result = Validators.validate_endpoint_connectivity("localhost:99999", timeout=1.0)
        assert not result.is_valid, "Connection to invalid port should fail"
        print(f"❌ Expected port connection failure: {result.errors[0]}")


class TestHelpfulMessages:
    """Test suite for helpful message generation."""
    
    def test_service_registration_help(self):
        """Test service registration help messages."""
        help_info = HelpfulMessages.service_registration_help("invalid-service@name")
        
        assert "issue" in help_info
        assert "common_causes" in help_info
        assert "solutions" in help_info
        assert "examples" in help_info
        assert "code_example" in help_info
        
        assert len(help_info["common_causes"]) > 0
        assert len(help_info["solutions"]) > 0
        assert "valid_names" in help_info["examples"]
        assert "invalid_names" in help_info["examples"]
        
        print(f"📚 Service registration help generated: {len(help_info['solutions'])} solutions")
    
    def test_connection_help(self):
        """Test connection help messages."""
        help_info = HelpfulMessages.connection_help("localhost:50051", "Connection refused")
        
        assert "issue" in help_info
        assert "troubleshooting_steps" in help_info
        assert "diagnostic_commands" in help_info
        assert "common_fixes" in help_info
        
        assert len(help_info["troubleshooting_steps"]) > 0
        assert len(help_info["diagnostic_commands"]) > 0
        assert "connection_refused" in help_info["common_fixes"]
        
        print(f"🔧 Connection help generated: {len(help_info['troubleshooting_steps'])} steps")
    
    def test_performance_help(self):
        """Test performance help messages."""
        help_info = HelpfulMessages.performance_help("latency", 100.0, 10.0)
        
        assert "issue" in help_info
        assert "optimization_tips" in help_info
        assert "configuration_suggestions" in help_info
        assert help_info["impact"] in ["High", "Medium", "Low"]
        
        print(f"⚡ Performance help generated for high latency")


class TestErrorFormatting:
    """Test suite for error formatting."""
    
    def test_error_formatting_connection_error(self):
        """Test formatting of connection errors."""
        error = ConnectionError("Connection to localhost:50051 failed")
        formatted = format_error_for_user(error, "testing connection")
        
        assert "error" in formatted
        assert "debug" in formatted
        assert "type" in formatted["error"]
        assert "troubleshooting" in formatted["error"]
        
        troubleshooting = formatted["error"]["troubleshooting"]
        assert len(troubleshooting["common_causes"]) > 0
        assert len(troubleshooting["solutions"]) > 0
        assert troubleshooting["documentation"] is not None
        
        print(f"🔧 Connection error formatted with {len(troubleshooting['solutions'])} solutions")
    
    def test_error_formatting_timeout_error(self):
        """Test formatting of timeout errors."""
        error = TimeoutError("Operation timed out after 30 seconds")
        formatted = format_error_for_user(error, "making API request")
        
        troubleshooting = formatted["error"]["troubleshooting"]
        assert any("timeout" in cause.lower() for cause in troubleshooting["common_causes"])
        assert any("timeout" in solution.lower() for solution in troubleshooting["solutions"])
        
        print(f"⏱️ Timeout error formatted with helpful suggestions")


class TestRetryDecorator:
    """Test suite for retry decorator."""
    
    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """Test retry decorator with async function that succeeds."""
        call_count = 0
        
        @with_retry(max_retries=3, delay=0.01)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 1
        print("✅ Async retry test passed on first attempt")
    
    @pytest.mark.asyncio
    async def test_async_retry_eventual_success(self):
        """Test retry decorator with async function that succeeds after retries."""
        call_count = 0
        
        @with_retry(max_retries=3, delay=0.01)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError(f"Attempt {call_count} failed")
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 3
        print(f"✅ Async retry test succeeded after {call_count} attempts")
    
    @pytest.mark.asyncio
    async def test_async_retry_max_retries_exceeded(self):
        """Test retry decorator when max retries are exceeded."""
        call_count = 0
        
        @with_retry(max_retries=2, delay=0.01)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError(f"Attempt {call_count} failed")
        
        with pytest.raises(ConnectionError):
            await test_function()
        
        assert call_count == 3  # Initial attempt + 2 retries
        print(f"❌ Async retry test failed after {call_count} attempts (expected)")


class TestBridgeValidation:
    """Test suite for Universal Bridge validation."""
    
    @pytest.mark.asyncio
    async def test_service_registration_validation(self):
        """Test service registration with various inputs."""
        
        # Create bridge with test configuration
        config = BridgeConfig()
        config.mcp.max_services = 10
        bridge = UniversalBridge(config)
        
        # Test valid service registration
        result = bridge.register_service("test-service", "localhost:50051")
        assert result["success"] is True
        assert result["service_name"] == "test-service"
        assert result["endpoint"] == "localhost:50051"
        assert "integration_guide" in result
        assert "next_steps" in result
        print(f"✅ Valid service registration: {result['service_name']}")
        
        # Test invalid service name
        with pytest.raises(ConfigurationError) as exc_info:
            bridge.register_service("invalid service name", "localhost:50051")
        
        error = exc_info.value
        assert "space" in str(error).lower() or "invalid" in str(error).lower()
        print(f"❌ Invalid service name rejected: {error}")
        
        # Test invalid endpoint
        with pytest.raises(ConfigurationError) as exc_info:
            bridge.register_service("test-service2", "invalid-endpoint")
        
        error = exc_info.value
        assert "port" in str(error).lower() or "endpoint" in str(error).lower()
        print(f"❌ Invalid endpoint rejected: {error}")
    
    @pytest.mark.asyncio
    async def test_service_limit_validation(self):
        """Test service registration limit validation."""
        
        # Create bridge with low service limit
        config = BridgeConfig()
        config.mcp.max_services = 2
        bridge = UniversalBridge(config)
        
        # Register services up to limit
        bridge.register_service("service1", "localhost:50051")
        bridge.register_service("service2", "localhost:50052")
        
        # Try to register beyond limit
        with pytest.raises(ServiceUnavailableError) as exc_info:
            bridge.register_service("service3", "localhost:50053")
        
        error = exc_info.value
        assert "maximum" in str(error).lower() or "limit" in str(error).lower()
        print(f"❌ Service limit enforced: {error}")
    
    @pytest.mark.asyncio
    async def test_massive_scale_configuration(self):
        """Test massive scale configuration validation."""
        
        # Test creating massive scale config
        config = create_massive_scale_config(10000)
        
        assert config.mcp.max_services == 10000
        assert config.frontend.max_connections >= 100000
        assert config.performance.enable_aggressive_caching is True
        
        # Test validation
        issues = config.validate_massive_scale()
        # Should have no critical issues for 10K services
        critical_issues = [issue for issue in issues if "critical" in issue.lower()]
        assert len(critical_issues) == 0, f"Critical issues found: {critical_issues}"
        
        print(f"✅ Massive scale config validated for {config.mcp.max_services} services")


class TestIntegrationGuide:
    """Test suite for integration guide generation."""
    
    def test_integration_guide_generation(self):
        """Test integration guide generation."""
        guide = create_integration_guide("user-service", "localhost:50051")
        
        assert "service" in guide
        assert "endpoint" in guide
        assert "integration_steps" in guide
        assert "example_calls" in guide
        assert "tips" in guide
        
        assert guide["service"] == "user-service"
        assert guide["endpoint"] == "localhost:50051"
        assert len(guide["integration_steps"]) >= 3
        assert len(guide["example_calls"]) >= 2
        assert len(guide["tips"]) >= 3
        
        # Check step structure
        for step in guide["integration_steps"]:
            assert "step" in step
            assert "title" in step
            assert "code" in step
            assert "description" in step
        
        print(f"📚 Integration guide generated with {len(guide['integration_steps'])} steps")


async def run_comprehensive_validation_tests():
    """Run all validation tests."""
    print("🧪 Starting Comprehensive Validation Test Suite")
    print("=" * 60)
    
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    # Test categories
    test_classes = [
        TestValidators(),
        TestHelpfulMessages(),
        TestErrorFormatting(),
        TestRetryDecorator(),
        TestBridgeValidation(),
        TestIntegrationGuide()
    ]
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n🔍 Running {class_name} tests...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_') and callable(getattr(test_class, method))]
        
        for method_name in test_methods:
            test_results["total_tests"] += 1
            test_method = getattr(test_class, method_name)
            
            try:
                start_time = time.time()
                
                # Run async tests with asyncio
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()
                
                execution_time = (time.time() - start_time) * 1000
                test_results["passed_tests"] += 1
                
                test_results["test_details"].append({
                    "class": class_name,
                    "method": method_name,
                    "status": "PASSED",
                    "execution_time_ms": execution_time
                })
                
                print(f"  ✅ {method_name} ({execution_time:.1f}ms)")
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                test_results["failed_tests"] += 1
                
                test_results["test_details"].append({
                    "class": class_name,
                    "method": method_name,
                    "status": "FAILED",
                    "execution_time_ms": execution_time,
                    "error": str(e)
                })
                
                print(f"  ❌ {method_name} - {e}")
    
    # Print test summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed_tests']} ✅")
    print(f"Failed: {test_results['failed_tests']} ❌")
    print(f"Success Rate: {(test_results['passed_tests'] / test_results['total_tests']) * 100:.1f}%")
    
    # Show failed tests if any
    if test_results["failed_tests"] > 0:
        print(f"\n❌ Failed Tests:")
        for test in test_results["test_details"]:
            if test["status"] == "FAILED":
                print(f"  • {test['class']}.{test['method']}: {test.get('error', 'Unknown error')}")
    
    # Show performance summary
    total_time = sum(test["execution_time_ms"] for test in test_results["test_details"])
    avg_time = total_time / len(test_results["test_details"]) if test_results["test_details"] else 0
    
    print(f"\n⚡ Performance Summary:")
    print(f"Total execution time: {total_time:.1f}ms")
    print(f"Average test time: {avg_time:.1f}ms")
    
    fastest_test = min(test_results["test_details"], key=lambda x: x["execution_time_ms"])
    slowest_test = max(test_results["test_details"], key=lambda x: x["execution_time_ms"])
    
    print(f"Fastest test: {fastest_test['method']} ({fastest_test['execution_time_ms']:.1f}ms)")
    print(f"Slowest test: {slowest_test['method']} ({slowest_test['execution_time_ms']:.1f}ms)")
    
    return test_results


async def main():
    """Main test runner."""
    try:
        print("🌟 Universal API Bridge - Comprehensive Validation Test Suite")
        print("Testing error handling, validation, and helpful messages")
        print()
        
        results = await run_comprehensive_validation_tests()
        
        # Exit with appropriate code
        if results["failed_tests"] == 0:
            print("\n🎉 All tests passed! The Universal API Bridge validation system is working correctly.")
            return 0
        else:
            print(f"\n⚠️ {results['failed_tests']} tests failed. Please review and fix issues.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main()) 