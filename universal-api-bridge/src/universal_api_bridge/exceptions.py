"""Exception classes for Universal API Bridge."""


class BridgeError(Exception):
    """Base exception for all bridge errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "BRIDGE_ERROR"
        self.details = details or {}


class GRPCConnectionError(BridgeError):
    """Raised when gRPC connection fails."""
    
    def __init__(self, message: str, service_name: str = None, endpoint: str = None):
        super().__init__(message, "GRPC_CONNECTION_ERROR")
        self.service_name = service_name
        self.endpoint = endpoint


class SchemaTranslationError(BridgeError):
    """Raised when schema translation fails."""
    
    def __init__(self, message: str, source_schema: str = None, target_schema: str = None):
        super().__init__(message, "SCHEMA_TRANSLATION_ERROR")
        self.source_schema = source_schema
        self.target_schema = target_schema


class LoadBalancingError(BridgeError):
    """Raised when load balancing fails."""
    
    def __init__(self, message: str, service_name: str = None, strategy: str = None):
        super().__init__(message, "LOAD_BALANCING_ERROR")
        self.service_name = service_name
        self.strategy = strategy


class CircuitBreakerError(BridgeError):
    """Raised when circuit breaker is open."""
    
    def __init__(self, message: str, service_name: str = None, failure_count: int = None):
        super().__init__(message, "CIRCUIT_BREAKER_ERROR")
        self.service_name = service_name
        self.failure_count = failure_count


class ServiceUnavailableError(BridgeError):
    """Raised when a service is unavailable."""
    
    def __init__(self, message: str, service_name: str = None):
        super().__init__(message, "SERVICE_UNAVAILABLE")
        self.service_name = service_name


class ConnectionPoolExhaustedError(BridgeError):
    """Raised when connection pool is exhausted."""
    
    def __init__(self, message: str, service_name: str = None, pool_size: int = None):
        super().__init__(message, "CONNECTION_POOL_EXHAUSTED")
        self.service_name = service_name
        self.pool_size = pool_size


class ServiceRegistryError(BridgeError):
    """Raised when service registry operation fails."""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "SERVICE_REGISTRY_ERROR")
        self.operation = operation


class ConfigurationError(BridgeError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key


class PerformanceError(BridgeError):
    """Raised when performance thresholds are exceeded."""
    
    def __init__(self, message: str, metric: str = None, threshold: float = None, actual: float = None):
        super().__init__(message, "PERFORMANCE_ERROR")
        self.metric = metric
        self.threshold = threshold
        self.actual = actual


class RateLimitError(BridgeError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class AuthenticationError(BridgeError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(BridgeError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class SecurityError(BridgeError):
    """Raised when security validation fails."""
    
    def __init__(self, message: str = "Security error"):
        super().__init__(message, "SECURITY_ERROR")


class InputValidationError(BridgeError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Input validation failed"):
        super().__init__(message, "INPUT_VALIDATION_ERROR")


class TimeoutError(BridgeError):
    """Raised when operation times out."""
    
    def __init__(self, message: str = "Operation timed out", timeout_seconds: float = None):
        super().__init__(message, "TIMEOUT_ERROR")
        self.timeout_seconds = timeout_seconds 