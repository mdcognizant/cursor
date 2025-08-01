"""Custom exceptions for LLM Agent Bridge."""


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


class ValidationError(BridgeError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class AuthenticationError(BridgeError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(BridgeError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed", resource: str = None):
        super().__init__(message, "AUTHORIZATION_ERROR")
        self.resource = resource


class RateLimitError(BridgeError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class ServiceUnavailableError(BridgeError):
    """Raised when a required service is unavailable."""
    
    def __init__(self, message: str, service_name: str = None):
        super().__init__(message, "SERVICE_UNAVAILABLE")
        self.service_name = service_name


class TimeoutError(BridgeError):
    """Raised when operation times out."""
    
    def __init__(self, message: str = "Operation timed out", timeout_seconds: float = None):
        super().__init__(message, "TIMEOUT_ERROR")
        self.timeout_seconds = timeout_seconds


class ConfigurationError(BridgeError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key 