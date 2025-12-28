"""Universal API Bridge - Main bridge class for REST-to-gRPC conversion."""

import asyncio
import logging
import time
import sys
import signal
import json
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from datetime import datetime

from .config import BridgeConfig, ServiceCluster, ServiceEndpoint, create_massive_scale_config, create_cluster_from_endpoints
from .mcp import MCPLayer
from .gateway import UniversalGateway
from .schema import SchemaTranslator
from .exceptions import (
    ConfigurationError, 
    ServiceUnavailableError, 
    GRPCConnectionError, 
    BridgeError,
    LoadBalancingError
)
from .utils import (
    Validators, 
    HelpfulMessages, 
    ValidationResult, 
    with_retry, 
    log_performance, 
    SafeAsyncOperation,
    format_error_for_user,
    create_integration_guide
)

logger = logging.getLogger(__name__)


class UniversalBridge:
    """
    Universal API Bridge - Convert any REST API to high-performance gRPC backend.
    
    This bridge provides:
    - Universal REST frontend accepting any API pattern
    - MCP layer for 10,000+ service connectivity  
    - Pure gRPC backend for maximum efficiency
    - Automatic schema translation
    - Load balancing and circuit breakers
    - High-performance connection pooling
    """
    
    def __init__(self, config: Optional[BridgeConfig] = None):
        """Initialize the Universal Bridge.
        
        Args:
            config: Bridge configuration. If None, creates optimized default config.
        """
        self.config = config or BridgeConfig()
        
        # Core components
        self.mcp_layer: Optional[MCPLayer] = None
        self.gateway: Optional[UniversalGateway] = None
        self.schema_translator: Optional[SchemaTranslator] = None
        
        # Runtime state
        self._running = False
        self._startup_completed = False
        
        # Performance tracking
        self._start_time = 0.0
        self._total_requests = 0
        self._successful_requests = 0
        
        logger.info("Universal API Bridge initialized")
    
    def register_service(self, name: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Register a gRPC service for the bridge to route to with comprehensive validation.
        
        Args:
            name: Service name for routing (must be DNS-compatible)
            endpoint: Service endpoint in format "host:port"
            **kwargs: Additional service configuration
        
        Returns:
            Registration result with status and helpful information
        
        Example:
            result = bridge.register_service("user-service", "localhost:50051")
            if result["success"]:
                print("Service registered successfully!")
            else:
                print(f"Registration failed: {result['errors']}")
        
        Raises:
            ConfigurationError: If validation fails
            ServiceUnavailableError: If maximum services limit reached
        """
        registration_start = time.time()
        
        try:
            # Step 1: Validate service name
            logger.info(f"🔍 Validating service name '{name}'...")
            name_validation = Validators.validate_service_name(name)
            
            if not name_validation.is_valid:
                help_info = HelpfulMessages.service_registration_help(name)
                error_msg = f"Service name validation failed: {', '.join(name_validation.errors)}"
                
                logger.error(f"❌ {error_msg}")
                for suggestion in name_validation.suggestions:
                    logger.info(f"💡 Suggestion: {suggestion}")
                
                raise ConfigurationError(
                    error_msg,
                    details={
                        "validation_errors": name_validation.errors,
                        "suggestions": name_validation.suggestions,
                        "help": help_info
                    }
                )
            
            # Log any warnings
            for warning in name_validation.warnings:
                logger.warning(f"⚠️ {warning}")
            
            # Step 2: Validate endpoint format
            logger.info(f"🔍 Validating endpoint '{endpoint}'...")
            endpoint_validation = Validators.validate_endpoint(endpoint)
            
            if not endpoint_validation.is_valid:
                help_info = HelpfulMessages.connection_help(endpoint, "Invalid format")
                error_msg = f"Endpoint validation failed: {', '.join(endpoint_validation.errors)}"
                
                logger.error(f"❌ {error_msg}")
                for suggestion in endpoint_validation.suggestions:
                    logger.info(f"💡 Suggestion: {suggestion}")
                
                raise ConfigurationError(
                    error_msg,
                    details={
                        "validation_errors": endpoint_validation.errors,
                        "suggestions": endpoint_validation.suggestions,
                        "help": help_info
                    }
                )
            
            # Step 3: Test connectivity (optional but recommended)
            logger.info(f"🔍 Testing connectivity to '{endpoint}'...")
            connectivity_test = Validators.validate_endpoint_connectivity(endpoint, timeout=5.0)
            
            for suggestion in connectivity_test.suggestions:
                logger.info(f"✅ {suggestion}")
            
            if not connectivity_test.is_valid:
                for error in connectivity_test.errors:
                    logger.warning(f"⚠️ Connectivity issue: {error}")
                logger.warning("Service will be registered but may not be immediately available")
            
            # Step 4: Check service limits
            current_service_count = self.get_service_count()
            max_services = self.config.mcp.max_services
            
            if current_service_count >= max_services:
                error_msg = (
                    f"Cannot register service '{name}': Maximum services limit "
                    f"({max_services}) reached. Current: {current_service_count}"
                )
                logger.error(f"❌ {error_msg}")
                logger.info("💡 Consider using bridge.configure_massive_scale() for more services")
                
                raise ServiceUnavailableError(
                    error_msg,
                    details={
                        "current_services": current_service_count,
                        "max_services": max_services,
                        "suggestion": "Call bridge.configure_massive_scale(10000) to increase limit"
                    }
                )
            
            # Step 5: Parse and create service endpoint
            try:
                host, port_str = endpoint.rsplit(":", 1)
                port = int(port_str)
                
                service_endpoint = ServiceEndpoint(
                    host=host,
                    port=port,
                    **kwargs
                )
                
                cluster = ServiceCluster(
                    name=name,
                    endpoints=[service_endpoint]
                )
                
            except ValueError as e:
                error_msg = f"Failed to parse endpoint '{endpoint}': {e}"
                logger.error(f"❌ {error_msg}")
                raise ConfigurationError(error_msg)
            
            # Step 6: Check for duplicate registration
            if name in self.config.clusters:
                logger.warning(f"⚠️ Service '{name}' already registered, updating configuration")
            
            # Step 7: Register the service
            self.config.add_service_cluster(cluster)
            
            registration_time = time.time() - registration_start
            
            logger.info(f"✅ Successfully registered service '{name}' at {endpoint} in {registration_time*1000:.1f}ms")
            
            # Create integration guide
            integration_guide = create_integration_guide(name, endpoint)
            
            # Return comprehensive registration result
            return {
                "success": True,
                "service_name": name,
                "endpoint": endpoint,
                "registration_time_ms": registration_time * 1000,
                "service_count": self.get_service_count(),
                "max_services": max_services,
                "capacity_utilization": self.get_service_count() / max_services,
                "connectivity_status": "healthy" if connectivity_test.is_valid else "warning",
                "integration_guide": integration_guide,
                "next_steps": [
                    f"Test with: curl http://localhost:{self.config.frontend.port}/api/{name}/health",
                    f"View all services: curl http://localhost:{self.config.frontend.port}/api/services",
                    "Check bridge health: curl http://localhost:{self.config.frontend.port}/health"
                ]
            }
            
        except Exception as e:
            registration_time = time.time() - registration_start
            logger.error(f"❌ Failed to register service '{name}' after {registration_time*1000:.1f}ms: {e}")
            
            # Format error for user
            user_error = format_error_for_user(e, f"registering service '{name}'")
            
            if isinstance(e, (ConfigurationError, ServiceUnavailableError)):
                raise
            else:
                raise ConfigurationError(
                    f"Unexpected error during service registration: {e}",
                    details=user_error
                )
    
    def register_service_cluster(self, name: str, endpoints: List[str], **kwargs) -> None:
        """Register a cluster of gRPC services for load balancing.
        
        Args:
            name: Cluster name
            endpoints: List of endpoints in format ["host:port", ...]
            **kwargs: Additional cluster configuration
        
        Example:
            bridge.register_service_cluster(
                "user-service-cluster", 
                ["server1:50051", "server2:50051", "server3:50051"],
                load_balancing="round_robin"
            )
        """
        try:
            cluster = create_cluster_from_endpoints(name, endpoints, **kwargs)
            self.config.add_service_cluster(cluster)
            logger.info(f"Registered service cluster '{name}' with {len(endpoints)} endpoints")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to register cluster '{name}': {e}")
    
    def auto_discover_services(self, discovery_backend: str = "consul", **kwargs) -> None:
        """Enable automatic service discovery.
        
        Args:
            discovery_backend: Discovery backend ("consul", "etcd", "k8s")
            **kwargs: Backend-specific configuration
        """
        self.config.mcp.auto_discovery = True
        self.config.mcp.discovery_service = discovery_backend
        
        for key, value in kwargs.items():
            if hasattr(self.config.mcp, key):
                setattr(self.config.mcp, key, value)
        
        logger.info(f"Enabled auto-discovery with {discovery_backend}")
    
    def configure_massive_scale(self, max_services: int = 10000) -> None:
        """Configure the bridge for massive scale deployment.
        
        Args:
            max_services: Maximum number of services to support
        """
        # Apply massive scale optimizations
        optimized_config = create_massive_scale_config(max_services)
        
        # Merge with existing config
        self.config.mcp.max_services = optimized_config.mcp.max_services
        self.config.mcp.max_connections_per_service = optimized_config.mcp.max_connections_per_service
        self.config.frontend.max_connections = optimized_config.frontend.max_connections
        self.config.performance = optimized_config.performance
        
        logger.info(f"Configured for massive scale: {max_services} services")
    
    @log_performance
    async def start(self) -> Dict[str, Any]:
        """Start the Universal Bridge with comprehensive startup validation.
        
        Returns:
            Startup result with detailed status information
            
        Raises:
            ConfigurationError: If configuration is invalid
            BridgeError: If startup fails
        """
        if self._running:
            logger.warning("⚠️ Bridge already running")
            return {
                "success": True,
                "already_running": True,
                "uptime_seconds": time.time() - self._start_time
            }
        
        startup_start = time.time()
        startup_steps = []
        
        async with SafeAsyncOperation("Universal Bridge Startup", timeout=60.0):
            try:
                logger.info("🚀 Starting Universal API Bridge...")
                self._start_time = startup_start
                
                # Step 1: Validate configuration
                logger.info("🔍 Step 1/6: Validating configuration...")
                step_start = time.time()
                
                issues = self.config.validate_massive_scale()
                if issues:
                    logger.warning(f"⚠️ Configuration warnings: {'; '.join(issues)}")
                    for issue in issues:
                        logger.info(f"💡 Suggestion: {issue}")
                
                startup_steps.append({
                    "step": 1,
                    "name": "Configuration Validation",
                    "duration_ms": (time.time() - step_start) * 1000,
                    "status": "completed",
                    "warnings": issues
                })
                
                # Step 2: Initialize core components
                logger.info("🔧 Step 2/6: Initializing core components...")
                step_start = time.time()
                
                try:
                    await self._initialize_components()
                    startup_steps.append({
                        "step": 2,
                        "name": "Component Initialization",
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "completed"
                    })
                except Exception as e:
                    error_msg = f"Failed to initialize components: {e}"
                    logger.error(f"❌ {error_msg}")
                    startup_steps.append({
                        "step": 2,
                        "name": "Component Initialization",
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "failed",
                        "error": str(e)
                    })
                    raise BridgeError(error_msg)
                
                # Step 3: Start MCP layer
                logger.info("🔗 Step 3/6: Starting MCP layer...")
                step_start = time.time()
                
                try:
                    await self.mcp_layer.start()
                    logger.info(f"✅ MCP layer started with capacity for {self.config.mcp.max_services} services")
                    startup_steps.append({
                        "step": 3,
                        "name": "MCP Layer Startup",
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "completed",
                        "capacity": self.config.mcp.max_services
                    })
                except Exception as e:
                    error_msg = f"Failed to start MCP layer: {e}"
                    logger.error(f"❌ {error_msg}")
                    startup_steps.append({
                        "step": 3,
                        "name": "MCP Layer Startup",
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "failed",
                        "error": str(e)
                    })
                    raise BridgeError(error_msg)
                
                # Step 4: Register configured services
                logger.info("📝 Step 4/6: Registering configured services...")
                step_start = time.time()
                
                try:
                    registration_results = await self._register_configured_services()
                    startup_steps.append({
                        "step": 4,
                        "name": "Service Registration",
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "completed",
                        "services_registered": len(registration_results.get("successful", [])),
                        "registration_failures": len(registration_results.get("failed", []))
                    })
                except Exception as e:
                    error_msg = f"Failed to register services: {e}"
                    logger.error(f"❌ {error_msg}")
                    startup_steps.append({
                        "step": 4,
                        "name": "Service Registration",
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "failed",
                        "error": str(e)
                    })
                    # Don't fail startup for service registration issues
                    logger.warning("⚠️ Continuing startup despite service registration issues")
                
                # Step 5: Start gateway
                logger.info("🌐 Step 5/6: Starting universal gateway...")
                step_start = time.time()
                
                try:
                    await self.gateway.start()
                    logger.info(f"✅ Gateway started on {self.config.frontend.host}:{self.config.frontend.port}")
                    startup_steps.append({
                        "step": 5,
                        "name": "Gateway Startup",
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "completed",
                        "endpoint": f"{self.config.frontend.host}:{self.config.frontend.port}"
                    })
                except Exception as e:
                    error_msg = f"Failed to start gateway: {e}"
                    logger.error(f"❌ {error_msg}")
                    startup_steps.append({
                        "step": 5,
                        "name": "Gateway Startup", 
                        "duration_ms": (time.time() - step_start) * 1000,
                        "status": "failed",
                        "error": str(e)
                    })
                    raise BridgeError(error_msg)
                
                # Step 6: Final setup and health checks
                logger.info("✅ Step 6/6: Final setup and health checks...")
                step_start = time.time()
                
                self._running = True
                self._startup_completed = True
                
                # Perform initial health check
                health_status = await self.get_health_status()
                
                startup_steps.append({
                    "step": 6,
                    "name": "Final Setup",
                    "duration_ms": (time.time() - step_start) * 1000,
                    "status": "completed",
                    "health_status": health_status.get("status", "unknown")
                })
                
                total_startup_time = time.time() - startup_start
                
                logger.info("🎉" + "="*60)
                logger.info("🎉 UNIVERSAL API BRIDGE STARTED SUCCESSFULLY!")
                logger.info(f"🎉 Startup completed in {total_startup_time*1000:.1f}ms")
                logger.info(f"🎉 Frontend: http://{self.config.frontend.host}:{self.config.frontend.port}")
                logger.info(f"🎉 Health: http://{self.config.frontend.host}:{self.config.frontend.port}/health")
                logger.info(f"🎉 API Docs: http://{self.config.frontend.host}:{self.config.frontend.port}/docs")
                logger.info(f"🎉 Services: {self.get_service_count()}/{self.config.mcp.max_services}")
                logger.info("🎉" + "="*60)
                
                # Return comprehensive startup result
                return {
                    "success": True,
                    "startup_time_ms": total_startup_time * 1000,
                    "startup_steps": startup_steps,
                    "configuration": {
                        "frontend_endpoint": f"{self.config.frontend.host}:{self.config.frontend.port}",
                        "max_services": self.config.mcp.max_services,
                        "registered_services": self.get_service_count(),
                        "performance_mode": self.config.performance.enable_aggressive_caching
                    },
                    "endpoints": {
                        "base_url": f"http://{self.config.frontend.host}:{self.config.frontend.port}",
                        "health": f"http://{self.config.frontend.host}:{self.config.frontend.port}/health",
                        "metrics": f"http://{self.config.frontend.host}:{self.config.frontend.port}/metrics",
                        "api_docs": f"http://{self.config.frontend.host}:{self.config.frontend.port}/docs",
                        "services": f"http://{self.config.frontend.host}:{self.config.frontend.port}/api/services"
                    },
                    "next_steps": [
                        f"Test health: curl {self.config.frontend.host}:{self.config.frontend.port}/health",
                        f"View services: curl {self.config.frontend.host}:{self.config.frontend.port}/api/services",
                        f"Register service: bridge.register_service('my-service', 'localhost:50051')",
                        "Start making REST API calls to /api/{service-name}/*"
                    ],
                    "health_status": health_status
                }
                
            except Exception as e:
                total_startup_time = time.time() - startup_start
                logger.error(f"❌ Bridge startup failed after {total_startup_time*1000:.1f}ms: {e}")
                
                # Attempt graceful cleanup
                try:
                    await self.stop()
                except Exception as cleanup_error:
                    logger.error(f"❌ Cleanup during failed startup also failed: {cleanup_error}")
                
                # Format error for user
                user_error = format_error_for_user(e, "starting Universal Bridge")
                
                raise BridgeError(
                    f"Failed to start Universal API Bridge: {e}",
                    details={
                        "startup_time_ms": total_startup_time * 1000,
                        "completed_steps": startup_steps,
                        "error_details": user_error,
                        "recovery_suggestions": [
                            "Check all service endpoints are accessible",
                            "Verify configuration settings",
                            "Ensure sufficient system resources",
                            "Check logs for detailed error information"
                        ]
                    }
                )
    
    async def stop(self) -> None:
        """Stop the Universal Bridge."""
        if not self._running:
            return
        
        logger.info("Stopping Universal API Bridge...")
        
        try:
            # Stop components in reverse order
            if self.gateway:
                await self.gateway.stop()
            
            if self.mcp_layer:
                await self.mcp_layer.stop()
            
            self._running = False
            self._startup_completed = False
            
            uptime = time.time() - self._start_time
            logger.info(
                f"Universal API Bridge stopped. "
                f"Uptime: {uptime:.1f}s, "
                f"Requests processed: {self._total_requests}"
            )
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None, **kwargs) -> None:
        """Run the Universal Bridge (blocking).
        
        Args:
            host: Override server host
            port: Override server port
            **kwargs: Additional server configuration
        """
        # Override config if specified
        if host is not None:
            self.config.frontend.host = host
        if port is not None:
            self.config.frontend.port = port
        
        # Apply additional config
        for key, value in kwargs.items():
            if hasattr(self.config.frontend, key):
                setattr(self.config.frontend, key, value)
        
        logger.info(
            f"Starting Universal API Bridge on "
            f"{self.config.frontend.host}:{self.config.frontend.port}"
        )
        
        # Run the bridge
        asyncio.run(self._run_async())
    
    async def run_async(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Run the Universal Bridge (async).
        
        Useful for embedding in larger applications.
        """
        if host is not None:
            self.config.frontend.host = host
        if port is not None:
            self.config.frontend.port = port
        
        await self._run_async()
    
    async def _run_async(self) -> None:
        """Internal async runner."""
        try:
            await self.start()
            
            # Keep running until interrupted
            while self._running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Bridge runtime error: {e}")
            raise
        finally:
            await self.stop()
    
    async def _initialize_components(self) -> None:
        """Initialize core bridge components."""
        # Initialize MCP layer
        self.mcp_layer = MCPLayer(self.config.mcp)
        
        # Initialize schema translator
        self.schema_translator = SchemaTranslator()
        
        # Initialize universal gateway
        self.gateway = UniversalGateway(
            config=self.config,
            mcp_layer=self.mcp_layer,
            schema_translator=self.schema_translator
        )
        
        logger.info("Core components initialized")
    
    async def _register_configured_services(self) -> Dict[str, Any]:
        """Register all configured service clusters with MCP layer with detailed results."""
        successful_registrations = []
        failed_registrations = []
        
        logger.info(f"📝 Registering {len(self.config.clusters)} configured service clusters...")
        
        for cluster_name, cluster in self.config.clusters.items():
            try:
                logger.info(f"🔗 Registering cluster '{cluster_name}' with {len(cluster.endpoints)} endpoints...")
                
                await self.mcp_layer.register_service(cluster)
                
                successful_registrations.append({
                    "cluster_name": cluster_name,
                    "endpoints": [ep.endpoint for ep in cluster.endpoints],
                    "endpoint_count": len(cluster.endpoints),
                    "load_balancing": cluster.load_balancing.value,
                    "circuit_breaker_enabled": cluster.circuit_breaker_enabled
                })
                
                logger.info(f"✅ Successfully registered cluster '{cluster_name}'")
                
            except Exception as e:
                error_msg = f"Failed to register cluster '{cluster_name}': {e}"
                logger.error(f"❌ {error_msg}")
                
                failed_registrations.append({
                    "cluster_name": cluster_name,
                    "error": str(e),
                    "endpoints": [ep.endpoint for ep in cluster.endpoints] if cluster.endpoints else []
                })
        
        total_endpoints = sum(len(cluster.endpoints) for cluster in self.config.clusters.values())
        success_count = len(successful_registrations)
        failure_count = len(failed_registrations)
        
        if success_count > 0:
            logger.info(f"✅ Successfully registered {success_count} clusters with {total_endpoints} total endpoints")
        
        if failure_count > 0:
            logger.warning(f"⚠️ Failed to register {failure_count} clusters")
            for failure in failed_registrations:
                logger.warning(f"   • {failure['cluster_name']}: {failure['error']}")
        
        return {
            "successful": successful_registrations,
            "failed": failed_registrations,
            "total_clusters": len(self.config.clusters),
            "total_endpoints": total_endpoints,
            "success_rate": success_count / len(self.config.clusters) if self.config.clusters else 1.0
        }
    
    # Monitoring and Management Methods
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        if not self._running:
            return {"status": "stopped", "uptime": 0}
        
        uptime = time.time() - self._start_time
        
        # Get MCP layer stats
        mcp_stats = await self.mcp_layer.get_global_stats() if self.mcp_layer else {}
        
        # Get gateway stats
        gateway_stats = await self.gateway.get_stats() if self.gateway else {}
        
        return {
            "status": "healthy" if self._startup_completed else "starting",
            "uptime_seconds": uptime,
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "success_rate": (
                self._successful_requests / self._total_requests 
                if self._total_requests > 0 else 0.0
            ),
            "mcp_layer": mcp_stats,
            "gateway": gateway_stats,
            "configuration": {
                "max_services": self.config.mcp.max_services,
                "registered_services": len(self.config.clusters),
                "frontend_host": self.config.frontend.host,
                "frontend_port": self.config.frontend.port,
            }
        }
    
    async def get_service_stats(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for specific service or all services."""
        if not self.mcp_layer:
            return {}
        
        if service_name:
            return await self.mcp_layer.get_service_health(service_name)
        else:
            # Get stats for all services
            stats = {}
            for cluster_name in self.config.clusters.keys():
                try:
                    stats[cluster_name] = await self.mcp_layer.get_service_health(cluster_name)
                except Exception as e:
                    stats[cluster_name] = {"error": str(e)}
            return stats
    
    async def reload_configuration(self, new_config: BridgeConfig) -> None:
        """Reload bridge configuration without stopping."""
        logger.info("Reloading bridge configuration...")
        
        try:
            # Validate new configuration
            issues = new_config.validate_massive_scale()
            if issues:
                raise ConfigurationError(f"Invalid configuration: {'; '.join(issues)}")
            
            # Store old config for rollback
            old_config = self.config
            
            # Apply new configuration
            self.config = new_config
            
            # Update MCP layer configuration
            if self.mcp_layer:
                # Re-register services if needed
                await self._register_configured_services()
            
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            # Rollback on error
            self.config = old_config
            logger.error(f"Failed to reload configuration: {e}")
            raise
    
    # Performance Optimization Methods
    
    def enable_performance_mode(self) -> None:
        """Enable high-performance optimizations."""
        self.config.performance.enable_aggressive_caching = True
        self.config.performance.enable_batch_processing = True
        self.config.performance.enable_memory_optimization = True
        self.config.mcp.enable_compression = True
        self.config.mcp.enable_connection_pooling = True
        
        logger.info("Performance mode enabled")
    
    def enable_memory_optimization(self) -> None:
        """Enable memory usage optimizations."""
        self.config.performance.enable_memory_optimization = True
        self.config.performance.gc_threshold = 500  # More aggressive GC
        self.config.mcp.pool_recycle_time = 1800  # Shorter pool recycle
        
        logger.info("Memory optimization enabled")
    
    # Utility Methods
    
    def is_running(self) -> bool:
        """Check if bridge is running."""
        return self._running
    
    def is_ready(self) -> bool:
        """Check if bridge is ready to accept requests."""
        return self._running and self._startup_completed
    
    def get_service_count(self) -> int:
        """Get total number of registered services."""
        return sum(len(cluster.endpoints) for cluster in self.config.clusters.values())
    
    def get_supported_endpoints(self) -> List[str]:
        """Get list of all supported service endpoints."""
        endpoints = []
        for cluster in self.config.clusters.values():
            for endpoint in cluster.endpoints:
                endpoints.append(f"{cluster.name}: {endpoint.endpoint}")
        return endpoints


# Factory Functions and Convenience Methods

def create_universal_bridge(
    max_services: int = 1000,
    enable_performance_mode: bool = True,
    **config_overrides
) -> UniversalBridge:
    """Create a Universal Bridge with optimized configuration.
    
    Args:
        max_services: Maximum number of services to support
        enable_performance_mode: Enable performance optimizations
        **config_overrides: Configuration overrides
    
    Returns:
        Configured UniversalBridge instance
    """
    config = create_massive_scale_config(max_services)
    
    # Apply overrides
    for key, value in config_overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
        elif hasattr(config.frontend, key):
            setattr(config.frontend, key, value)
        elif hasattr(config.mcp, key):
            setattr(config.mcp, key, value)
    
    bridge = UniversalBridge(config)
    
    if enable_performance_mode:
        bridge.enable_performance_mode()
    
    return bridge


def quick_bridge(services: Dict[str, str], port: int = 8000) -> UniversalBridge:
    """Create and start a bridge quickly with a simple service mapping.
    
    Args:
        services: Dict mapping service names to endpoints {"name": "host:port"}
        port: Bridge port
    
    Example:
        bridge = quick_bridge({
            "user-service": "localhost:50051",
            "ai-model": "ml-server:50052"
        })
        bridge.run()
    """
    bridge = create_universal_bridge()
    
    # Register services
    for name, endpoint in services.items():
        bridge.register_service(name, endpoint)
    
    bridge.config.frontend.port = port
    
    return bridge


# Example usage and testing
async def run_example():
    """Example of how to use the Universal Bridge."""
    
    # Create bridge
    bridge = UniversalBridge()
    
    # Configure for massive scale
    bridge.configure_massive_scale(max_services=10000)
    
    # Register services
    bridge.register_service("user-service", "localhost:50051")
    bridge.register_service("order-service", "localhost:50052")
    bridge.register_service("ai-model", "ml-server:50053")
    
    # Register service clusters for load balancing
    bridge.register_service_cluster(
        "payment-cluster",
        ["payment1:50054", "payment2:50054", "payment3:50054"]
    )
    
    # Enable performance optimizations
    bridge.enable_performance_mode()
    
    # Start the bridge
    await bridge.start()
    
    try:
        # Bridge is now running and accepting REST requests
        # Any REST call to http://localhost:8000/api/{service-name}/* 
        # will be automatically converted to gRPC
        
        print("Bridge running at http://localhost:8000")
        print("Try: curl -X POST http://localhost:8000/api/user-service/create -d '{\"name\":\"John\"}'")
        
        # Keep running
        while bridge.is_running():
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await bridge.stop()


if __name__ == "__main__":
    # Run example
    asyncio.run(run_example()) 