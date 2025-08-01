"""Universal API Bridge - High-performance REST-to-gRPC bridge with MCP layer."""

__version__ = "1.0.0"

from .bridge import UniversalBridge
from .sdk import UniversalSDK
from .config import BridgeConfig
from .mcp import MCPLayer
from .exceptions import (
    BridgeError,
    GRPCConnectionError,
    SchemaTranslationError,
    LoadBalancingError,
    CircuitBreakerError,
)

__all__ = [
    "UniversalBridge",
    "UniversalSDK",
    "BridgeConfig",
    "MCPLayer",
    "BridgeError",
    "GRPCConnectionError",
    "SchemaTranslationError", 
    "LoadBalancingError",
    "CircuitBreakerError",
] 