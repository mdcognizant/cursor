"""FastAPI middleware for security, rate limiting, and logging."""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict, deque

from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from ..config import SecurityConfig
from ..exceptions import AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} {request.url.path} "
                f"in {process_time:.4f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} for {request.method} {request.url.path} "
                f"in {process_time:.4f}s",
                exc_info=True
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from JWT token first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, options={"verify_signature": False})
                if "sub" in payload:
                    return f"user:{payload['sub']}"
            except:
                pass
        
        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"
        
        return "unknown"
    
    def _is_rate_limited(self, client_id: str) -> tuple[bool, Optional[int]]:
        """Check if client is rate limited."""
        now = time.time()
        window_start = now - self.period
        
        # Clean old requests
        client_requests = self.requests[client_id]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        # Check if over limit
        if len(client_requests) >= self.calls:
            # Calculate retry after time
            oldest_request = client_requests[0]
            retry_after = int(oldest_request + self.period - now) + 1
            return True, retry_after
        
        # Add current request
        client_requests.append(now)
        return False, None
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        is_limited, retry_after = self._is_rate_limited(client_id)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise RateLimitError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after=retry_after
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        client_requests = self.requests[client_id]
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - len(client_requests)))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.period))
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for authentication and authorization."""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.bearer_auth = HTTPBearer(auto_error=False)
        
        # Paths that don't require authentication
        self.public_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/schema/list"
        }
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require auth)."""
        return any(path.startswith(public) for public in self.public_paths)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract authentication token from request."""
        # Try Bearer token first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        
        # Try API key
        if self.config.require_api_key:
            api_key = request.headers.get(self.config.api_key_header)
            if api_key:
                return api_key
        
        return None
    
    def _validate_jwt_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and time.time() > exp:
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        # In a real implementation, this would check against a database
        # For now, we'll just check if it's not empty
        return bool(api_key.strip())
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Skip if authentication is disabled
        if not self.config.enable_auth:
            return await call_next(request)
        
        # Extract token
        token = self._extract_token(request)
        if not token:
            raise AuthenticationError("Missing authentication token")
        
        # Validate token
        user_info = None
        
        # Try JWT validation first
        if self.config.jwt_secret:
            user_info = self._validate_jwt_token(token)
        
        # Fall back to API key validation
        if not user_info and self.config.require_api_key:
            if self._validate_api_key(token):
                user_info = {"sub": "api_key_user", "type": "api_key"}
        
        if not user_info:
            raise AuthenticationError("Invalid authentication token")
        
        # Add user info to request state
        request.state.user = user_info
        
        # Log authentication
        logger.debug(f"Authenticated user: {user_info.get('sub', 'unknown')}")
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.active_requests = 0
    
    async def dispatch(self, request: Request, call_next):
        self.active_requests += 1
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            path = request.url.path
            method = request.method
            status = response.status_code
            
            metric_key = f"{method}:{path}:{status}"
            self.request_count[metric_key] += 1
            self.request_duration[metric_key].append(duration)
            
            # Keep only last 1000 durations per endpoint
            if len(self.request_duration[metric_key]) > 1000:
                self.request_duration[metric_key] = self.request_duration[metric_key][-1000:]
            
            # Add metrics headers
            response.headers["X-Request-Count"] = str(sum(self.request_count.values()))
            response.headers["X-Active-Requests"] = str(self.active_requests - 1)
            
            return response
            
        finally:
            self.active_requests -= 1
    
    def get_metrics(self) -> Dict:
        """Get current metrics."""
        metrics = {
            "active_requests": self.active_requests,
            "total_requests": sum(self.request_count.values()),
            "endpoints": {}
        }
        
        for key, count in self.request_count.items():
            durations = self.request_duration[key]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            metrics["endpoints"][key] = {
                "count": count,
                "avg_duration": avg_duration,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0
            }
        
        return metrics 