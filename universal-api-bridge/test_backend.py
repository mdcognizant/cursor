#!/usr/bin/env python3
"""
Simple Test Backend for Monerium API Testing
This is a minimal version to test our concepts
"""

import httpx
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Pydantic models
class APIRequest(BaseModel):
    method: str
    endpoint: str
    headers: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None
    environment: Optional[str] = None

# FastAPI app
app = FastAPI(title="Test Monerium Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Test Monerium Backend is running", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Test Monerium Backend",
        "timestamp": datetime.now().isoformat(),
        "message": "Backend is working correctly"
    }

@app.options("/api/proxy")
async def proxy_options():
    """Handle OPTIONS preflight requests for CORS"""
    from fastapi import Response
    response = Response(content='{"message": "CORS preflight OK"}')
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.post("/api/proxy")
async def proxy_request(request: APIRequest):
    """Proxy requests to Monerium API"""
    try:
        # Determine base URL
        if request.environment == "production":
            base_url = "https://api.monerium.app"
        else:
            base_url = "https://api.monerium.dev"
        
        url = f"{base_url}{request.endpoint}"
        
        # Default headers
        headers = {
            "Accept": "application/vnd.monerium.api-v2+json",
            "Content-Type": "application/json"
        }
        
        # Add custom headers
        if request.headers:
            headers.update(request.headers)
        
        # Make request with SSL bypass for corporate environments
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            if request.method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif request.method.upper() == "POST":
                # Handle form data for OAuth endpoints
                if request.endpoint == "/auth/token" and request.data:
                    # OAuth2 endpoints expect form data
                    response = await client.post(url, headers=headers, data=request.data)
                else:
                    # Regular JSON data
                    response = await client.post(url, headers=headers, json=request.data)
            elif request.method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=request.data)
            elif request.method.upper() == "PATCH":
                response = await client.patch(url, headers=headers, json=request.data)
            elif request.method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")
            
            # Parse response
            try:
                if response.headers.get("content-type", "").startswith("application/json"):
                    response_data = response.json()
                else:
                    response_data = {"content": response.text, "content_type": response.headers.get("content-type")}
            except:
                response_data = {"content": response.text}
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response_data,
                "success": response.status_code < 400,
                "url": url,
                "method": request.method
            }
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/services")
async def list_services():
    """List available services"""
    return {
        "message": "Test backend with basic proxy functionality",
        "available_endpoints": [
            "/health - Health check",
            "/api/proxy - Proxy requests to Monerium API",
            "/services - This endpoint"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Test Monerium Backend...")
    print("🌐 Backend: http://localhost:8006")
    print("✅ Simple proxy functionality enabled")
    
    uvicorn.run(app, host="0.0.0.0", port=8006) 