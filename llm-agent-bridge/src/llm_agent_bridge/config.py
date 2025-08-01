"""Configuration classes for LLM Agent Bridge."""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import os


class GRPCServiceConfig(BaseModel):
    """Configuration for a single gRPC service."""
    
    name: str = Field(..., description="Service name")
    host: str = Field(..., description="gRPC service host")
    port: int = Field(..., ge=1, le=65535, description="gRPC service port")
    use_tls: bool = Field(default=True, description="Use TLS for connection")
    cert_file: Optional[str] = Field(default=None, description="Path to TLS certificate file")
    key_file: Optional[str] = Field(default=None, description="Path to TLS key file")
    ca_file: Optional[str] = Field(default=None, description="Path to CA certificate file")
    timeout: float = Field(default=30.0, ge=0.1, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retries")
    
    @property
    def endpoint(self) -> str:
        """Get the full gRPC endpoint."""
        return f"{self.host}:{self.port}"


class SecurityConfig(BaseModel):
    """Security configuration."""
    
    enable_auth: bool = Field(default=True, description="Enable authentication")
    jwt_secret: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiry_hours: int = Field(default=24, ge=1, description="JWT expiry in hours")
    
    # API Key configuration
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    require_api_key: bool = Field(default=False, description="Require API key for all requests")
    
    # Rate limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, ge=1, description="Requests per minute limit")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], description="CORS allowed methods")


class ServerConfig(BaseModel):
    """Server configuration."""
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    reload: bool = Field(default=False, description="Enable auto-reload for development")
    log_level: str = Field(default="info", description="Log level")
    
    # WebSocket configuration
    enable_websockets: bool = Field(default=True, description="Enable WebSocket endpoints")
    websocket_timeout: float = Field(default=300.0, ge=1.0, description="WebSocket timeout in seconds")


class ProtoConfig(BaseModel):
    """Protocol Buffers configuration."""
    
    proto_dir: str = Field(default="protos", description="Directory containing .proto files")
    output_dir: str = Field(default="generated", description="Output directory for compiled protos")
    auto_compile: bool = Field(default=True, description="Auto-compile .proto files on startup")
    include_dirs: List[str] = Field(default=[], description="Additional include directories")
    
    @validator("proto_dir", "output_dir")
    def validate_directories(cls, v):
        """Ensure directories exist or can be created."""
        if not os.path.exists(v):
            try:
                os.makedirs(v, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create directory {v}: {e}")
        return v


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""
    
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, ge=1, le=65535, description="Metrics server port")
    
    enable_health_check: bool = Field(default=True, description="Enable health check endpoint")
    health_check_path: str = Field(default="/health", description="Health check endpoint path")
    
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")
    jaeger_endpoint: Optional[str] = Field(default=None, description="Jaeger endpoint for tracing")


class BridgeConfig(BaseSettings):
    """Main configuration for LLM Agent Bridge."""
    
    # Server configuration
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    # Security configuration
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # gRPC services configuration
    grpc_services: Dict[str, GRPCServiceConfig] = Field(default={}, description="gRPC service configurations")
    
    # Protocol Buffers configuration
    proto: ProtoConfig = Field(default_factory=ProtoConfig)
    
    # Monitoring configuration
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Environment-specific settings
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    @classmethod
    def load_from_file(cls, config_file: str) -> "BridgeConfig":
        """Load configuration from a YAML or JSON file."""
        import json
        import yaml
        
        with open(config_file, "r") as f:
            if config_file.endswith((".yaml", ".yml")):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls(**data)
    
    def add_grpc_service(self, service_config: GRPCServiceConfig) -> None:
        """Add a gRPC service configuration."""
        self.grpc_services[service_config.name] = service_config
    
    def get_grpc_service(self, name: str) -> Optional[GRPCServiceConfig]:
        """Get gRPC service configuration by name."""
        return self.grpc_services.get(name)
    
    def validate_config(self) -> List[str]:
        """Validate the configuration and return list of issues."""
        issues = []
        
        if self.security.enable_auth and not self.security.jwt_secret:
            issues.append("JWT secret is required when authentication is enabled")
        
        if not self.grpc_services:
            issues.append("At least one gRPC service must be configured")
        
        for name, service in self.grpc_services.items():
            if service.use_tls and not service.cert_file:
                issues.append(f"TLS certificate file required for service '{name}'")
        
        return issues 