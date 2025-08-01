"""High-performance configuration system for Universal API Bridge."""

import os
import json
import asyncio
from typing import Dict, List, Optional, Union, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


# Security Configuration Classes
class AuthenticationType(str, Enum):
    """Supported authentication types."""
    JWT = "jwt"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    MTLS = "mtls"
    BASIC = "basic"
    BEARER = "bearer"


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


class SecurityConfig(BaseModel):
    """Enterprise-grade security configuration."""
    
    # Authentication & Authorization
    enable_authentication: bool = Field(default=True, description="Enable authentication")
    authentication_type: AuthenticationType = Field(default=AuthenticationType.JWT, description="Authentication type")
    jwt_secret_key: Optional[str] = Field(default=None, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(default=3600, ge=60, description="JWT expiration in seconds")
    
    # OAuth2 Configuration
    oauth2_issuer: Optional[str] = Field(default=None, description="OAuth2 issuer URL")
    oauth2_audience: Optional[str] = Field(default=None, description="OAuth2 audience")
    oauth2_jwks_uri: Optional[str] = Field(default=None, description="OAuth2 JWKS URI")
    
    # API Key Management
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    api_key_query_param: str = Field(default="api_key", description="API key query parameter")
    enable_api_key_rotation: bool = Field(default=True, description="Enable API key rotation")
    api_key_expiration: int = Field(default=86400, ge=3600, description="API key expiration in seconds")
    
    # mTLS Configuration
    enable_mtls: bool = Field(default=False, description="Enable mutual TLS")
    ca_cert_path: Optional[str] = Field(default=None, description="CA certificate path")
    server_cert_path: Optional[str] = Field(default=None, description="Server certificate path")
    server_key_path: Optional[str] = Field(default=None, description="Server key path")
    client_cert_verification: bool = Field(default=True, description="Verify client certificates")
    
    # Rate Limiting & Throttling
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_strategy: RateLimitStrategy = Field(default=RateLimitStrategy.TOKEN_BUCKET, description="Rate limiting strategy")
    default_rate_limit: int = Field(default=1000, ge=1, description="Default rate limit per minute")
    burst_limit: int = Field(default=100, ge=1, description="Burst limit")
    rate_limit_window: int = Field(default=60, ge=1, description="Rate limit window in seconds")
    
    # IP Security
    enable_ip_whitelist: bool = Field(default=False, description="Enable IP whitelist")
    ip_whitelist: List[str] = Field(default=[], description="IP whitelist")
    enable_ip_blacklist: bool = Field(default=True, description="Enable IP blacklist")
    ip_blacklist: List[str] = Field(default=[], description="IP blacklist")
    enable_geoblocking: bool = Field(default=False, description="Enable geographic blocking")
    blocked_countries: List[str] = Field(default=[], description="Blocked country codes")
    
    # Web Application Firewall (WAF)
    enable_waf: bool = Field(default=True, description="Enable WAF")
    waf_rules: List[str] = Field(default=[], description="Custom WAF rules")
    enable_ddos_protection: bool = Field(default=True, description="Enable DDoS protection")
    ddos_threshold: int = Field(default=10000, ge=100, description="DDoS threshold requests per minute")
    
    # Input Validation & Sanitization
    enable_input_validation: bool = Field(default=True, description="Enable input validation")
    max_request_size: int = Field(default=16777216, ge=1024, description="Max request size in bytes")
    enable_sql_injection_protection: bool = Field(default=True, description="Enable SQL injection protection")
    enable_xss_protection: bool = Field(default=True, description="Enable XSS protection")
    enable_csrf_protection: bool = Field(default=True, description="Enable CSRF protection")
    
    # Security Headers
    enable_security_headers: bool = Field(default=True, description="Enable security headers")
    hsts_max_age: int = Field(default=31536000, ge=0, description="HSTS max age")
    content_security_policy: str = Field(default="default-src 'self'", description="Content Security Policy")
    
    # Encryption
    enable_field_encryption: bool = Field(default=False, description="Enable field-level encryption")
    encryption_key: Optional[str] = Field(default=None, description="Encryption key")
    encryption_algorithm: str = Field(default="AES-256-GCM", description="Encryption algorithm")
    
    # Audit & Compliance
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    audit_log_level: str = Field(default="INFO", description="Audit log level")
    compliance_mode: str = Field(default="standard", description="Compliance mode (standard, strict, enterprise)")


# Enhanced Load Balancing Strategy
class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies for massive scale."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    IP_HASH = "ip_hash"
    RANDOM = "random"
    HEALTH_AWARE = "health_aware"
    RESPONSE_TIME = "response_time"
    RESOURCE_BASED = "resource_based"


class ServiceDiscoveryBackend(str, Enum):
    """Service discovery backends for distributed systems."""
    MEMORY = "memory"
    REDIS = "redis"
    ETCD = "etcd"
    CONSUL = "consul"
    KUBERNETES = "kubernetes"
    ZOOKEEPER = "zookeeper"


class CacheBackend(str, Enum):
    """Caching backends for multi-level caching."""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    HAZELCAST = "hazelcast"
    DISTRIBUTED = "distributed"


class ProtocolType(str, Enum):
    """Supported protocol types."""
    GRPC = "grpc"
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    WEBSOCKET = "websocket"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# Service Configuration Models
class ServiceEndpoint(BaseModel):
    """Individual service endpoint configuration."""
    
    host: str = Field(..., description="Service host")
    port: int = Field(..., ge=1, le=65535, description="Service port")
    protocol: ProtocolType = Field(default=ProtocolType.GRPC, description="Protocol type")
    weight: float = Field(default=1.0, ge=0.0, description="Load balancing weight")
    priority: int = Field(default=1, ge=1, description="Service priority")
    
    # TLS Configuration
    use_tls: bool = Field(default=True, description="Use TLS")
    cert_file: Optional[str] = Field(default=None, description="TLS certificate file")
    key_file: Optional[str] = Field(default=None, description="TLS key file")
    ca_file: Optional[str] = Field(default=None, description="CA certificate file")
    
    # Performance Configuration
    connection_pool_size: int = Field(default=100, ge=1, description="Connection pool size")
    max_concurrent_streams: int = Field(default=1000, ge=1, description="Max concurrent streams")
    keep_alive_time: int = Field(default=300, ge=1, description="Keep alive time in seconds")
    timeout: float = Field(default=30.0, ge=0.1, description="Request timeout")
    
    # Health Check
    health_check_path: str = Field(default="/health", description="Health check endpoint")
    health_check_interval: int = Field(default=30, ge=1, description="Health check interval")
    
    @property
    def endpoint(self) -> str:
        """Get the full endpoint string."""
        return f"{self.host}:{self.port}"


class ServiceCluster(BaseModel):
    """Service cluster configuration for load balancing."""
    
    name: str = Field(..., description="Cluster name")
    endpoints: List[ServiceEndpoint] = Field(..., min_items=1, description="Service endpoints")
    load_balancing: LoadBalancingStrategy = Field(default=LoadBalancingStrategy.ROUND_ROBIN)
    
    # Circuit Breaker Configuration
    circuit_breaker_enabled: bool = Field(default=True, description="Enable circuit breaker")
    failure_threshold: int = Field(default=5, ge=1, description="Failure threshold")
    recovery_timeout: int = Field(default=60, ge=1, description="Recovery timeout in seconds")
    
    # Service Discovery
    auto_discovery: bool = Field(default=False, description="Enable automatic service discovery")
    discovery_service: Optional[str] = Field(default=None, description="Service discovery backend")
    discovery_interval: int = Field(default=30, ge=1, description="Discovery check interval")


class MCPConfig(BaseModel):
    """Model Context Protocol configuration for massive connectivity (100k+ APIs)."""
    
    # Core MCP Settings - Enhanced for 100k scale
    max_services: int = Field(default=100000, ge=1, le=1000000, description="Maximum number of services")
    max_connections_per_service: int = Field(default=10000, ge=1, description="Max connections per service")
    connection_timeout: float = Field(default=30.0, ge=0.1, description="Connection timeout")
    idle_timeout: float = Field(default=300.0, ge=1.0, description="Idle connection timeout")
    
    # Distributed Service Registry - Enhanced for massive scale
    registry_backend: ServiceDiscoveryBackend = Field(default=ServiceDiscoveryBackend.ETCD, description="Registry backend")
    registry_hosts: List[str] = Field(default=["localhost:2379"], description="Registry cluster hosts")
    registry_username: Optional[str] = Field(default=None, description="Registry username")
    registry_password: Optional[str] = Field(default=None, description="Registry password")
    registry_ttl: int = Field(default=30, ge=1, description="Service TTL in registry")
    registry_heartbeat_interval: int = Field(default=10, ge=1, description="Heartbeat interval")
    enable_registry_clustering: bool = Field(default=True, description="Enable registry clustering")
    registry_replication_factor: int = Field(default=3, ge=1, description="Registry replication factor")
    
    # Advanced Load Balancing
    global_load_balancing: LoadBalancingStrategy = Field(default=LoadBalancingStrategy.HEALTH_AWARE)
    enable_sticky_sessions: bool = Field(default=False, description="Enable sticky sessions")
    session_affinity_timeout: int = Field(default=3600, ge=60, description="Session affinity timeout")
    enable_health_aware_routing: bool = Field(default=True, description="Enable health-aware routing")
    health_check_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Health check threshold")
    
    # Enhanced Circuit Breaker
    global_circuit_breaker: bool = Field(default=True, description="Enable global circuit breaker")
    max_failure_rate: float = Field(default=0.5, ge=0.0, le=1.0, description="Max failure rate")
    circuit_breaker_timeout: int = Field(default=60, ge=1, description="Circuit breaker timeout")
    half_open_requests: int = Field(default=10, ge=1, description="Half-open state request limit")
    enable_adaptive_circuit_breaker: bool = Field(default=True, description="Enable adaptive circuit breaker")
    
    # Advanced Connection Pooling
    enable_connection_pooling: bool = Field(default=True, description="Enable connection pooling")
    pool_min_size: int = Field(default=10, ge=1, description="Pool minimum size")
    pool_max_size: int = Field(default=1000, ge=1, description="Pool maximum size")
    pool_recycle_time: int = Field(default=3600, ge=1, description="Pool recycle time in seconds")
    pool_overflow: int = Field(default=100, ge=0, description="Pool overflow connections")
    enable_pool_pre_ping: bool = Field(default=True, description="Enable pool pre-ping")
    enable_pool_reset_on_return: bool = Field(default=True, description="Enable pool reset on return")
    
    # Multi-Level Caching Strategy
    enable_response_caching: bool = Field(default=True, description="Enable response caching")
    l1_cache_backend: CacheBackend = Field(default=CacheBackend.MEMORY, description="L1 cache backend")
    l2_cache_backend: CacheBackend = Field(default=CacheBackend.REDIS, description="L2 cache backend")
    l3_cache_backend: CacheBackend = Field(default=CacheBackend.DISTRIBUTED, description="L3 cache backend")
    l1_cache_size: int = Field(default=10000, ge=1, description="L1 cache max entries")
    l2_cache_size: int = Field(default=1000000, ge=1, description="L2 cache max entries")
    cache_ttl: int = Field(default=300, ge=1, description="Default cache TTL")
    cache_warm_up_enabled: bool = Field(default=True, description="Enable cache warm-up")
    cache_compression_enabled: bool = Field(default=True, description="Enable cache compression")
    
    # Performance Optimization for 100k scale
    enable_compression: bool = Field(default=True, description="Enable gRPC compression")
    compression_algorithm: str = Field(default="gzip", description="Compression algorithm")
    enable_multiplexing: bool = Field(default=True, description="Enable connection multiplexing")
    max_concurrent_streams: int = Field(default=1000, ge=1, description="Max concurrent streams per connection")
    enable_flow_control: bool = Field(default=True, description="Enable flow control")
    
    # Distributed Coordination
    enable_distributed_locks: bool = Field(default=True, description="Enable distributed locks")
    lock_timeout: int = Field(default=30, ge=1, description="Distributed lock timeout")
    enable_leader_election: bool = Field(default=True, description="Enable leader election")
    enable_sharding: bool = Field(default=True, description="Enable service sharding")
    shard_count: int = Field(default=128, ge=1, description="Number of shards")
    
    # Resilience Patterns
    enable_bulkhead_pattern: bool = Field(default=True, description="Enable bulkhead pattern")
    bulkhead_max_concurrent: int = Field(default=100, ge=1, description="Bulkhead max concurrent requests")
    enable_timeout_pattern: bool = Field(default=True, description="Enable timeout pattern")
    default_timeout: float = Field(default=30.0, ge=0.1, description="Default operation timeout")
    enable_retry_pattern: bool = Field(default=True, description="Enable retry pattern")
    max_retry_attempts: int = Field(default=3, ge=0, description="Max retry attempts")
    retry_backoff_multiplier: float = Field(default=2.0, ge=1.0, description="Retry backoff multiplier")


class FrontendConfig(BaseModel):
    """Frontend gateway configuration."""
    
    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    
    # Performance Settings
    max_connections: int = Field(default=100000, ge=1, description="Maximum concurrent connections")
    keep_alive_timeout: int = Field(default=300, ge=1, description="Keep alive timeout")
    request_timeout: int = Field(default=30, ge=1, description="Request timeout")
    max_request_size: int = Field(default=16777216, ge=1024, description="Max request size in bytes")
    
    # Protocol Support
    enable_http2: bool = Field(default=True, description="Enable HTTP/2")
    enable_websockets: bool = Field(default=True, description="Enable WebSocket support")
    enable_graphql: bool = Field(default=False, description="Enable GraphQL gateway")
    
    # Compression
    enable_compression: bool = Field(default=True, description="Enable response compression")
    compression_threshold: int = Field(default=1024, ge=1, description="Compression threshold in bytes")
    
    # Security
    enable_cors: bool = Field(default=True, description="Enable CORS")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    # Rate Limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=10000, ge=1, description="Rate limit per minute")
    
    # Caching
    enable_static_caching: bool = Field(default=True, description="Enable static content caching")
    cache_control_max_age: int = Field(default=3600, ge=0, description="Cache control max age")


class MonitoringConfig(BaseModel):
    """Enhanced monitoring and observability configuration for 100k+ APIs."""
    
    # Core Metrics
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, ge=1, le=65535, description="Metrics port")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    enable_custom_metrics: bool = Field(default=True, description="Enable custom metrics")
    
    # Health Checks
    enable_health_checks: bool = Field(default=True, description="Enable health checks")
    health_check_interval: int = Field(default=10, ge=1, description="Health check interval")
    health_check_timeout: int = Field(default=5, ge=1, description="Health check timeout")
    enable_deep_health_checks: bool = Field(default=True, description="Enable deep health checks")
    
    # OpenTelemetry Distributed Tracing
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    tracing_backend: str = Field(default="jaeger", description="Tracing backend (jaeger, zipkin, datadog)")
    tracing_endpoint: Optional[str] = Field(default="http://localhost:14268/api/traces", description="Tracing endpoint")
    tracing_service_name: str = Field(default="universal-api-bridge", description="Service name for tracing")
    sampling_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="Trace sampling rate")
    enable_trace_correlation: bool = Field(default=True, description="Enable trace correlation")
    
    # Advanced Tracing Configuration
    enable_span_attributes: bool = Field(default=True, description="Enable span attributes")
    enable_trace_baggage: bool = Field(default=True, description="Enable trace baggage")
    trace_id_ratio_based_sampler: float = Field(default=0.1, ge=0.0, le=1.0, description="Trace ID ratio based sampler")
    enable_parent_based_sampler: bool = Field(default=True, description="Enable parent based sampler")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json, text)")
    enable_access_logs: bool = Field(default=True, description="Enable access logs")
    enable_structured_logging: bool = Field(default=True, description="Enable structured logging")
    log_retention_days: int = Field(default=30, ge=1, description="Log retention in days")
    
    # Performance Monitoring
    enable_performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")
    enable_memory_profiling: bool = Field(default=False, description="Enable memory profiling")
    enable_cpu_profiling: bool = Field(default=False, description="Enable CPU profiling")
    profiling_sample_rate: float = Field(default=0.01, ge=0.0, le=1.0, description="Profiling sample rate")
    
    # Alerting & Notifications
    enable_alerting: bool = Field(default=True, description="Enable alerting")
    alert_webhook: Optional[str] = Field(default=None, description="Alert webhook URL")
    alert_channels: List[str] = Field(default=[], description="Alert channels (slack, email, pagerduty)")
    alert_thresholds: Dict[str, float] = Field(
        default={
            "error_rate": 0.05,
            "latency_p99": 1000.0,
            "cpu_usage": 0.8,
            "memory_usage": 0.8,
            "connection_pool_exhaustion": 0.9
        },
        description="Alert thresholds"
    )
    
    # Service Mesh Integration
    enable_service_mesh: bool = Field(default=False, description="Enable service mesh integration")
    service_mesh_type: str = Field(default="istio", description="Service mesh type (istio, linkerd, consul)")
    enable_envoy_stats: bool = Field(default=False, description="Enable Envoy proxy stats")
    
    # Business Metrics
    enable_business_metrics: bool = Field(default=True, description="Enable business metrics")
    business_metric_tags: List[str] = Field(default=[], description="Business metric tags")


class PerformanceConfig(BaseModel):
    """Performance optimization configuration."""
    
    # Async Settings
    max_workers: int = Field(default=100, ge=1, description="Max async workers")
    worker_connections: int = Field(default=1000, ge=1, description="Worker connections")
    
    # Memory Management
    enable_memory_optimization: bool = Field(default=True, description="Enable memory optimization")
    gc_threshold: int = Field(default=1000, ge=1, description="Garbage collection threshold")
    
    # Caching Strategy
    enable_aggressive_caching: bool = Field(default=True, description="Enable aggressive caching")
    cache_warm_up: bool = Field(default=True, description="Enable cache warm-up")
    
    # Connection Optimization
    tcp_nodelay: bool = Field(default=True, description="Enable TCP_NODELAY")
    tcp_keepalive: bool = Field(default=True, description="Enable TCP keepalive")
    
    # Batch Processing
    enable_batch_processing: bool = Field(default=True, description="Enable batch processing")
    batch_size: int = Field(default=100, ge=1, description="Batch processing size")
    batch_timeout: float = Field(default=0.01, ge=0.001, description="Batch timeout in seconds")


class BridgeConfig(BaseSettings):
    """Main configuration for Universal API Bridge - Enterprise Grade for 100k+ APIs."""
    
    # Core Components
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    # Service Clusters
    clusters: Dict[str, ServiceCluster] = Field(default={}, description="Service clusters")
    
    # Global Settings
    environment: str = Field(default="production", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    deployment_mode: str = Field(default="distributed", description="Deployment mode (standalone, distributed, kubernetes)")
    
    # Schema Translation
    enable_auto_schema_discovery: bool = Field(default=True, description="Enable automatic schema discovery")
    schema_cache_ttl: int = Field(default=3600, ge=1, description="Schema cache TTL")
    enable_schema_validation: bool = Field(default=True, description="Enable schema validation")
    
    # Enterprise Features
    enable_multi_tenancy: bool = Field(default=False, description="Enable multi-tenancy")
    tenant_isolation_level: str = Field(default="namespace", description="Tenant isolation level")
    enable_disaster_recovery: bool = Field(default=False, description="Enable disaster recovery")
    backup_interval: int = Field(default=3600, ge=60, description="Backup interval in seconds")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    def add_service_cluster(self, cluster: ServiceCluster) -> None:
        """Add a service cluster configuration."""
        self.clusters[cluster.name] = cluster
    
    def get_service_cluster(self, name: str) -> Optional[ServiceCluster]:
        """Get service cluster by name."""
        return self.clusters.get(name)
    
    def get_all_endpoints(self) -> List[ServiceEndpoint]:
        """Get all service endpoints across all clusters."""
        endpoints = []
        for cluster in self.clusters.values():
            endpoints.extend(cluster.endpoints)
        return endpoints
    
    def get_total_service_count(self) -> int:
        """Get total number of configured services."""
        return sum(len(cluster.endpoints) for cluster in self.clusters.values())
    
    def validate_massive_scale(self) -> List[str]:
        """Validate configuration for massive scale deployment."""
        issues = []
        
        total_services = self.get_total_service_count()
        
        # Check if we're within MCP limits
        if total_services > self.mcp.max_services:
            issues.append(
                f"Total services ({total_services}) exceeds MCP limit ({self.mcp.max_services})"
            )
        
        # Check connection pool sizes
        total_connections = sum(
            endpoint.connection_pool_size 
            for endpoint in self.get_all_endpoints()
        )
        
        max_possible_connections = self.mcp.max_services * self.mcp.max_connections_per_service
        if total_connections > max_possible_connections:
            issues.append(
                f"Total connection pools ({total_connections}) may exceed system limits"
            )
        
        # Check frontend capacity
        if self.frontend.max_connections < total_services * 10:
            issues.append(
                "Frontend max_connections may be too low for the number of services"
            )
        
        # Validate cache backend for large scale
        if total_services > 1000 and self.mcp.cache_backend == "memory":
            issues.append(
                "Memory cache backend may not be suitable for 1000+ services. Consider Redis."
            )
        
        return issues
    
    @classmethod
    def load_from_file(cls, config_file: str) -> "BridgeConfig":
        """Load configuration from file with optimizations for large configs."""
        import yaml
        import orjson
        
        config_path = Path(config_file)
        
        # Use optimized JSON parsing for large files
        with open(config_path, "rb") as f:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                data = orjson.loads(f.read())
        
        return cls(**data)
    
    async def save_to_file(self, config_file: str, optimize_for_size: bool = True) -> None:
        """Save configuration to file with optimizations."""
        import orjson
        
        config_dict = self.dict(exclude_none=True)
        
        if optimize_for_size:
            # Use orjson for better performance with large configs
            with open(config_file, "wb") as f:
                f.write(orjson.dumps(config_dict, option=orjson.OPT_INDENT_2))
        else:
            import json
            with open(config_file, "w") as f:
                json.dump(config_dict, f, indent=2)


# Factory functions for massive scale
def create_massive_scale_config(num_services: int = 100000) -> BridgeConfig:
    """Create optimized configuration for massive scale deployment (100k+ APIs)."""
    
    # Calculate optimal settings based on service count
    optimal_workers = min(max(num_services // 1000, 8), 64)
    optimal_connections = min(num_services * 100, 10000000)
    optimal_pool_size = min(max(num_services // 100, 100), 10000)
    
    config = BridgeConfig()
    
    # Optimize frontend for massive scale
    config.frontend.workers = optimal_workers
    config.frontend.max_connections = optimal_connections
    config.frontend.rate_limit_per_minute = num_services * 1000
    config.frontend.enable_http2 = True
    config.frontend.enable_compression = True
    
    # Optimize MCP layer for 100k+ services
    config.mcp.max_services = num_services
    config.mcp.max_connections_per_service = optimal_pool_size
    config.mcp.registry_backend = ServiceDiscoveryBackend.ETCD
    config.mcp.enable_compression = True
    config.mcp.enable_response_caching = True
    config.mcp.enable_multiplexing = True
    config.mcp.enable_distributed_locks = True
    config.mcp.enable_sharding = True
    
    # Configure security for enterprise scale
    config.security.enable_authentication = True
    config.security.authentication_type = AuthenticationType.JWT
    config.security.enable_rate_limiting = True
    config.security.rate_limit_strategy = RateLimitStrategy.TOKEN_BUCKET
    config.security.default_rate_limit = num_services // 10
    config.security.enable_waf = True
    config.security.enable_ddos_protection = True
    
    # Optimize performance settings for massive scale
    config.performance.max_workers = optimal_workers * 20
    config.performance.worker_connections = optimal_pool_size
    config.performance.enable_aggressive_caching = True
    config.performance.enable_batch_processing = True
    config.performance.batch_size = min(1000, num_services // 100)
    
    # Configure monitoring for 100k+ services with adaptive sampling
    config.monitoring.sampling_rate = max(0.001, 1.0 / num_services)  # Adaptive sampling
    config.monitoring.enable_tracing = True
    config.monitoring.enable_performance_monitoring = True
    config.monitoring.enable_alerting = True
    
    return config


def create_security_hardened_config() -> BridgeConfig:
    """Create security-hardened configuration for enterprise deployment."""
    config = create_massive_scale_config(100000)
    
    # Enhanced security settings
    config.security.enable_mtls = True
    config.security.enable_ip_whitelist = True
    config.security.enable_waf = True
    config.security.enable_ddos_protection = True
    config.security.enable_input_validation = True
    config.security.enable_sql_injection_protection = True
    config.security.enable_xss_protection = True
    config.security.enable_csrf_protection = True
    config.security.enable_security_headers = True
    config.security.enable_audit_logging = True
    config.security.compliance_mode = "enterprise"
    
    # Enhanced monitoring for security
    config.monitoring.enable_alerting = True
    config.monitoring.log_level = "DEBUG"
    config.monitoring.enable_structured_logging = True
    
    return config


def create_cluster_from_endpoints(
    name: str, 
    endpoints: List[str], 
    load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
) -> ServiceCluster:
    """Create a service cluster from endpoint strings."""
    
    service_endpoints = []
    for endpoint in endpoints:
        host, port = endpoint.split(":")
        service_endpoints.append(ServiceEndpoint(
            host=host,
            port=int(port)
        ))
    
    return ServiceCluster(
        name=name,
        endpoints=service_endpoints,
        load_balancing=load_balancing
    ) 