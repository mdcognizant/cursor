"""Main FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

from ..config import BridgeConfig
from ..exceptions import BridgeError, GRPCConnectionError, ValidationError, AuthenticationError
from ..proto.validator import ProtoValidator
from ..proto.schema_manager import SchemaManager
from ..tools.proto_compiler import auto_compile_protos
from .middleware import SecurityMiddleware, RateLimitMiddleware, LoggingMiddleware
from .routes import agent_router, task_router, health_router, schema_router, websocket_router

logger = logging.getLogger(__name__)


async def setup_proto_system(config: BridgeConfig) -> tuple[ProtoValidator, SchemaManager]:
    """Set up the Protocol Buffer system."""
    try:
        # Auto-compile proto files if needed
        if not auto_compile_protos(config.proto):
            raise Exception("Failed to compile Protocol Buffer files")
        
        # Initialize validator and schema manager
        validator = ProtoValidator()
        schema_manager = SchemaManager(config.proto.output_dir)
        
        # TODO: Load generated protobuf modules and register them
        # This would be implemented after proto compilation
        
        logger.info("Protocol Buffer system initialized successfully")
        return validator, schema_manager
        
    except Exception as e:
        logger.error(f"Failed to setup Protocol Buffer system: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting LLM Agent Bridge application...")
    
    try:
        # Setup Protocol Buffer system
        validator, schema_manager = await setup_proto_system(app.state.config)
        app.state.proto_validator = validator
        app.state.schema_manager = schema_manager
        
        # Initialize gRPC client connections
        # This would be implemented in the gRPC client module
        
        logger.info("Application startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    finally:
        logger.info("Shutting down LLM Agent Bridge application...")
        # Cleanup resources here


def create_app(config: BridgeConfig = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = BridgeConfig()
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="LLM Agent Bridge",
        description="""
        A REST to gRPC bridge for LLM agent communication.
        
        This API provides a RESTful interface for communicating with multiple 
        LLM agents via gRPC services using Protocol Buffers for efficient 
        message serialization.
        
        ## Features
        
        - **Agent Communication**: Send messages to agents and receive responses
        - **Task Orchestration**: Execute complex tasks across multiple agents  
        - **Real-time Updates**: WebSocket support for live agent communication
        - **Schema Validation**: Built-in Protocol Buffer validation and versioning
        - **Security**: JWT authentication and API key support
        - **Monitoring**: Health checks and metrics endpoints
        """,
        version="0.1.0",
        contact={
            "name": "LLM Agent Bridge Team",
            "email": "contact@example.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
        openapi_url="/openapi.json" if config.debug else None,
        lifespan=lifespan
    )
    
    # Store config in app state
    app.state.config = config
    
    # Configure CORS
    if config.security.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.security.cors_origins,
            allow_credentials=True,
            allow_methods=config.security.cors_methods,
            allow_headers=["*"],
        )
    
    # Add compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    
    if config.security.enable_rate_limiting:
        app.add_middleware(
            RateLimitMiddleware,
            calls=config.security.rate_limit_per_minute,
            period=60
        )
    
    if config.security.enable_auth:
        app.add_middleware(SecurityMiddleware, config=config.security)
    
    # Add exception handlers
    add_exception_handlers(app)
    
    # Include routers
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(schema_router, prefix="/schema", tags=["Schema"])
    app.include_router(agent_router, prefix="/agents", tags=["Agents"])
    app.include_router(task_router, prefix="/tasks", tags=["Tasks"])
    
    if config.server.enable_websockets:
        app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
    
    # Custom OpenAPI schema
    app.openapi = lambda: get_custom_openapi(app)
    
    return app


def add_exception_handlers(app: FastAPI) -> None:
    """Add custom exception handlers."""
    
    @app.exception_handler(BridgeError)
    async def bridge_error_handler(request: Request, exc: BridgeError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "field": exc.field,
                    "value": exc.value
                }
            }
        )
    
    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message
                }
            }
        )
    
    @app.exception_handler(GRPCConnectionError)
    async def grpc_error_handler(request: Request, exc: GRPCConnectionError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "service": exc.service_name,
                    "endpoint": exc.endpoint
                }
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred"
                }
            }
        )


def get_custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom schema components
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "details": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["code", "message"]
                }
            },
            "required": ["error"]
        }
    })
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Add global security
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def run_server(config: BridgeConfig = None) -> None:
    """Run the FastAPI server with uvicorn."""
    if config is None:
        config = BridgeConfig()
    
    app = create_app(config)
    
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        workers=config.server.workers if not config.server.reload else 1,
        reload=config.server.reload,
        log_level=config.server.log_level.lower(),
        access_log=True,
        loop="asyncio"
    ) 