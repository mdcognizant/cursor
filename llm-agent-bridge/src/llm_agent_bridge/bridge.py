"""Main LLM Agent Bridge class."""

import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from .config import BridgeConfig, GRPCServiceConfig
from .api.app import create_app, run_server
from .proto.validator import ProtoValidator
from .proto.schema_manager import SchemaManager
from .tools.proto_compiler import auto_compile_protos
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class AgentBridge:
    """Main LLM Agent Bridge class for managing the REST to gRPC bridge."""
    
    def __init__(self, config: Optional[BridgeConfig] = None, config_file: Optional[str] = None):
        """Initialize the Agent Bridge.
        
        Args:
            config: BridgeConfig instance. If None, will be loaded from config_file or defaults.
            config_file: Path to configuration file (YAML/JSON). Only used if config is None.
        """
        if config is not None:
            self.config = config
        elif config_file is not None:
            self.config = BridgeConfig.load_from_file(config_file)
        else:
            self.config = BridgeConfig()
        
        # Validate configuration
        issues = self.config.validate_config()
        if issues:
            raise ConfigurationError(f"Configuration validation failed: {'; '.join(issues)}")
        
        # Initialize components
        self.proto_validator: Optional[ProtoValidator] = None
        self.schema_manager: Optional[SchemaManager] = None
        self.app = None
        
        # Runtime state
        self._running = False
        self._startup_completed = False
        
        logger.info("AgentBridge initialized successfully")
    
    def add_grpc_service(self, name: str, host: str, port: int, **kwargs) -> None:
        """Add a gRPC service configuration.
        
        Args:
            name: Service name
            host: Service host
            port: Service port
            **kwargs: Additional service configuration options
        """
        service_config = GRPCServiceConfig(
            name=name,
            host=host,
            port=port,
            **kwargs
        )
        self.config.add_grpc_service(service_config)
        logger.info(f"Added gRPC service: {name} at {host}:{port}")
    
    def get_service_config(self, name: str) -> Optional[GRPCServiceConfig]:
        """Get gRPC service configuration by name."""
        return self.config.get_grpc_service(name)
    
    def list_services(self) -> Dict[str, GRPCServiceConfig]:
        """List all configured gRPC services."""
        return self.config.grpc_services.copy()
    
    async def startup(self) -> None:
        """Perform startup initialization."""
        if self._startup_completed:
            logger.warning("Startup already completed")
            return
        
        try:
            logger.info("Starting Agent Bridge startup sequence...")
            
            # 1. Compile Protocol Buffers
            logger.info("Compiling Protocol Buffer files...")
            if not auto_compile_protos(self.config.proto):
                raise Exception("Failed to compile Protocol Buffer files")
            
            # 2. Initialize proto validator and schema manager
            logger.info("Initializing Protocol Buffer validation...")
            self.proto_validator = ProtoValidator()
            self.schema_manager = SchemaManager(Path(self.config.proto.output_dir))
            
            # 3. Load and register protobuf modules
            await self._load_protobuf_modules()
            
            # 4. Initialize gRPC client connections
            await self._initialize_grpc_clients()
            
            # 5. Create FastAPI application
            logger.info("Creating FastAPI application...")
            self.app = create_app(self.config)
            
            self._startup_completed = True
            logger.info("Agent Bridge startup completed successfully")
            
        except Exception as e:
            logger.error(f"Agent Bridge startup failed: {e}")
            raise
    
    async def _load_protobuf_modules(self) -> None:
        """Load and register generated protobuf modules."""
        try:
            # This would load the generated protobuf modules
            # and register them with the validator
            
            # For now, we'll just log that this step would happen
            logger.info("Protocol Buffer modules loaded and registered")
            
            # TODO: Implement actual module loading and registration
            # This would involve:
            # 1. Dynamically importing generated _pb2.py and _pb2_grpc.py files
            # 2. Registering message types with the validator
            # 3. Registering service descriptors
            
        except Exception as e:
            logger.error(f"Failed to load protobuf modules: {e}")
            raise
    
    async def _initialize_grpc_clients(self) -> None:
        """Initialize gRPC client connections."""
        try:
            # This would initialize gRPC client connections to configured services
            logger.info("gRPC client connections initialized")
            
            # TODO: Implement actual gRPC client initialization
            # This would involve:
            # 1. Creating gRPC channels for each configured service
            # 2. Setting up TLS if required
            # 3. Testing connectivity
            # 4. Setting up connection pooling and retry logic
            
        except Exception as e:
            logger.error(f"Failed to initialize gRPC clients: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Perform shutdown cleanup."""
        try:
            logger.info("Starting Agent Bridge shutdown sequence...")
            
            # 1. Stop accepting new requests
            self._running = False
            
            # 2. Close gRPC connections
            await self._close_grpc_clients()
            
            # 3. Clean up resources
            self.proto_validator = None
            self.schema_manager = None
            self.app = None
            
            self._startup_completed = False
            logger.info("Agent Bridge shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _close_grpc_clients(self) -> None:
        """Close gRPC client connections."""
        try:
            # This would close all gRPC client connections
            logger.info("gRPC client connections closed")
            
            # TODO: Implement actual gRPC client cleanup
            
        except Exception as e:
            logger.error(f"Failed to close gRPC clients: {e}")
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None, **kwargs) -> None:
        """Run the Agent Bridge server.
        
        Args:
            host: Override server host
            port: Override server port
            **kwargs: Additional uvicorn configuration options
        """
        # Override config if specified
        if host is not None:
            self.config.server.host = host
        if port is not None:
            self.config.server.port = port
        
        # Update config with additional options
        for key, value in kwargs.items():
            if hasattr(self.config.server, key):
                setattr(self.config.server, key, value)
        
        logger.info(
            f"Starting Agent Bridge server on "
            f"{self.config.server.host}:{self.config.server.port}"
        )
        
        # Run the server
        self._running = True
        run_server(self.config)
    
    async def run_async(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Run the Agent Bridge server asynchronously.
        
        This is useful when you want to run the bridge as part of a larger application.
        """
        # Perform startup
        await self.startup()
        
        # Override config if specified
        if host is not None:
            self.config.server.host = host
        if port is not None:
            self.config.server.port = port
        
        try:
            import uvicorn
            
            config = uvicorn.Config(
                self.app,
                host=self.config.server.host,
                port=self.config.server.port,
                log_level=self.config.server.log_level.lower(),
                access_log=True,
            )
            
            server = uvicorn.Server(config)
            self._running = True
            
            logger.info(
                f"Starting Agent Bridge server (async) on "
                f"{self.config.server.host}:{self.config.server.port}"
            )
            
            await server.serve()
            
        except Exception as e:
            logger.error(f"Error running async server: {e}")
            raise
        finally:
            await self.shutdown()
    
    def is_running(self) -> bool:
        """Check if the bridge is currently running."""
        return self._running
    
    def is_startup_completed(self) -> bool:
        """Check if startup has been completed."""
        return self._startup_completed
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of the bridge."""
        status = {
            "status": "healthy" if self._running and self._startup_completed else "starting",
            "running": self._running,
            "startup_completed": self._startup_completed,
            "services": {}
        }
        
        # Add service status
        for name, service_config in self.config.grpc_services.items():
            status["services"][name] = {
                "endpoint": service_config.endpoint,
                "use_tls": service_config.use_tls,
                "status": "unknown"  # Would be updated by health checks
            }
        
        return status
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = {
            "uptime_seconds": 0,  # Would track actual uptime
            "total_requests": 0,
            "active_requests": 0,
            "grpc_connections": len(self.config.grpc_services),
            "proto_schemas": 0,  # Would count registered schemas
        }
        
        # Add per-service metrics
        if self.schema_manager:
            metrics["proto_schemas"] = len(self.schema_manager.list_versions())
        
        return metrics


# Convenience function for quick setup
def create_bridge(config_file: Optional[str] = None, **config_overrides) -> AgentBridge:
    """Create an AgentBridge instance with optional configuration overrides.
    
    Args:
        config_file: Path to configuration file
        **config_overrides: Configuration overrides as keyword arguments
    
    Returns:
        Configured AgentBridge instance
    """
    if config_file:
        config = BridgeConfig.load_from_file(config_file)
    else:
        config = BridgeConfig()
    
    # Apply overrides
    for key, value in config_overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
        elif hasattr(config.server, key):
            setattr(config.server, key, value)
        elif hasattr(config.security, key):
            setattr(config.security, key, value)
    
    return AgentBridge(config=config) 