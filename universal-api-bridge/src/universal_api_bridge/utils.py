"""Utility functions for Universal API Bridge with extensive error handling and validation."""

import asyncio
import functools
import inspect
import logging
import traceback
import time
import re
import socket
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def add_error(self, message: str, suggestion: str = None):
        """Add an error with optional suggestion."""
        self.is_valid = False
        self.errors.append(message)
        if suggestion:
            self.suggestions.append(suggestion)
    
    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions
        }


class HelpfulMessages:
    """Collection of helpful messages for integration and troubleshooting."""
    
    @staticmethod
    def service_registration_help(service_name: str) -> Dict[str, Any]:
        """Provide help for service registration issues."""
        return {
            "issue": f"Service '{service_name}' registration",
            "common_causes": [
                "Service name contains invalid characters",
                "Endpoint format is incorrect",
                "Service is already registered",
                "Maximum services limit reached"
            ],
            "solutions": [
                f"Ensure service name '{service_name}' contains only alphanumeric characters, hyphens, and underscores",
                "Use format 'host:port' for endpoints (e.g., 'localhost:50051')",
                "Check existing services with bridge.get_service_count()",
                "Use bridge.configure_massive_scale() for 10K+ services"
            ],
            "examples": {
                "valid_names": ["user-service", "ai_model", "order-svc-v2"],
                "invalid_names": ["user service", "ai.model", "order@svc"],
                "valid_endpoints": ["localhost:50051", "api-server:8080", "127.0.0.1:9000"],
                "invalid_endpoints": ["localhost", "http://api:50051", "api-server"]
            },
            "code_example": f"""
# Correct service registration
bridge.register_service("{service_name}", "localhost:50051")

# For clusters
bridge.register_service_cluster(
    "{service_name}-cluster",
    ["server1:50051", "server2:50051", "server3:50051"]
)
""".strip()
        }
    
    @staticmethod
    def connection_help(endpoint: str, error: str) -> Dict[str, Any]:
        """Provide help for connection issues."""
        return {
            "issue": f"Connection to {endpoint} failed",
            "error": error,
            "troubleshooting_steps": [
                "1. Verify the service is running",
                "2. Check if the port is open and accessible",
                "3. Ensure firewall allows connections",
                "4. Verify the correct protocol (gRPC/HTTP)",
                "5. Check network connectivity"
            ],
            "diagnostic_commands": [
                f"telnet {endpoint.split(':')[0]} {endpoint.split(':')[1] if ':' in endpoint else '80'}",
                f"nc -zv {endpoint.split(':')[0]} {endpoint.split(':')[1] if ':' in endpoint else '80'}",
                f"curl -v http://{endpoint}/health",
                f"grpcurl -plaintext {endpoint} list"
            ],
            "common_fixes": {
                "connection_refused": [
                    "Service is not running - start the service",
                    "Wrong port number - check service configuration",
                    "Service crashed - check service logs"
                ],
                "timeout": [
                    "Network connectivity issues - check network",
                    "Service is overloaded - check service performance",
                    "Firewall blocking - configure firewall rules"
                ],
                "dns_resolution": [
                    "Invalid hostname - use IP address or check DNS",
                    "Hosts file misconfiguration - verify /etc/hosts",
                    "DNS server issues - try different DNS"
                ]
            }
        }
    
    @staticmethod
    def performance_help(metric: str, current_value: float, expected_value: float) -> Dict[str, Any]:
        """Provide help for performance issues."""
        return {
            "issue": f"Performance issue with {metric}",
            "current": current_value,
            "expected": expected_value,
            "impact": "High" if current_value > expected_value * 2 else "Medium",
            "optimization_tips": {
                "latency": [
                    "Enable connection pooling",
                    "Use caching for frequent requests",
                    "Optimize gRPC message sizes",
                    "Consider geographical proximity",
                    "Enable compression"
                ],
                "throughput": [
                    "Increase connection pool size",
                    "Use batch processing for multiple requests",
                    "Enable request multiplexing", 
                    "Scale backend services horizontally",
                    "Optimize database queries"
                ],
                "memory": [
                    "Enable memory optimization mode",
                    "Reduce cache sizes",
                    "Use streaming for large payloads",
                    "Implement garbage collection tuning",
                    "Monitor for memory leaks"
                ]
            },
            "configuration_suggestions": {
                "connection_pool_size": min(1000, max(10, int(current_value * 1.5))),
                "cache_ttl": 300 if metric == "latency" else 600,
                "batch_size": 100 if metric == "throughput" else 50
            }
        }


class Validators:
    """Collection of validation functions with helpful error messages."""
    
    @staticmethod
    def validate_service_name(name: str) -> ValidationResult:
        """Validate service name with detailed feedback."""
        result = ValidationResult(True, [], [], [])
        
        if not name:
            result.add_error(
                "Service name cannot be empty",
                "Provide a descriptive name like 'user-service' or 'ai-model'"
            )
            return result
        
        if not isinstance(name, str):
            result.add_error(
                f"Service name must be a string, got {type(name).__name__}",
                "Convert to string: str(service_name)"
            )
            return result
        
        # Length validation
        if len(name) < 2:
            result.add_error(
                "Service name must be at least 2 characters long",
                "Use descriptive names like 'api', 'db', 'cache'"
            )
        
        if len(name) > 63:
            result.add_error(
                "Service name must be 63 characters or less (DNS limitation)",
                f"Shorten '{name}' to fit DNS requirements"
            )
        
        # Character validation
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_]*[a-zA-Z0-9]$', name):
            invalid_chars = [c for c in name if not re.match(r'[a-zA-Z0-9\-_]', c)]
            result.add_error(
                f"Service name contains invalid characters: {invalid_chars}",
                "Use only letters, numbers, hyphens, and underscores"
            )
        
        if name.startswith('-') or name.endswith('-'):
            result.add_error(
                "Service name cannot start or end with hyphens",
                f"Change '{name}' to something like '{name.strip('-')}'"
            )
        
        # Best practice warnings
        if name.upper() == name:
            result.add_warning("Consider using lowercase for service names (convention)")
        
        if ' ' in name:
            result.add_error(
                "Service name cannot contain spaces",
                f"Replace spaces with hyphens: '{name.replace(' ', '-')}'"
            )
        
        return result
    
    @staticmethod
    def validate_endpoint(endpoint: str) -> ValidationResult:
        """Validate endpoint format with detailed feedback."""
        result = ValidationResult(True, [], [], [])
        
        if not endpoint:
            result.add_error(
                "Endpoint cannot be empty",
                "Use format 'host:port' (e.g., 'localhost:50051')"
            )
            return result
        
        if not isinstance(endpoint, str):
            result.add_error(
                f"Endpoint must be a string, got {type(endpoint).__name__}",
                "Convert to string: str(endpoint)"
            )
            return result
        
        # Basic format validation
        if ':' not in endpoint:
            result.add_error(
                f"Endpoint '{endpoint}' missing port number",
                f"Add port: '{endpoint}:50051'"
            )
            return result
        
        try:
            host, port_str = endpoint.rsplit(':', 1)
            port = int(port_str)
        except ValueError:
            result.add_error(
                f"Invalid port number in '{endpoint}'",
                "Port must be a number between 1 and 65535"
            )
            return result
        
        # Host validation
        if not host:
            result.add_error(
                "Host cannot be empty",
                "Use 'localhost', an IP address, or hostname"
            )
        
        # Port validation
        if port < 1 or port > 65535:
            result.add_error(
                f"Port {port} is out of valid range (1-65535)",
                "Use a port between 1024 and 65535 for non-privileged services"
            )
        
        if port < 1024:
            result.add_warning(
                f"Port {port} is privileged (requires root access)"
            )
        
        # Common port suggestions
        common_grpc_ports = [50051, 9090, 8080, 8081, 8082]
        if port not in common_grpc_ports and 50000 <= port <= 50100:
            result.suggestions.append(
                f"Port {port} is in common gRPC range. Common ports: {common_grpc_ports}"
            )
        
        return result
    
    @staticmethod
    def validate_endpoint_connectivity(endpoint: str, timeout: float = 5.0) -> ValidationResult:
        """Test actual connectivity to endpoint."""
        result = ValidationResult(True, [], [], [])
        
        try:
            host, port_str = endpoint.rsplit(':', 1)
            port = int(port_str)
        except ValueError:
            result.add_error(
                f"Cannot parse endpoint '{endpoint}'",
                "Use format 'host:port'"
            )
            return result
        
        # Test TCP connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        try:
            start_time = time.time()
            result_code = sock.connect_ex((host, port))
            connection_time = time.time() - start_time
            
            if result_code == 0:
                result.suggestions.append(
                    f"✅ Connection successful in {connection_time*1000:.1f}ms"
                )
                
                if connection_time > 1.0:
                    result.add_warning(
                        f"Connection took {connection_time:.2f}s (slow)"
                    )
            else:
                result.add_error(
                    f"Cannot connect to {endpoint}",
                    "Ensure the service is running and accessible"
                )
        except socket.gaierror as e:
            result.add_error(
                f"DNS resolution failed for '{host}': {e}",
                "Check hostname or use IP address"
            )
        except Exception as e:
            result.add_error(
                f"Connection test failed: {e}",
                "Check network connectivity and firewall settings"
            )
        finally:
            sock.close()
        
        return result


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple = (Exception,)
):
    """Decorator for automatic retry with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        break
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}), "
                        f"retrying in {wait_time:.2f}s: {e}"
                    )
                    
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        break
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}), "
                        f"retrying in {wait_time:.2f}s: {e}"
                    )
                    
                    time.sleep(wait_time)
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def log_performance(func: Callable) -> Callable:
    """Decorator to log function performance metrics."""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"✅ {func.__name__} completed in {execution_time*1000:.2f}ms"
            )
            
            if execution_time > 1.0:
                logger.warning(
                    f"⚠️ {func.__name__} took {execution_time:.2f}s (slow)"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"❌ {func.__name__} failed after {execution_time*1000:.2f}ms: {e}"
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"✅ {func.__name__} completed in {execution_time*1000:.2f}ms"
            )
            
            if execution_time > 1.0:
                logger.warning(
                    f"⚠️ {func.__name__} took {execution_time:.2f}s (slow)"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"❌ {func.__name__} failed after {execution_time*1000:.2f}ms: {e}"
            )
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class SafeAsyncOperation:
    """Context manager for safe async operations with comprehensive error handling."""
    
    def __init__(self, operation_name: str, timeout: float = 30.0):
        self.operation_name = operation_name
        self.timeout = timeout
        self.start_time = None
        
    async def __aenter__(self):
        self.start_time = time.time()
        logger.info(f"🚀 Starting {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(f"✅ {self.operation_name} completed in {duration:.2f}s")
        else:
            logger.error(
                f"❌ {self.operation_name} failed after {duration:.2f}s: {exc_val}"
            )
            
            # Provide helpful error context
            if isinstance(exc_val, asyncio.TimeoutError):
                logger.error(
                    f"💡 {self.operation_name} timed out. Consider increasing timeout "
                    f"or optimizing the operation."
                )
            elif isinstance(exc_val, ConnectionError):
                logger.error(
                    f"💡 {self.operation_name} connection failed. Check network "
                    f"connectivity and service availability."
                )
            
        return False  # Don't suppress exceptions


def validate_configuration(config: Dict[str, Any]) -> ValidationResult:
    """Validate bridge configuration with helpful suggestions."""
    result = ValidationResult(True, [], [], [])
    
    # Check required fields
    required_fields = ["frontend", "mcp", "monitoring"]
    for field in required_fields:
        if field not in config:
            result.add_error(
                f"Missing required configuration section: {field}",
                f"Add '{field}' section to configuration"
            )
    
    # Validate frontend configuration
    if "frontend" in config:
        frontend = config["frontend"]
        
        if "port" in frontend:
            port = frontend["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                result.add_error(
                    f"Invalid frontend port: {port}",
                    "Use a port between 1024 and 65535"
                )
        
        if "max_connections" in frontend:
            max_conn = frontend["max_connections"]
            if max_conn < 100:
                result.add_warning(
                    f"Frontend max_connections ({max_conn}) is very low"
                )
            elif max_conn > 100000:
                result.add_warning(
                    f"Frontend max_connections ({max_conn}) is very high - "
                    "ensure system can handle this load"
                )
    
    # Validate MCP configuration  
    if "mcp" in config:
        mcp = config["mcp"]
        
        if "max_services" in mcp:
            max_services = mcp["max_services"]
            if max_services > 10000:
                result.add_warning(
                    f"MCP max_services ({max_services}) exceeds tested limits"
                )
                result.suggestions.append(
                    "For 10K+ services, ensure adequate system resources"
                )
    
    return result


def format_error_for_user(error: Exception, context: str = None) -> Dict[str, Any]:
    """Format error for user-friendly display with troubleshooting info."""
    error_type = type(error).__name__
    error_message = str(error)
    
    # Get stack trace for debugging
    stack_trace = traceback.format_exc()
    
    # Create user-friendly error response
    user_error = {
        "error": {
            "type": error_type,
            "message": error_message,
            "context": context,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "troubleshooting": {
                "common_causes": [],
                "solutions": [],
                "documentation": None
            }
        },
        "debug": {
            "stack_trace": stack_trace,
            "function": inspect.currentframe().f_back.f_code.co_name if inspect.currentframe().f_back else None
        }
    }
    
    # Add specific troubleshooting based on error type
    if "connection" in error_message.lower() or "connect" in error_message.lower():
        user_error["error"]["troubleshooting"].update({
            "common_causes": [
                "Service is not running",
                "Incorrect host or port",
                "Network connectivity issues",
                "Firewall blocking connection"
            ],
            "solutions": [
                "Verify service is running and healthy",
                "Check host and port configuration",
                "Test network connectivity with ping/telnet",
                "Configure firewall to allow connection"
            ],
            "documentation": "/docs/troubleshooting#connection-errors"
        })
    
    elif "timeout" in error_message.lower():
        user_error["error"]["troubleshooting"].update({
            "common_causes": [
                "Service is overloaded",
                "Network latency is high",
                "Request is too complex",
                "Backend service is slow"
            ],
            "solutions": [
                "Increase timeout configuration",
                "Optimize request complexity",
                "Scale backend services",
                "Check network performance"
            ],
            "documentation": "/docs/troubleshooting#timeout-errors"
        })
    
    elif "permission" in error_message.lower() or "auth" in error_message.lower():
        user_error["error"]["troubleshooting"].update({
            "common_causes": [
                "Invalid API key or token",
                "Insufficient permissions",
                "Authentication configuration error"
            ],
            "solutions": [
                "Verify API key is correct and active",
                "Check user permissions for this operation",
                "Review authentication configuration"
            ],
            "documentation": "/docs/authentication"
        })
    
    return user_error


def create_integration_guide(service_name: str, endpoint: str) -> Dict[str, Any]:
    """Create integration guide for a specific service."""
    return {
        "service": service_name,
        "endpoint": endpoint,
        "integration_steps": [
            {
                "step": 1,
                "title": "Register Service",
                "code": f'bridge.register_service("{service_name}", "{endpoint}")',
                "description": f"Register {service_name} with the bridge"
            },
            {
                "step": 2,
                "title": "Test Connectivity",
                "code": f'curl http://localhost:8000/api/{service_name}/health',
                "description": "Verify the service is accessible through the bridge"
            },
            {
                "step": 3,
                "title": "Make REST Calls",
                "code": f'curl -X POST http://localhost:8000/api/{service_name}/your-endpoint',
                "description": "Use standard REST API calls that will be converted to gRPC"
            }
        ],
        "example_calls": [
            {
                "method": "GET",
                "url": f"/api/{service_name}/status",
                "description": "Get service status"
            },
            {
                "method": "POST", 
                "url": f"/api/{service_name}/data",
                "description": "Send data to service",
                "body": {"key": "value"}
            }
        ],
        "tips": [
            f"Use descriptive names for {service_name} resources",
            "Include error handling in your client code",
            "Monitor service health through /health endpoints",
            "Use the bridge's built-in retry logic for reliability"
        ]
    } 