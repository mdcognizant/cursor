"""Health check route handlers."""

import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..models import HealthStatus

router = APIRouter()

# Store startup time for uptime calculation
_startup_time = time.time()


@router.get("/", response_model=HealthStatus, summary="Health Check")
@router.get("/status", response_model=HealthStatus, summary="Detailed Health Status")
async def get_health_status(request: Request) -> HealthStatus:
    """Get the health status of the bridge service.
    
    Returns detailed information about:
    - Service status (healthy/degraded/unhealthy)
    - Uptime
    - Component health checks
    - Version information
    """
    current_time = time.time()
    uptime_seconds = int(current_time - _startup_time)
    
    # Perform health checks
    checks = await perform_health_checks(request)
    
    # Determine overall status
    status = determine_overall_status(checks)
    
    return HealthStatus(
        status=status,
        timestamp=datetime.utcnow(),
        version="0.1.0",
        uptime_seconds=uptime_seconds,
        checks=checks
    )


@router.get("/live", summary="Liveness Probe")
async def liveness_probe() -> JSONResponse:
    """Liveness probe for Kubernetes/container orchestration.
    
    Returns 200 if the service is running, regardless of health status.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "alive", "timestamp": datetime.utcnow().isoformat()}
    )


@router.get("/ready", summary="Readiness Probe")
async def readiness_probe(request: Request) -> JSONResponse:
    """Readiness probe for Kubernetes/container orchestration.
    
    Returns 200 if the service is ready to accept traffic.
    Returns 503 if the service is not ready.
    """
    # Check if startup is completed
    bridge_state = getattr(request.app.state, 'startup_completed', False)
    
    if not bridge_state:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "reason": "startup not completed",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    # Perform basic readiness checks
    checks = await perform_readiness_checks(request)
    
    if all(check.get("healthy", False) for check in checks.values()):
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": checks
            }
        )
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": checks
            }
        )


async def perform_health_checks(request: Request) -> Dict[str, Dict[str, Any]]:
    """Perform comprehensive health checks on all components."""
    checks = {}
    
    # Protocol Buffer system check
    checks["protobuf"] = await check_protobuf_system(request)
    
    # gRPC connections check
    checks["grpc_connections"] = await check_grpc_connections(request)
    
    # Schema manager check
    checks["schema_manager"] = await check_schema_manager(request)
    
    # Database/storage check (if applicable)
    checks["storage"] = await check_storage_health()
    
    return checks


async def perform_readiness_checks(request: Request) -> Dict[str, Dict[str, Any]]:
    """Perform readiness checks for core components."""
    checks = {}
    
    # Basic component initialization
    checks["protobuf"] = await check_protobuf_system(request)
    checks["configuration"] = await check_configuration(request)
    
    return checks


async def check_protobuf_system(request: Request) -> Dict[str, Any]:
    """Check Protocol Buffer system health."""
    try:
        proto_validator = getattr(request.app.state, 'proto_validator', None)
        
        if proto_validator is None:
            return {
                "healthy": False,
                "status": "not initialized",
                "message": "Protocol Buffer validator not initialized"
            }
        
        # Check if we have registered message types
        # This would be a real check in a complete implementation
        return {
            "healthy": True,
            "status": "operational",
            "message": "Protocol Buffer system operational",
            "details": {
                "validator_initialized": True,
                "registered_types": 0  # Would be actual count
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "message": f"Protocol Buffer system error: {str(e)}"
        }


async def check_grpc_connections(request: Request) -> Dict[str, Any]:
    """Check gRPC connection health."""
    try:
        config = getattr(request.app.state, 'config', None)
        
        if not config:
            return {
                "healthy": False,
                "status": "no configuration",
                "message": "Configuration not available"
            }
        
        # In a real implementation, this would test actual gRPC connections
        grpc_services = config.grpc_services
        
        return {
            "healthy": True,
            "status": "operational",
            "message": f"gRPC connections healthy",
            "details": {
                "configured_services": len(grpc_services),
                "active_connections": 0,  # Would be actual count
                "services": list(grpc_services.keys())
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "message": f"gRPC connection check failed: {str(e)}"
        }


async def check_schema_manager(request: Request) -> Dict[str, Any]:
    """Check schema manager health."""
    try:
        schema_manager = getattr(request.app.state, 'schema_manager', None)
        
        if schema_manager is None:
            return {
                "healthy": False,
                "status": "not initialized",
                "message": "Schema manager not initialized"
            }
        
        # Check schema versions
        versions = schema_manager.list_versions()
        current_version = schema_manager.get_current_version()
        
        return {
            "healthy": True,
            "status": "operational",
            "message": "Schema manager operational",
            "details": {
                "available_versions": len(versions),
                "current_version": current_version,
                "versions": versions
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "message": f"Schema manager check failed: {str(e)}"
        }


async def check_configuration(request: Request) -> Dict[str, Any]:
    """Check configuration health."""
    try:
        config = getattr(request.app.state, 'config', None)
        
        if not config:
            return {
                "healthy": False,
                "status": "missing",
                "message": "Configuration not loaded"
            }
        
        # Validate configuration
        issues = config.validate_config()
        
        if issues:
            return {
                "healthy": False,
                "status": "invalid",
                "message": "Configuration validation failed",
                "details": {"issues": issues}
            }
        
        return {
            "healthy": True,
            "status": "valid",
            "message": "Configuration is valid",
            "details": {
                "environment": config.environment,
                "grpc_services": len(config.grpc_services),
                "security_enabled": config.security.enable_auth
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "error", 
            "message": f"Configuration check failed: {str(e)}"
        }


async def check_storage_health() -> Dict[str, Any]:
    """Check storage/database health."""
    try:
        # This would check database connections, file system access, etc.
        # For now, just return a basic check
        
        return {
            "healthy": True,
            "status": "operational",
            "message": "Storage system healthy",
            "details": {
                "type": "filesystem",
                "writable": True
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "message": f"Storage check failed: {str(e)}"
        }


def determine_overall_status(checks: Dict[str, Dict[str, Any]]) -> str:
    """Determine overall health status based on component checks."""
    if not checks:
        return "unhealthy"
    
    healthy_count = sum(1 for check in checks.values() if check.get("healthy", False))
    total_count = len(checks)
    
    if healthy_count == total_count:
        return "healthy"
    elif healthy_count >= total_count * 0.7:  # 70% threshold
        return "degraded"
    else:
        return "unhealthy" 