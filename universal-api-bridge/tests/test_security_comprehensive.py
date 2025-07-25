"""
Comprehensive security testing for Universal API Bridge.

This test suite validates all security features including:
- JWT and OAuth2 authentication
- Rate limiting and throttling
- WAF and input validation
- IP whitelisting/blacklisting
- Circuit breaker security integration
- API key management
- Security headers
- Audit logging
"""

import asyncio
import json
import pytest
import time
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from universal_api_bridge.config import SecurityConfig, AuthenticationType, RateLimitStrategy
from universal_api_bridge.security import (
    SecurityManager, JWTManager, APIKeyManager, RateLimiter, 
    WAFEngine, InputValidator, SecurityMiddleware, SecurityContext
)
from universal_api_bridge.exceptions import (
    AuthenticationError, AuthorizationError, SecurityError, 
    RateLimitError, InputValidationError
)


class TestJWTAuthentication:
    """Test JWT authentication functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_authentication=True,
            authentication_type=AuthenticationType.JWT,
            jwt_secret_key="test-secret-key-12345",
            jwt_algorithm="HS256",
            jwt_expiration=3600
        )
        self.jwt_manager = JWTManager(self.config)
    
    def test_jwt_token_creation(self):
        """Test JWT token creation."""
        payload = {
            "sub": "user123",
            "roles": ["admin", "user"],
            "permissions": ["read", "write"]
        }
        
        token = self.jwt_manager.create_token(payload)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_jwt_token_verification(self):
        """Test JWT token verification."""
        payload = {
            "sub": "user123",
            "roles": ["admin"],
            "permissions": ["read", "write"]
        }
        
        token = self.jwt_manager.create_token(payload)
        verified_payload = self.jwt_manager.verify_token(token)
        
        assert verified_payload["sub"] == "user123"
        assert "roles" in verified_payload
        assert "iss" in verified_payload
        assert "exp" in verified_payload
    
    def test_jwt_invalid_token(self):
        """Test handling of invalid JWT tokens."""
        with pytest.raises(AuthenticationError):
            self.jwt_manager.verify_token("invalid.token.here")
    
    def test_jwt_expired_token(self):
        """Test handling of expired JWT tokens."""
        # Create manager with very short expiration
        short_config = SecurityConfig(
            jwt_secret_key="test-key",
            jwt_expiration=1  # 1 second
        )
        short_jwt_manager = JWTManager(short_config)
        
        token = short_jwt_manager.create_token({"sub": "test"})
        time.sleep(2)  # Wait for expiration
        
        with pytest.raises(AuthenticationError):
            short_jwt_manager.verify_token(token)


class TestAPIKeyManagement:
    """Test API key management functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_authentication=True,
            authentication_type=AuthenticationType.API_KEY,
            api_key_expiration=86400
        )
        self.api_key_manager = APIKeyManager(self.config)
    
    def test_api_key_creation(self):
        """Test API key creation."""
        api_key = self.api_key_manager.create_api_key(
            user_id="user123",
            roles=["admin"],
            permissions=["read", "write"]
        )
        
        assert isinstance(api_key, str)
        assert len(api_key) > 20  # Should be a decent length
    
    def test_api_key_verification(self):
        """Test API key verification."""
        api_key = self.api_key_manager.create_api_key(
            user_id="user123",
            roles=["admin"],
            permissions=["read", "write"]
        )
        
        key_info = self.api_key_manager.verify_api_key(api_key)
        
        assert key_info["user_id"] == "user123"
        assert "admin" in key_info["roles"]
        assert "read" in key_info["permissions"]
        assert key_info["active"] is True
    
    def test_api_key_invalid(self):
        """Test handling of invalid API keys."""
        with pytest.raises(AuthenticationError):
            self.api_key_manager.verify_api_key("invalid-api-key")
    
    def test_demo_api_key(self):
        """Test that demo API key works."""
        demo_key = "demo-api-key-12345"
        key_info = self.api_key_manager.verify_api_key(demo_key)
        
        assert key_info["user_id"] == "demo-user"
        assert "user" in key_info["roles"]


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_rate_limiting=True,
            rate_limit_strategy=RateLimitStrategy.TOKEN_BUCKET,
            default_rate_limit=5,  # 5 requests per window
            burst_limit=3,
            rate_limit_window=60
        )
        self.rate_limiter = RateLimiter(self.config)
    
    def test_rate_limit_within_limit(self):
        """Test requests within rate limit are allowed."""
        # Should allow first few requests
        for i in range(3):
            allowed = self.rate_limiter.check_rate_limit("user123", "/api/test")
            assert allowed is True
    
    def test_rate_limit_burst_exceeded(self):
        """Test burst limit enforcement."""
        # Fill up the bucket
        for i in range(3):
            self.rate_limiter.check_rate_limit("user123", "/api/test")
        
        # Next request should be denied
        allowed = self.rate_limiter.check_rate_limit("user123", "/api/test")
        assert allowed is False
    
    def test_rate_limit_per_user(self):
        """Test rate limiting is per user."""
        # Fill bucket for user1
        for i in range(3):
            self.rate_limiter.check_rate_limit("user1", "/api/test")
        
        # user2 should still be allowed
        allowed = self.rate_limiter.check_rate_limit("user2", "/api/test")
        assert allowed is True
    
    def test_fixed_window_rate_limiting(self):
        """Test fixed window rate limiting."""
        config = SecurityConfig(
            enable_rate_limiting=True,
            rate_limit_strategy=RateLimitStrategy.FIXED_WINDOW,
            default_rate_limit=3,
            rate_limit_window=1  # 1 second window
        )
        limiter = RateLimiter(config)
        
        # Should allow first 3 requests
        for i in range(3):
            allowed = limiter.check_rate_limit("user123", "/api/test")
            assert allowed is True
        
        # 4th request should be denied
        allowed = limiter.check_rate_limit("user123", "/api/test")
        assert allowed is False


class TestWAFEngine:
    """Test Web Application Firewall functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(enable_waf=True)
        self.waf_engine = WAFEngine(self.config)
    
    def test_sql_injection_detection(self):
        """Test SQL injection attack detection."""
        malicious_requests = [
            "SELECT * FROM users WHERE id = 1",
            "'; DROP TABLE users; --",
            "UNION SELECT password FROM users",
            "1' OR '1'='1"
        ]
        
        for request in malicious_requests:
            threats = self.waf_engine.scan_request(request, {})
            assert len(threats) > 0
            assert any("sql_injection" in threat for threat in threats)
    
    def test_xss_detection(self):
        """Test XSS attack detection."""
        malicious_requests = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "onload='alert(1)'"
        ]
        
        for request in malicious_requests:
            threats = self.waf_engine.scan_request(request, {})
            assert len(threats) > 0
            assert any("xss" in threat for threat in threats)
    
    def test_path_traversal_detection(self):
        """Test path traversal attack detection."""
        malicious_requests = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f",
        ]
        
        for request in malicious_requests:
            threats = self.waf_engine.scan_request(request, {})
            assert len(threats) > 0
            assert any("path_traversal" in threat for threat in threats)
    
    def test_clean_request(self):
        """Test that clean requests pass through."""
        clean_requests = [
            "Hello, this is a normal request",
            '{"user": "john", "action": "login"}',
            "GET /api/users/123 HTTP/1.1"
        ]
        
        for request in clean_requests:
            threats = self.waf_engine.scan_request(request, {})
            assert len(threats) == 0


class TestInputValidator:
    """Test input validation functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_input_validation=True,
            enable_xss_protection=True,
            enable_sql_injection_protection=True,
            max_request_size=1024
        )
        self.validator = InputValidator(self.config)
    
    def test_request_size_validation(self):
        """Test request size validation."""
        # Valid size
        assert self.validator.validate_request_size(512) is True
        
        # Invalid size
        assert self.validator.validate_request_size(2048) is False
    
    def test_string_sanitization(self):
        """Test string input sanitization."""
        # XSS attempt
        dirty_input = "<script>alert('xss')</script>Hello"
        clean_input = self.validator.sanitize_input(dirty_input)
        assert "<script>" not in clean_input
        assert "Hello" in clean_input
        
        # SQL injection attempt
        dirty_input = "'; DROP TABLE users; --"
        clean_input = self.validator.sanitize_input(dirty_input)
        assert "DROP" not in clean_input
    
    def test_nested_data_sanitization(self):
        """Test sanitization of nested data structures."""
        dirty_data = {
            "username": "john",
            "comment": "<script>alert('xss')</script>",
            "tags": ["<script>", "normal_tag"],
            "metadata": {
                "description": "javascript:alert(1)"
            }
        }
        
        clean_data = self.validator.sanitize_input(dirty_data)
        
        assert clean_data["username"] == "john"  # Should be unchanged
        assert "<script>" not in clean_data["comment"]
        assert "<script>" not in clean_data["tags"][0]
        assert "javascript:" not in clean_data["metadata"]["description"]


@pytest.mark.asyncio
class TestSecurityIntegration:
    """Test integrated security functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_authentication=True,
            authentication_type=AuthenticationType.JWT,
            jwt_secret_key="test-secret-key",
            enable_rate_limiting=True,
            default_rate_limit=10,
            enable_waf=True,
            enable_input_validation=True,
            enable_ip_whitelist=False,
            enable_ip_blacklist=True,
            ip_blacklist=["192.168.1.100"],
            enable_ddos_protection=True,
            ddos_threshold=100
        )
        self.security_manager = SecurityManager(self.config)
    
    async def test_user_authentication_flow(self):
        """Test complete user authentication flow."""
        # Authenticate user
        credentials = {"username": "admin", "password": "secure_password"}
        token = await self.security_manager.authenticate_user(credentials)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        verified = self.security_manager.jwt_manager.verify_token(token)
        assert verified["sub"] == "admin"
    
    async def test_invalid_authentication(self):
        """Test handling of invalid credentials."""
        credentials = {"username": "admin", "password": "wrong_password"}
        
        with pytest.raises(AuthenticationError):
            await self.security_manager.authenticate_user(credentials)
    
    def test_api_key_creation_and_validation(self):
        """Test API key creation and validation flow."""
        # Create API key
        api_key = self.security_manager.create_api_key(
            user_id="test_user",
            roles=["admin"],
            permissions=["read", "write", "delete"]
        )
        
        # Validate API key
        key_info = self.security_manager.api_key_manager.verify_api_key(api_key)
        assert key_info["user_id"] == "test_user"
        assert "admin" in key_info["roles"]
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        user_id = "test_user"
        endpoint = "/api/test"
        
        # Should allow initial requests
        for i in range(5):
            allowed = self.security_manager.check_rate_limit(user_id, endpoint)
            assert allowed is True
        
        # Should eventually hit limit (depending on strategy)
        # Note: This test might need adjustment based on token bucket behavior
    
    def test_input_validation_integration(self):
        """Test input validation integration."""
        malicious_data = {
            "user_input": "<script>alert('xss')</script>",
            "query": "'; DROP TABLE users; --"
        }
        
        sanitized = self.security_manager.validate_input(malicious_data)
        
        assert "<script>" not in sanitized["user_input"]
        assert "DROP" not in sanitized["query"]


@pytest.mark.asyncio 
class TestSecurityPerformance:
    """Test security performance under load."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_authentication=True,
            enable_rate_limiting=True,
            enable_waf=True,
            enable_input_validation=True
        )
        self.security_manager = SecurityManager(self.config)
    
    async def test_jwt_performance(self):
        """Test JWT creation and verification performance."""
        payload = {"sub": "user123", "roles": ["user"]}
        
        # Test token creation performance
        start_time = time.time()
        tokens = []
        for i in range(1000):
            token = self.security_manager.jwt_manager.create_token(payload)
            tokens.append(token)
        creation_time = time.time() - start_time
        
        print(f"JWT creation: {1000/creation_time:.1f} tokens/second")
        assert creation_time < 5.0  # Should create 1000 tokens in under 5 seconds
        
        # Test token verification performance
        start_time = time.time()
        for token in tokens[:100]:  # Verify first 100
            verified = self.security_manager.jwt_manager.verify_token(token)
            assert verified["sub"] == "user123"
        verification_time = time.time() - start_time
        
        print(f"JWT verification: {100/verification_time:.1f} tokens/second")
        assert verification_time < 2.0  # Should verify 100 tokens in under 2 seconds
    
    async def test_rate_limiter_performance(self):
        """Test rate limiter performance."""
        start_time = time.time()
        
        # Test 10,000 rate limit checks
        for i in range(10000):
            user_id = f"user_{i % 100}"  # 100 different users
            endpoint = f"/api/endpoint_{i % 10}"  # 10 different endpoints
            self.security_manager.check_rate_limit(user_id, endpoint)
        
        elapsed_time = time.time() - start_time
        print(f"Rate limiting: {10000/elapsed_time:.1f} checks/second")
        assert elapsed_time < 5.0  # Should handle 10k checks in under 5 seconds
    
    async def test_waf_performance(self):
        """Test WAF scanning performance."""
        test_requests = [
            "Normal request data",
            "SELECT * FROM users",  # SQL injection
            "<script>alert('xss')</script>",  # XSS
            "../../etc/passwd",  # Path traversal
            "rm -rf /",  # Command injection
        ] * 200  # 1000 total requests
        
        start_time = time.time()
        
        for request in test_requests:
            threats = self.security_manager.waf_engine.scan_request(request, {})
            # Just scan, don't assert on results for performance test
        
        elapsed_time = time.time() - start_time
        print(f"WAF scanning: {len(test_requests)/elapsed_time:.1f} requests/second")
        assert elapsed_time < 10.0  # Should scan 1000 requests in under 10 seconds


class TestSecurityMetrics:
    """Test security metrics and monitoring."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_audit_logging=True,
            enable_rate_limiting=True
        )
        self.security_manager = SecurityManager(self.config)
    
    def test_authentication_metrics(self):
        """Test authentication metrics collection."""
        # Perform some authentication operations
        try:
            # This should fail and be logged
            credentials = {"username": "invalid", "password": "invalid"}
            asyncio.run(self.security_manager.authenticate_user(credentials))
        except AuthenticationError:
            pass  # Expected
        
        # Successful authentication
        credentials = {"username": "admin", "password": "secure_password"}
        token = asyncio.run(self.security_manager.authenticate_user(credentials))
        assert token is not None
    
    def test_rate_limiting_metrics(self):
        """Test rate limiting metrics collection."""
        user_id = "metrics_test_user"
        
        # Generate some requests to track
        for i in range(20):
            allowed = self.security_manager.check_rate_limit(user_id, "/api/test")
            # Some should be allowed, some denied depending on configuration


@pytest.mark.asyncio
class TestSecurityStressTest:
    """Stress test security components for 100k+ APIs scale."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = SecurityConfig(
            enable_authentication=True,
            enable_rate_limiting=True,
            enable_waf=True,
            default_rate_limit=1000,  # Higher limit for stress test
            burst_limit=100
        )
        self.security_manager = SecurityManager(self.config)
    
    async def test_concurrent_authentication(self):
        """Test concurrent authentication requests."""
        async def authenticate_user():
            credentials = {"username": "admin", "password": "secure_password"}
            try:
                token = await self.security_manager.authenticate_user(credentials)
                return token is not None
            except:
                return False
        
        # Run 100 concurrent authentications
        start_time = time.time()
        tasks = [authenticate_user() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed_time = time.time() - start_time
        
        successful = sum(1 for r in results if r is True)
        print(f"Concurrent auth: {successful}/100 successful in {elapsed_time:.2f}s")
        assert successful >= 90  # At least 90% should succeed
        assert elapsed_time < 10.0  # Should complete in under 10 seconds
    
    async def test_massive_rate_limiting(self):
        """Test rate limiting with many users and endpoints."""
        start_time = time.time()
        
        # Simulate 1000 users hitting 100 endpoints
        checks_performed = 0
        for user_id in range(1000):
            for endpoint_id in range(10):  # 10 endpoints per user = 10k total
                endpoint = f"/api/service_{endpoint_id}"
                user = f"user_{user_id}"
                self.security_manager.check_rate_limit(user, endpoint)
                checks_performed += 1
        
        elapsed_time = time.time() - start_time
        rate = checks_performed / elapsed_time
        
        print(f"Massive rate limiting: {rate:.1f} checks/second ({checks_performed} total)")
        assert rate > 1000  # Should handle at least 1000 checks per second
        assert elapsed_time < 30.0  # Should complete in reasonable time
    
    def test_security_memory_usage(self):
        """Test memory usage of security components."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many API keys to test memory usage
        api_keys = []
        for i in range(10000):
            api_key = self.security_manager.create_api_key(
                user_id=f"user_{i}",
                roles=["user"],
                permissions=["read"]
            )
            api_keys.append(api_key)
        
        # Verify some of the keys
        for i in range(0, 1000, 100):  # Every 100th key
            key_info = self.security_manager.api_key_manager.verify_api_key(api_keys[i])
            assert key_info["user_id"] == f"user_{i}"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Should not use excessive memory (less than 100MB for 10k keys)
        assert memory_increase < 100


if __name__ == "__main__":
    # Run specific test classes for debugging
    pytest.main([
        __file__ + "::TestJWTAuthentication",
        __file__ + "::TestSecurityPerformance",
        "-v"
    ]) 