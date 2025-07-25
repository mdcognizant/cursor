"""Universal API Bridge SDK for client applications."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class UniversalSDK:
    """SDK for interacting with the Universal API Bridge."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def call_service(
        self, 
        service: str, 
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a service through the universal bridge."""
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        url = f"{self.base_url}/api/{service}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                params=params if params else None,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"SDK call failed: {e}")
            return {"error": str(e)}
            
    async def health_check(self) -> Dict[str, Any]:
        """Check bridge health."""
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return await response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)} 