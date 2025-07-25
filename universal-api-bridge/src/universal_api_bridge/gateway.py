"""Universal Gateway for REST-to-gRPC conversion and routing."""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import traceback

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import BridgeConfig
from .exceptions import *
from .mcp import MCPLayer
from .utils import format_error_for_user, HelpfulMessages

logger = logging.getLogger(__name__)


@dataclass
class RequestContext:
    """Context for a REST request being processed."""
    request_id: str
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    body: Optional[Dict[str, Any]] = None
    start_time: float = 0.0
    

class UniversalGateway:
    """Universal Gateway that converts REST requests to gRPC calls."""
    
    def __init__(self, config: BridgeConfig, mcp_layer: MCPLayer, schema_translator=None):
        self.config = config
        self.mcp_layer = mcp_layer
        self.schema_translator = schema_translator
        self.app = FastAPI(
            title="Universal API Bridge",
            description="REST-to-gRPC Universal Gateway",
            version="1.0.0"
        )
        self.setup_middleware()
        self.setup_routes()
        self._server = None
        self._running = False
        
    def setup_middleware(self) -> None:
        """Set up FastAPI middleware."""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            try:
                response = await call_next(request)
                process_time = time.time() - start_time
                logger.info(
                    f"{request.method} {request.url.path} "
                    f"-> {response.status_code} ({process_time*1000:.2f}ms)"
                )
                return response
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(
                    f"{request.method} {request.url.path} "
                    f"-> ERROR ({process_time*1000:.2f}ms): {e}"
                )
                raise
                
    def setup_routes(self) -> None:
        """Set up API routes."""
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            mcp_health = await self.mcp_layer.get_global_stats()
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "mcp_layer": mcp_health,
                "gateway": "operational"
            }
            
        # Universal REST-to-gRPC endpoint
        @self.app.api_route(
            "/api/{service_path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        )
        async def universal_endpoint(request: Request, service_path: str):
            """Universal endpoint that converts REST to gRPC."""
            return await self.handle_rest_request(request, service_path)
            
        # Direct service endpoints
        @self.app.api_route(
            "/{service_name}/{method_path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        async def service_endpoint(request: Request, service_name: str, method_path: str):
            """Direct service endpoint routing."""
            full_path = f"{service_name}/{method_path}"
            return await self.handle_rest_request(request, full_path)
            
    async def handle_rest_request(self, request: Request, service_path: str) -> Union[JSONResponse, StreamingResponse]:
        """Handle REST request and convert to gRPC."""
        
        request_id = f"req_{int(time.time() * 1000000)}"
        start_time = time.time()
        
        try:
            # Extract request context
            context = await self._extract_request_context(request, service_path, request_id)
            
            # Determine target service
            service_name = await self._determine_service(context)
            
            # Convert REST to gRPC
            grpc_request = await self._convert_rest_to_grpc(context)
            
            # Execute via MCP layer
            grpc_response = await self.mcp_layer.execute_request(
                service_name=service_name,
                method="ProcessRequest",
                request=grpc_request,
                metadata={
                    "request_id": request_id,
                    "rest_method": context.method,
                    "rest_path": context.path
                }
            )
            
            # Convert gRPC response back to REST
            rest_response = await self._convert_grpc_to_rest(grpc_response, context)
            
            # Log success
            execution_time = time.time() - start_time
            logger.info(
                f"✅ REST-to-gRPC conversion successful: {context.method} {context.path} "
                f"-> {service_name} ({execution_time*1000:.2f}ms)"
            )
            
            return JSONResponse(
                content=rest_response,
                status_code=200,
                headers={
                    "X-Request-ID": request_id,
                    "X-Service": service_name,
                    "X-Execution-Time": f"{execution_time*1000:.2f}ms",
                    "X-Protocol": "REST-to-gRPC"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Request processing error: {e}")
            logger.error(traceback.format_exc())
            
            error_response = format_error_for_user(
                error=e,
                context={
                    "request_id": request_id,
                    "method": request.method,
                    "path": service_path,
                    "execution_time_ms": execution_time * 1000
                },
                helpful_message=HelpfulMessages.get_conversion_error_help()
            )
            
            return JSONResponse(
                content=error_response,
                status_code=500,
                headers={
                    "X-Request-ID": request_id,
                    "X-Error": "conversion_failed"
                }
            )
            
    async def _extract_request_context(self, request: Request, service_path: str, request_id: str) -> RequestContext:
        """Extract context from REST request."""
        
        # Get headers
        headers = dict(request.headers)
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                if "application/json" in headers.get("content-type", ""):
                    body_bytes = await request.body()
                    if body_bytes:
                        body = json.loads(body_bytes.decode('utf-8'))
                else:
                    # Handle form data or other content types
                    body = {"raw": await request.body()}
            except Exception as e:
                logger.warning(f"Failed to parse request body: {e}")
                body = {"error": "body_parse_failed"}
                
        return RequestContext(
            request_id=request_id,
            method=request.method,
            path=f"/api/{service_path}",
            headers=headers,
            query_params=query_params,
            body=body,
            start_time=time.time()
        )
        
    async def _determine_service(self, context: RequestContext) -> str:
        """Determine target gRPC service from REST request."""
        
        # Extract service name from path
        path_parts = context.path.strip("/").split("/")
        
        # Remove 'api' prefix if present
        if path_parts and path_parts[0] == "api":
            path_parts = path_parts[1:]
            
        if not path_parts:
            raise HTTPException(
                status_code=400,
                detail="Invalid API path: service name required"
            )
            
        # Map common REST paths to services
        service_mappings = {
            "users": "user_service",
            "orders": "order_service", 
            "payments": "payment_service",
            "analytics": "analytics_service",
            "streaming": "streaming_service",
            "batch": "payment_service",  # Batch payments
            "realtime": "analytics_service"  # Real-time analytics
        }
        
        base_service = path_parts[0]
        service_name = service_mappings.get(base_service, f"{base_service}_service")
        
        logger.debug(f"Mapped REST path '{context.path}' to service '{service_name}'")
        return service_name
        
    async def _convert_rest_to_grpc(self, context: RequestContext) -> Dict[str, Any]:
        """Convert REST request to gRPC format."""
        
        grpc_request = {
            "metadata": {
                "request_id": context.request_id,
                "rest_method": context.method,
                "rest_path": context.path,
                "headers": context.headers,
                "timestamp": context.start_time,
                "protocol_version": "rest-to-grpc/1.0"
            }
        }
        
        # Add request data based on HTTP method
        if context.method == "GET":
            grpc_request["query_parameters"] = context.query_params
            
            # Extract resource ID from path
            path_parts = context.path.strip("/").split("/")
            if len(path_parts) > 2 and path_parts[-1]:
                try:
                    # Try to parse as ID
                    resource_id = path_parts[-1]
                    grpc_request["resource_id"] = resource_id
                except:
                    pass
                    
        elif context.method in ["POST", "PUT", "PATCH"]:
            if context.body:
                grpc_request["request_body"] = context.body
            if context.query_params:
                grpc_request["query_parameters"] = context.query_params
                
            # For PUT/PATCH, extract resource ID
            if context.method in ["PUT", "PATCH"]:
                path_parts = context.path.strip("/").split("/")
                if len(path_parts) > 2 and path_parts[-1]:
                    grpc_request["resource_id"] = path_parts[-1]
                    
        elif context.method == "DELETE":
            path_parts = context.path.strip("/").split("/")
            if len(path_parts) > 2 and path_parts[-1]:
                grpc_request["resource_id"] = path_parts[-1]
            if context.query_params:
                grpc_request["query_parameters"] = context.query_params
                
        # Add service context
        grpc_request["service_context"] = {
            "protocol": "grpc",
            "compression": "gzip",
            "timeout_seconds": 30,
            "retry_policy": {
                "max_attempts": 3,
                "backoff_multiplier": 2.0
            }
        }
        
        return grpc_request
        
    async def _convert_grpc_to_rest(self, grpc_response: Any, context: RequestContext) -> Dict[str, Any]:
        """Convert gRPC response back to REST format."""
        
        # Handle different response types
        if isinstance(grpc_response, dict):
            # Standard response
            rest_response = {
                "status": "success",
                "data": grpc_response,
                "meta": {
                    "request_id": context.request_id,
                    "method": context.method,
                    "path": context.path,
                    "execution_time_ms": (time.time() - context.start_time) * 1000,
                    "protocol": "REST-via-gRPC"
                }
            }
        elif isinstance(grpc_response, list):
            # Batch or streaming response
            rest_response = {
                "status": "success",
                "data": grpc_response,
                "meta": {
                    "request_id": context.request_id,
                    "count": len(grpc_response),
                    "type": "batch",
                    "execution_time_ms": (time.time() - context.start_time) * 1000
                }
            }
        else:
            # Fallback for other types
            rest_response = {
                "status": "success", 
                "data": str(grpc_response) if grpc_response else None,
                "meta": {
                    "request_id": context.request_id,
                    "execution_time_ms": (time.time() - context.start_time) * 1000
                }
            }
            
        return rest_response
        
    async def start(self) -> Dict[str, Any]:
        """Start the universal gateway."""
        try:
            host = self.config.frontend.host
            port = self.config.frontend.port
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
            self._server = uvicorn.Server(config)
            self._running = True
            
            # Start in background task
            self._server_task = asyncio.create_task(self._server.serve())
            
            logger.info(f"✅ Universal Gateway started on {host}:{port}")
            
            return {
                "status": "started",
                "host": host,
                "port": port,
                "endpoints": {
                    "health": f"http://{host}:{port}/health",
                    "universal_api": f"http://{host}:{port}/api/{{service}}/{{method}}",
                    "direct_service": f"http://{host}:{port}/{{service}}/{{method}}"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to start Universal Gateway: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
            
    async def stop(self) -> None:
        """Stop the universal gateway."""
        if self._running and self._server:
            self._running = False
            self._server.should_exit = True
            
            if hasattr(self, '_server_task'):
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
                    
            logger.info("Universal Gateway stopped")
            
    def is_running(self) -> bool:
        """Check if gateway is running."""
        return self._running
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "status": "running" if self._running else "stopped",
            "endpoints_registered": len(self.app.routes),
            "host": self.config.frontend.host,
            "port": self.config.frontend.port
        } 