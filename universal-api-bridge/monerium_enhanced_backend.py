#!/usr/bin/env python3
"""
Enhanced Monerium Backend Gateway
Comprehensive implementation of all Monerium API v2 endpoints
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import deque
from fastapi import FastAPI, HTTPException, Request, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MoneriumEnhancedGateway:
    """Enhanced Monerium MCP Gateway with complete API v2 support"""
    
    def __init__(self):
        # Monerium API Configuration
        self.client_id = "54be063f-6cca-11f0-a3e6-4eb54501c717"
        self.client_secret = "71ab65b523e1651fa197ea39ecf2156ed30da3199c668053029860133e0cfdd5"
        self.auth_code_client = "54bc5fda-6cca-11f0-a3e6-4eb54501c717"
        
        # API Base URLs
        self.api_base_urls = {
            "production": "https://api.monerium.app",
            "sandbox": "https://api.monerium.dev"
        }
        self.current_environment = "sandbox"  # Default to sandbox
        self.current_token = None
        
        # Service Registry for all Monerium endpoints
        self.service_registry = {
            # Authentication services
            "auth-welcome": {
                "name": "Welcome Service",
                "endpoint": "/",
                "method": "GET",
                "description": "Welcome message and API information"
            },
            "auth-token": {
                "name": "Token Service", 
                "endpoint": "/auth/token",
                "method": "POST",
                "description": "OAuth2 access token management"
            },
            "auth-context": {
                "name": "Auth Context Service",
                "endpoint": "/auth/context", 
                "method": "GET",
                "description": "User authentication context"
            },
            "auth-signup": {
                "name": "Signup Service",
                "endpoint": "/auth/signup",
                "method": "POST", 
                "description": "User registration"
            },
            
            # Profile services
            "profiles-list": {
                "name": "Profiles List Service",
                "endpoint": "/profiles",
                "method": "GET",
                "description": "List all accessible profiles"
            },
            "profile-details": {
                "name": "Profile Details Service", 
                "endpoint": "/profiles/{profile}",
                "method": "GET",
                "description": "Get single profile details"
            },
            "profile-submit-details": {
                "name": "Profile Submit Details Service",
                "endpoint": "/profiles/{profile}/details",
                "method": "PUT",
                "description": "Submit KYC profile details"
            },
            "profile-submit-form": {
                "name": "Profile Submit Form Service",
                "endpoint": "/profiles/{profile}/form", 
                "method": "PUT",
                "description": "Submit profile form data"
            },
            "profile-submit-verifications": {
                "name": "Profile Submit Verifications Service",
                "endpoint": "/profiles/{profile}/verifications",
                "method": "PUT", 
                "description": "Submit profile verifications"
            },
            
            # Address services
            "addresses-list": {
                "name": "Addresses List Service",
                "endpoint": "/addresses",
                "method": "GET",
                "description": "List linked blockchain addresses"
            },
            "address-link": {
                "name": "Address Link Service", 
                "endpoint": "/addresses",
                "method": "POST",
                "description": "Link new blockchain address"
            },
            "address-details": {
                "name": "Address Details Service",
                "endpoint": "/addresses/{address}",
                "method": "GET", 
                "description": "Get address details"
            },
            
            # Balance services  
            "balances": {
                "name": "Balance Service",
                "endpoint": "/balances/{chain}/{address}",
                "method": "GET",
                "description": "Get token balances for address on chain"
            },
            
            # IBAN services
            "ibans-list": {
                "name": "IBANs List Service", 
                "endpoint": "/ibans",
                "method": "GET",
                "description": "List all IBANs"
            },
            "iban-request": {
                "name": "IBAN Request Service",
                "endpoint": "/ibans", 
                "method": "POST",
                "description": "Request new IBAN"
            },
            "iban-details": {
                "name": "IBAN Details Service",
                "endpoint": "/ibans/{iban}",
                "method": "GET",
                "description": "Get IBAN details" 
            },
            "iban-move": {
                "name": "IBAN Move Service",
                "endpoint": "/ibans/{iban}",
                "method": "PATCH",
                "description": "Move IBAN to different address/chain"
            },
            
            # Order services
            "orders-list": {
                "name": "Orders List Service",
                "endpoint": "/orders", 
                "method": "GET",
                "description": "List all orders"
            },
            "order-place": {
                "name": "Order Place Service",
                "endpoint": "/orders",
                "method": "POST",
                "description": "Place new order"
            },
            "order-details": {
                "name": "Order Details Service", 
                "endpoint": "/orders/{orderId}",
                "method": "GET",
                "description": "Get order details"
            },
            
            # File services
            "file-upload": {
                "name": "File Upload Service",
                "endpoint": "/files",
                "method": "POST", 
                "description": "Upload documents"
            },
            
            # Token services
            "tokens": {
                "name": "Tokens Service",
                "endpoint": "/tokens",
                "method": "GET",
                "description": "Get supported tokens information"
            },
            
            # Webhook services
            "webhooks-list": {
                "name": "Webhooks List Service",
                "endpoint": "/webhooks",
                "method": "GET", 
                "description": "List webhook subscriptions"
            },
            "webhook-create": {
                "name": "Webhook Create Service",
                "endpoint": "/webhooks",
                "method": "POST",
                "description": "Create webhook subscription"
            },
            "webhook-update": {
                "name": "Webhook Update Service",
                "endpoint": "/webhooks/{subscription}",
                "method": "PATCH",
                "description": "Update webhook subscription" 
            }
        }
        
        # Circuit breaker for resilience
        self.circuit_breaker = {
            "failures": 0,
            "threshold": 5,
            "timeout": 60000,
            "state": "closed"
        }
        
        logger.info("🚀 Enhanced Monerium MCP Gateway initialized")
        logger.info(f"🏦 API Environment: {self.current_environment}")
        logger.info(f"🔑 Client ID: {self.client_id[:10]}...")

    def get_api_base_url(self, environment: str = None) -> str:
        """Get API base URL for specified environment"""
        env = environment or self.current_environment
        return self.api_base_urls.get(env, self.api_base_urls["sandbox"])

    async def make_request(self, method: str, endpoint: str, headers: Dict = None, 
                          data: Any = None, environment: str = None) -> Dict[str, Any]:
        """Make HTTP request to Monerium API with proper error handling"""
        base_url = self.get_api_base_url(environment)
        url = f"{base_url}{endpoint}"
        
        # Default headers
        default_headers = {
            "Accept": "application/vnd.monerium.api-v2+json",
            "Content-Type": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        # Configure HTTP client with SSL bypass for corporate environments
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            try:
                logger.info(f"🔧 MCP Route: {endpoint} → {method} {url}")
                
                if method.upper() == "GET":
                    response = await client.get(url, headers=default_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=default_headers, json=data)
                elif method.upper() == "PUT": 
                    response = await client.put(url, headers=default_headers, json=data)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=default_headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=default_headers)
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported HTTP method: {method}")
                
                # Handle different response types
                if response.headers.get("content-type", "").startswith("application/json"):
                    result = response.json()
                else:
                    result = {"content": response.text, "status_code": response.status_code}
                
                # Log successful requests
                if response.status_code < 400:
                    logger.info(f"✅ Request successful - Status: {response.status_code}")
                else:
                    logger.warning(f"⚠️ Request failed - Status: {response.status_code}")
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": result,
                    "success": response.status_code < 400
                }
                
            except httpx.TimeoutException:
                logger.error(f"⏰ Request timeout: {url}")
                raise HTTPException(status_code=504, detail="Request timeout")
            except httpx.RequestError as e:
                logger.error(f"❌ Request error: {e}")
                raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    async def authenticate_client_credentials(self) -> Dict[str, Any]:
        """Authenticate using client credentials"""
        data = {
            "grant_type": "client_credentials", 
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # Convert data to form-encoded format
        form_data = "&".join([f"{k}={v}" for k, v in data.items()])
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.get_api_base_url()}/auth/token",
                headers=headers,
                content=form_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.current_token = token_data.get("access_token")
                logger.info(f"✅ Authentication successful - Token: {self.current_token[:20]}...")
                return token_data
            else:
                logger.error(f"❌ Authentication failed: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="Authentication failed")

# Pydantic models
class APIRequest(BaseModel):
    method: str
    endpoint: str
    headers: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None
    environment: Optional[str] = None

class LiveMonitorEvent(BaseModel):
    timestamp: str
    event_type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    user_action: Optional[str] = None
    status: Optional[str] = None

# Initialize the gateway
gateway = MoneriumEnhancedGateway()

# FastAPI app setup
app = FastAPI(title="Enhanced Monerium MCP Gateway", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint - no authentication required"""
    return {
        "status": "healthy",
        "service": "Enhanced Monerium MCP Gateway",
        "timestamp": datetime.now().isoformat(),
        "environment": gateway.current_environment,
        "api_base_url": gateway.get_api_base_url(),
        "services": gateway.service_registry,
        "circuit_breaker": gateway.circuit_breaker,
        "auth_status": "authenticated" if gateway.current_token else "not_authenticated"
    }

# Services endpoint  
@app.get("/services")
async def list_services():
    """List all available Monerium services"""
    return {
        "services": gateway.service_registry,
        "total_count": len(gateway.service_registry),
        "environment": gateway.current_environment,
        "api_base_url": gateway.get_api_base_url()
    }

# Generic API proxy endpoint
@app.post("/api/proxy") 
async def proxy_request(request: APIRequest):
    """Proxy requests to Monerium API"""
    try:
        # Handle authentication if token provided in headers
        headers = request.headers or {}
        if gateway.current_token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {gateway.current_token}"
        
        result = await gateway.make_request(
            method=request.method,
            endpoint=request.endpoint, 
            headers=headers,
            data=request.data,
            environment=request.environment
        )
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Proxy request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Authentication endpoints
@app.post("/auth/token")
async def get_access_token(grant_type: str = Form(), client_id: str = Form(None), 
                          client_secret: str = Form(None)):
    """Get access token using client credentials"""
    try:
        if grant_type == "client_credentials":
            result = await gateway.authenticate_client_credentials()
            return result
        else:
            raise HTTPException(status_code=400, detail="Only client_credentials grant type supported")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Token request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/context")
async def get_auth_context():
    """Get authentication context"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    result = await gateway.make_request("GET", "/auth/context", headers=headers)
    return result

# Profile endpoints
@app.get("/profiles")
async def list_profiles(state: str = None, kind: str = None):
    """List profiles"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    endpoint = "/profiles"
    
    # Add query parameters
    params = []
    if state:
        params.append(f"state={state}")
    if kind:
        params.append(f"kind={kind}")
    if params:
        endpoint += "?" + "&".join(params)
    
    result = await gateway.make_request("GET", endpoint, headers=headers)
    return result

@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get profile details"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    result = await gateway.make_request("GET", f"/profiles/{profile_id}", headers=headers)
    return result

# Address endpoints
@app.get("/addresses") 
async def list_addresses(profile: str = None, chain: str = None):
    """List addresses"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    endpoint = "/addresses"
    
    # Add query parameters
    params = []
    if profile:
        params.append(f"profile={profile}")
    if chain:
        params.append(f"chain={chain}")
    if params:
        endpoint += "?" + "&".join(params)
    
    result = await gateway.make_request("GET", endpoint, headers=headers)
    return result

@app.get("/addresses/{address}")
async def get_address(address: str):
    """Get address details"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    result = await gateway.make_request("GET", f"/addresses/{address}", headers=headers)
    return result

# Balance endpoints
@app.get("/balances/{chain}/{address}")
async def get_balances(chain: str, address: str, currency: str = None):
    """Get token balances"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    endpoint = f"/balances/{chain}/{address}"
    
    if currency:
        endpoint += f"?currency={currency}"
    
    result = await gateway.make_request("GET", endpoint, headers=headers)
    return result

# IBAN endpoints  
@app.get("/ibans")
async def list_ibans(profile: str = None, chain: str = None):
    """List IBANs"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    endpoint = "/ibans"
    
    # Add query parameters
    params = []
    if profile:
        params.append(f"profile={profile}")
    if chain:
        params.append(f"chain={chain}")
    if params:
        endpoint += "?" + "&".join(params)
    
    result = await gateway.make_request("GET", endpoint, headers=headers)
    return result

@app.get("/ibans/{iban}")
async def get_iban(iban: str):
    """Get IBAN details"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    result = await gateway.make_request("GET", f"/ibans/{iban}", headers=headers)
    return result

# Order endpoints
@app.get("/orders")
async def list_orders(address: str = None, profile: str = None, state: str = None, 
                     memo: str = None, txHash: str = None):
    """List orders"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    endpoint = "/orders"
    
    # Add query parameters
    params = []
    if address:
        params.append(f"address={address}")
    if profile:
        params.append(f"profile={profile}")
    if state:
        params.append(f"state={state}")
    if memo:
        params.append(f"memo={memo}")
    if txHash:
        params.append(f"txHash={txHash}")
    if params:
        endpoint += "?" + "&".join(params)
    
    result = await gateway.make_request("GET", endpoint, headers=headers)
    return result

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    result = await gateway.make_request("GET", f"/orders/{order_id}", headers=headers)
    return result

# Token endpoints
@app.get("/tokens")
async def list_tokens():
    """List supported tokens"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    result = await gateway.make_request("GET", "/tokens", headers=headers)
    return result

# Webhook endpoints
@app.get("/webhooks")
async def list_webhooks():
    """List webhook subscriptions"""
    if not gateway.current_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    headers = {"Authorization": f"Bearer {gateway.current_token}"}
    result = await gateway.make_request("GET", "/webhooks", headers=headers)
    return result

# Welcome endpoint
@app.get("/")
async def welcome():
    """Welcome message"""
    result = await gateway.make_request("GET", "/")
    return result

# Environment switching
@app.post("/environment/{env}")
async def switch_environment(env: str):
    """Switch API environment"""
    if env not in gateway.api_base_urls:
        raise HTTPException(status_code=400, detail=f"Invalid environment: {env}")
    
    gateway.current_environment = env
    gateway.current_token = None  # Clear token when switching environments
    
    logger.info(f"🔄 Environment switched to: {env}")
    
    return {
        "environment": env,
        "api_base_url": gateway.get_api_base_url(),
        "message": f"Environment switched to {env}"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Enhanced Monerium MCP Gateway...")
    print(f"🏦 Monerium API: {gateway.get_api_base_url()}")
    print(f"🔑 Client ID: {gateway.client_id[:10]}...")
    print("🌐 Gateway: http://localhost:8005")
    
    uvicorn.run(app, host="0.0.0.0", port=8005) 