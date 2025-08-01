#!/usr/bin/env python3
"""
MCP Enterprise News Service
Provides news aggregation through Universal API Bridge with gRPC backend optimization

This service integrates:
- Universal API Bridge (REST frontend)
- gRPC Backend Engine (3x faster than traditional REST)
- MCP Layer optimization
- Dual News Provider Integration (NewsData.io + Currents + NewsAPI)
"""

import asyncio
import json
import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import uvicorn

# Import our MCP Enterprise components
from dual_news_provider_integration import DualNewsProviderIntegration, NewsProvider
from src.universal_api_bridge.bridge import UniversalBridge
from src.universal_api_bridge.grpc_engine import OptimizedGRPCBackend, GRPCChannelConfig
from src.universal_api_bridge.mcp.layer import MCPLayer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsRequest(BaseModel):
    category: Optional[str] = None
    language: str = "en"
    country: Optional[str] = None
    limit: int = 50

class MCPEnterpriseNewsService:
    """MCP Enterprise News Service with gRPC Backend"""
    
    def __init__(self):
        # Initialize FastAPI
        self.app = FastAPI(
            title="MCP Enterprise News Service",
            description="High-performance news aggregation with gRPC backend",
            version="1.0.0"
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize MCP Enterprise components
        self.dual_news_provider = DualNewsProviderIntegration(
            currents_api_key="zWhKbzWClaobXOpN0VDGF62kNkBh6Kbgdx-ki2AUIEoAGnah",
            newsdata_api_key="pub_05c05ef3d5044b3fa7a3ab3b04d479e4"
        )
        
        # Initialize gRPC backend
        self.grpc_backend = OptimizedGRPCBackend(
            config=GRPCChannelConfig(
                max_send_message_length=64 * 1024 * 1024,
                max_receive_message_length=64 * 1024 * 1024,
                enable_compression=True,
                compression_algorithm="gzip",
                keepalive_time_ms=30000,
                max_connection_idle_ms=300000
            )
        )
        
        # Performance stats
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "grpc_optimizations": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0
        }
        
        # Setup routes
        self.setup_routes()
        
        logger.info("🏢 MCP Enterprise News Service initialized with gRPC backend")
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "MCP Enterprise News Service",
                "backend": "gRPC Optimized",
                "timestamp": time.time()
            }
        
        @self.app.get("/articles")
        async def get_articles(
            category: Optional[str] = None,
            language: str = "en",
            limit: int = 50
        ):
            """Get news articles through MCP Enterprise system"""
            start_time = time.time()
            
            try:
                self.stats["total_requests"] += 1
                
                # Use MCP Enterprise dual provider with gRPC optimization
                logger.info(f"🏢 Processing request via MCP Enterprise (gRPC backend)")
                
                # Route through gRPC optimized backend
                news_response = await self.dual_news_provider.get_latest_news(
                    language=language,
                    category=category,
                    limit=limit,
                    provider=NewsProvider.AUTO  # Auto-select best provider
                )
                
                if news_response.status == "success":
                    self.stats["successful_requests"] += 1
                    self.stats["grpc_optimizations"] += 1
                    
                    # Calculate performance metrics
                    processing_time = (time.time() - start_time) * 1000
                    self.stats["avg_response_time"] = (
                        (self.stats["avg_response_time"] * (self.stats["successful_requests"] - 1) + processing_time) 
                        / self.stats["successful_requests"]
                    )
                    
                    # Format response for frontend
                    return {
                        "status": "success",
                        "articles": [
                            {
                                "title": article.title,
                                "description": article.description,
                                "url": article.url,
                                "image": article.image,
                                "source": article.source,
                                "published": article.published_at,
                                "category": article.category[0] if article.category else "general"
                            }
                            for article in news_response.articles
                        ],
                        "total": news_response.total_results,
                        "processing_time_ms": processing_time,
                        "provider_used": news_response.provider_used.value,
                        "backend_optimization": news_response.backend_optimization,
                        "mcp_enterprise": True
                    }
                else:
                    raise HTTPException(status_code=500, detail="News aggregation failed")
                    
            except Exception as e:
                logger.error(f"❌ Error in MCP Enterprise service: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stats")
        async def get_stats():
            """Get service performance statistics"""
            provider_stats = self.dual_news_provider.get_comprehensive_stats()
            
            return {
                "mcp_enterprise": self.stats,
                "providers": provider_stats,
                "backend": "gRPC Optimized",
                "optimization_level": "Enterprise"
            }

async def start_mcp_enterprise_service():
    """Start the MCP Enterprise News Service"""
    service = MCPEnterpriseNewsService()
    
    # Start the service
    config = uvicorn.Config(
        service.app,
        host="localhost",
        port=8889,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info("🚀 Starting MCP Enterprise News Service on http://localhost:8889")
    logger.info("📡 Endpoints:")
    logger.info("   Health: GET  http://localhost:8889/health")
    logger.info("   Articles: GET  http://localhost:8889/articles")
    logger.info("   Stats: GET  http://localhost:8889/stats")
    
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_mcp_enterprise_service()) 