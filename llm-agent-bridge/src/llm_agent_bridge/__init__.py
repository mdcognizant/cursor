"""LLM Agent Bridge - REST to gRPC bridge for LLM agent communication."""

__version__ = "0.1.0"

from .bridge import AgentBridge
from .sdk import AgentSDK
from .config import BridgeConfig
from .exceptions import (
    BridgeError,
    GRPCConnectionError,
    ValidationError,
    AuthenticationError,
)

__all__ = [
    "AgentBridge",
    "AgentSDK", 
    "BridgeConfig",
    "BridgeError",
    "GRPCConnectionError", 
    "ValidationError",
    "AuthenticationError",
] 