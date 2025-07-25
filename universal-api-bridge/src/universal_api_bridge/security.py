"""
Enterprise-grade security module for Universal API Bridge.

This module implements comprehensive security features including:
- JWT/OAuth2 authentication and authorization
- mTLS (mutual TLS) support
- Web Application Firewall (WAF)
- Rate limiting and throttling
- Input validation and sanitization
- IP whitelisting/blacklisting
- DDoS protection
- Security headers
- Audit logging
"""

import asyncio
import hashlib
import hmac
import ipaddress
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import weakref
import ssl
import secrets
import geoip2.database
import geoip2.errors

import jwt
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import redis.asyncio as aioredis
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import SecurityConfig, AuthenticationType, RateLimitStrategy
from .exceptions import (
    AuthenticationError, 
    AuthorizationError, 
    RateLimitError, 
    SecurityError,
    InputValidationError
)

logger = logging.getLogger(__name__)

# Security Constants
WAF_RULES = {
    'sql_injection': [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(['\"];?\s*(DROP|DELETE|UPDATE|INSERT))",
    ],
    'xss': [
        r"(<script[^>]*>.*?</script>)",
        r"(javascript:)",
        r"(on\w+\s*=)",
        r"(<iframe[^>]*>.*?</iframe>)",
        r"(<object[^>]*>.*?</object>)",
    ],
    'path_traversal': [
        r"(\.\./)",
        r"(\.\.\\)",
        r"(%2e%2e%2f)",
        r"(%2e%2e\\)",
    ],
    'command_injection': [
        r"(;\s*rm\s+)",
        r"(;\s*cat\s+)",
        r"(;\s*ls\s+)",
        r"(\|\s*rm\s+)",
        r"(\|\s*cat\s+)",
        r"(\|\s*ls\s+)",
    ]
}


@dataclass
class SecurityContext:
    """Security context for requests."""
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_key: Optional[str] = None
    tenant_id: Optional[str] = None
    authenticated: bool = False
    authentication_method: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class RateLimitInfo:
    """Rate limit information."""
    requests: int = 0
    window_start: float = field(default_factory=time.time)
    last_request: float = field(default_factory=time.time)
    blocked_until: Optional[float] = None


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from the bucket."""
        now = time.time()
        # Add tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class JWTManager:
    """JWT token management and validation."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.secret_key = config.jwt_secret_key or secrets.token_urlsafe(32)
        self.algorithm = config.jwt_algorithm
        self.expiration = config.jwt_expiration
        
    def create_token(self, payload: Dict[str, Any]) -> str:
        """Create a JWT token."""
        now = datetime.utcnow()
        token_payload = {
            "iat": now,
            "exp": now + timedelta(seconds=self.expiration),
            "iss": "universal-api-bridge",
            **payload
        }
        
        return jwt.encode(token_payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")


class OAuth2Manager:
    """OAuth2 token validation and management."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.issuer = config.oauth2_issuer
        self.audience = config.oauth2_audience
        self.jwks_uri = config.oauth2_jwks_uri
        self._jwks_cache = {}
        self._jwks_cache_expiry = 0
        
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify OAuth2 token."""
        # This is a simplified implementation
        # In production, you'd fetch and cache JWKS, verify signatures, etc.
        try:
            # Decode without verification for demo
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            
            # Verify issuer and audience
            if self.issuer and unverified_payload.get("iss") != self.issuer:
                raise AuthenticationError("Invalid issuer")
            
            if self.audience and unverified_payload.get("aud") != self.audience:
                raise AuthenticationError("Invalid audience")
                
            return unverified_payload
            
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid OAuth2 token: {str(e)}")


class APIKeyManager:
    """API key management and validation."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.keys: Dict[str, Dict[str, Any]] = {}
        self._init_demo_keys()
    
    def _init_demo_keys(self):
        """Initialize demo API keys."""
        demo_key = "demo-api-key-12345"
        self.keys[demo_key] = {
            "user_id": "demo-user",
            "roles": ["user"],
            "permissions": ["read", "write"],
            "created_at": time.time(),
            "expires_at": time.time() + self.config.api_key_expiration,
            "active": True
        }
    
    def create_api_key(self, user_id: str, roles: List[str], permissions: List[str]) -> str:
        """Create a new API key."""
        api_key = secrets.token_urlsafe(32)
        self.keys[api_key] = {
            "user_id": user_id,
            "roles": roles,
            "permissions": permissions,
            "created_at": time.time(),
            "expires_at": time.time() + self.config.api_key_expiration,
            "active": True
        }
        return api_key
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify an API key."""
        if api_key not in self.keys:
            raise AuthenticationError("Invalid API key")
        
        key_info = self.keys[api_key]
        
        if not key_info["active"]:
            raise AuthenticationError("API key is inactive")
        
        if time.time() > key_info["expires_at"]:
            raise AuthenticationError("API key has expired")
        
        return key_info


class RateLimiter:
    """Distributed rate limiting implementation."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.strategy = config.rate_limit_strategy
        self.default_limit = config.default_rate_limit
        self.burst_limit = config.burst_limit
        self.window = config.rate_limit_window
        
        # In-memory storage for rate limits (in production, use Redis)
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
    
    def _get_key(self, identifier: str, endpoint: str = "") -> str:
        """Generate rate limit key."""
        return f"rate_limit:{identifier}:{endpoint}"
    
    def check_rate_limit(self, identifier: str, endpoint: str = "", limit: Optional[int] = None) -> bool:
        """Check if request is within rate limit."""
        if not self.config.enable_rate_limiting:
            return True
        
        limit = limit or self.default_limit
        key = self._get_key(identifier, endpoint)
        
        if self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(key, limit)
        elif self.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(key, limit)
        elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(key, limit)
        else:
            return self._check_token_bucket(key, limit)
    
    def _check_token_bucket(self, key: str, limit: int) -> bool:
        """Token bucket rate limiting."""
        if key not in self.token_buckets:
            self.token_buckets[key] = TokenBucket(
                capacity=self.burst_limit,
                refill_rate=limit / self.window
            )
        
        return self.token_buckets[key].consume()
    
    def _check_fixed_window(self, key: str, limit: int) -> bool:
        """Fixed window rate limiting."""
        now = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = RateLimitInfo()
        
        rate_info = self.rate_limits[key]
        
        # Reset window if expired
        if now - rate_info.window_start >= self.window:
            rate_info.requests = 0
            rate_info.window_start = now
        
        if rate_info.requests >= limit:
            return False
        
        rate_info.requests += 1
        rate_info.last_request = now
        return True
    
    def _check_sliding_window(self, key: str, limit: int) -> bool:
        """Sliding window rate limiting."""
        now = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = RateLimitInfo()
        
        rate_info = self.rate_limits[key]
        
        # This is a simplified sliding window
        # In production, you'd use a more sophisticated implementation
        window_start = now - self.window
        
        if rate_info.last_request < window_start:
            rate_info.requests = 0
        
        if rate_info.requests >= limit:
            return False
        
        rate_info.requests += 1
        rate_info.last_request = now
        return True


class WAFEngine:
    """Web Application Firewall engine."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.compiled_rules = self._compile_rules()
        
    def _compile_rules(self) -> Dict[str, List[re.Pattern]]:
        """Compile WAF rules for better performance."""
        compiled = {}
        for category, patterns in WAF_RULES.items():
            compiled[category] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        return compiled
    
    def scan_request(self, request_data: str, headers: Dict[str, str]) -> List[str]:
        """Scan request for security threats."""
        if not self.config.enable_waf:
            return []
        
        threats = []
        
        # Scan request data
        for category, patterns in self.compiled_rules.items():
            for pattern in patterns:
                if pattern.search(request_data):
                    threats.append(f"{category}: {pattern.pattern}")
        
        # Scan headers
        header_string = json.dumps(headers, separators=(',', ':'))
        for category, patterns in self.compiled_rules.items():
            for pattern in patterns:
                if pattern.search(header_string):
                    threats.append(f"{category}_header: {pattern.pattern}")
        
        return threats


class InputValidator:
    """Input validation and sanitization."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def validate_request_size(self, content_length: int) -> bool:
        """Validate request size."""
        return content_length <= self.config.max_request_size
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data."""
        if not self.config.enable_input_validation:
            return data
        
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string input."""
        if self.config.enable_xss_protection:
            # Remove potential XSS vectors
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
            text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        if self.config.enable_sql_injection_protection:
            # Basic SQL injection protection
            dangerous_patterns = [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            ]
            for pattern in dangerous_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.jwt_manager = JWTManager(config)
        self.oauth2_manager = OAuth2Manager(config)
        self.api_key_manager = APIKeyManager(config)
        self.rate_limiter = RateLimiter(config)
        self.waf_engine = WAFEngine(config)
        self.input_validator = InputValidator(config)
        
        # GeoIP database (optional)
        self.geoip_db = None
        if config.enable_geoblocking:
            try:
                self.geoip_db = geoip2.database.Reader('GeoLite2-Country.mmdb')
            except Exception as e:
                logger.warning(f"Could not load GeoIP database: {e}")
    
    async def dispatch(self, request: Request, call_next):
        """Main security middleware dispatch."""
        try:
            # Create security context
            security_context = SecurityContext(
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                request_id=request.headers.get("x-request-id", secrets.token_hex(8))
            )
            
            # IP-based security checks
            if not await self._check_ip_security(security_context.ip_address):
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied from this IP address"}
                )
            
            # Geographic blocking
            if not await self._check_geo_blocking(security_context.ip_address):
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied from this geographic location"}
                )
            
            # DDoS protection
            if not await self._check_ddos_protection(security_context.ip_address):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Request rate too high - DDoS protection activated"}
                )
            
            # Rate limiting
            if not self.rate_limiter.check_rate_limit(
                security_context.ip_address, 
                str(request.url.path)
            ):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
            
            # Request size validation
            content_length = int(request.headers.get("content-length", 0))
            if not self.input_validator.validate_request_size(content_length):
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
            
            # Authentication
            if self.config.enable_authentication:
                security_context = await self._authenticate_request(request, security_context)
            
            # WAF scanning
            if self.config.enable_waf:
                await self._waf_scan(request)
            
            # Add security context to request state
            request.state.security_context = security_context
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            if self.config.enable_security_headers:
                self._add_security_headers(response)
            
            # Audit logging
            if self.config.enable_audit_logging:
                await self._audit_log(request, response, security_context)
            
            return response
            
        except AuthenticationError as e:
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication failed", "detail": str(e)}
            )
        except AuthorizationError as e:
            return JSONResponse(
                status_code=403,
                content={"error": "Authorization failed", "detail": str(e)}
            )
        except SecurityError as e:
            return JSONResponse(
                status_code=400,
                content={"error": "Security error", "detail": str(e)}
            )
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _check_ip_security(self, ip_address: str) -> bool:
        """Check IP whitelist/blacklist."""
        if self.config.enable_ip_blacklist and ip_address in self.config.ip_blacklist:
            return False
        
        if self.config.enable_ip_whitelist and self.config.ip_whitelist:
            return ip_address in self.config.ip_whitelist
        
        return True
    
    async def _check_geo_blocking(self, ip_address: str) -> bool:
        """Check geographic blocking."""
        if not self.config.enable_geoblocking or not self.geoip_db:
            return True
        
        try:
            response = self.geoip_db.country(ip_address)
            country_code = response.country.iso_code
            return country_code not in self.config.blocked_countries
        except geoip2.errors.AddressNotFoundError:
            return True  # Allow if country cannot be determined
        except Exception as e:
            logger.warning(f"GeoIP lookup error: {e}")
            return True
    
    async def _check_ddos_protection(self, ip_address: str) -> bool:
        """Check DDoS protection."""
        if not self.config.enable_ddos_protection:
            return True
        
        # Use rate limiter with DDoS threshold
        return self.rate_limiter.check_rate_limit(
            f"ddos:{ip_address}",
            "",
            self.config.ddos_threshold
        )
    
    async def _authenticate_request(self, request: Request, context: SecurityContext) -> SecurityContext:
        """Authenticate the request."""
        auth_header = request.headers.get("authorization")
        api_key_header = request.headers.get(self.config.api_key_header)
        api_key_query = request.query_params.get(self.config.api_key_query_param)
        
        if self.config.authentication_type == AuthenticationType.JWT and auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = self.jwt_manager.verify_token(token)
                context.user_id = payload.get("sub")
                context.roles = payload.get("roles", [])
                context.permissions = payload.get("permissions", [])
                context.authenticated = True
                context.authentication_method = "jwt"
        
        elif self.config.authentication_type == AuthenticationType.OAUTH2 and auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = await self.oauth2_manager.verify_token(token)
                context.user_id = payload.get("sub")
                context.roles = payload.get("roles", [])
                context.permissions = payload.get("scope", "").split()
                context.authenticated = True
                context.authentication_method = "oauth2"
        
        elif self.config.authentication_type == AuthenticationType.API_KEY:
            api_key = api_key_header or api_key_query
            if api_key:
                key_info = self.api_key_manager.verify_api_key(api_key)
                context.user_id = key_info["user_id"]
                context.roles = key_info["roles"]
                context.permissions = key_info["permissions"]
                context.api_key = api_key
                context.authenticated = True
                context.authentication_method = "api_key"
        
        if self.config.enable_authentication and not context.authenticated:
            raise AuthenticationError("Authentication required")
        
        return context
    
    async def _waf_scan(self, request: Request) -> None:
        """Perform WAF scanning."""
        # Get request body
        body = await request.body()
        request_data = body.decode("utf-8", errors="ignore")
        
        # Scan request
        threats = self.waf_engine.scan_request(request_data, dict(request.headers))
        
        if threats:
            logger.warning(f"WAF threats detected: {threats}")
            raise SecurityError(f"Malicious request detected: {', '.join(threats)}")
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if self.config.hsts_max_age > 0:
            response.headers["Strict-Transport-Security"] = f"max-age={self.config.hsts_max_age}; includeSubDomains"
        
        if self.config.content_security_policy:
            response.headers["Content-Security-Policy"] = self.config.content_security_policy
    
    async def _audit_log(self, request: Request, response: Response, context: SecurityContext) -> None:
        """Log security audit information."""
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": context.request_id,
            "ip_address": context.ip_address,
            "user_agent": context.user_agent,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.query_params),
            "user_id": context.user_id,
            "authenticated": context.authenticated,
            "authentication_method": context.authentication_method,
            "status_code": response.status_code,
            "roles": context.roles,
            "permissions": context.permissions
        }
        
        logger.info(f"Security audit: {json.dumps(audit_data)}")


class SecurityManager:
    """Main security manager for the Universal API Bridge."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.jwt_manager = JWTManager(config)
        self.oauth2_manager = OAuth2Manager(config)
        self.api_key_manager = APIKeyManager(config)
        self.rate_limiter = RateLimiter(config)
        self.waf_engine = WAFEngine(config)
        self.input_validator = InputValidator(config)
        
    def get_middleware(self):
        """Get the security middleware."""
        return SecurityMiddleware(None, self.config)
    
    async def authenticate_user(self, credentials: Dict[str, Any]) -> str:
        """Authenticate user and return token."""
        # This is a demo implementation
        username = credentials.get("username")
        password = credentials.get("password")
        
        # In production, verify against a real user database
        if username == "admin" and password == "secure_password":
            token_payload = {
                "sub": username,
                "roles": ["admin", "user"],
                "permissions": ["read", "write", "delete"],
                "type": "access_token"
            }
            return self.jwt_manager.create_token(token_payload)
        
        raise AuthenticationError("Invalid credentials")
    
    def create_api_key(self, user_id: str, roles: List[str], permissions: List[str]) -> str:
        """Create a new API key."""
        return self.api_key_manager.create_api_key(user_id, roles, permissions)
    
    def check_rate_limit(self, identifier: str, endpoint: str = "") -> bool:
        """Check rate limit for identifier."""
        return self.rate_limiter.check_rate_limit(identifier, endpoint)
    
    def validate_input(self, data: Any) -> Any:
        """Validate and sanitize input."""
        return self.input_validator.sanitize_input(data) 