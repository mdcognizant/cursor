"""Connection pool for managing gRPC connections efficiently."""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import weakref
from contextlib import asynccontextmanager

from ..exceptions import ConnectionPoolExhaustedError

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """Connection configuration."""
    max_connections: int = 100
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0  # 5 minutes
    max_lifetime: float = 3600.0  # 1 hour
    keep_alive_time: float = 30.0
    keep_alive_timeout: float = 5.0


class MockGrpcConnection:
    """Mock gRPC connection for testing purposes."""
    
    def __init__(self, address: str):
        self.address = address
        self.created_at = time.time()
        self.last_used = time.time()
        self.is_active = True
        self.request_count = 0
        
    async def call_unary(self, method: str, request: Any) -> Any:
        """Mock unary call."""
        self.last_used = time.time()
        self.request_count += 1
        
        # Simulate some processing time
        await asyncio.sleep(0.001)
        
        # Mock response based on method
        if "user" in method.lower():
            return {"id": 123, "name": "Test User", "email": "test@example.com"}
        elif "order" in method.lower():
            return {"id": 456, "total": 99.99, "status": "completed"}
        else:
            return {"status": "success", "data": "mock_response"}
            
    async def call_streaming(self, method: str, request: Any):
        """Mock streaming call."""
        self.last_used = time.time()
        self.request_count += 1
        
        # Simulate streaming response
        for i in range(3):
            yield {"chunk": i, "data": f"stream_data_{i}"}
            await asyncio.sleep(0.001)
            
    async def close(self) -> None:
        """Close the connection."""
        self.is_active = False
        
    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        return (
            self.is_active and
            time.time() - self.last_used < 300 and  # Not idle for too long
            time.time() - self.created_at < 3600    # Not too old
        )


class ConnectionPool:
    """Manages connections to gRPC services."""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.pools: Dict[str, List[MockGrpcConnection]] = {}
        self.active_connections: Dict[str, Set[MockGrpcConnection]] = {}
        self.connection_counts: Dict[str, int] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self) -> None:
        """Start the connection pool."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Connection pool started")
        
    async def stop(self) -> None:
        """Stop the connection pool."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        # Close all connections
        for service_pools in self.pools.values():
            for conn in service_pools:
                await conn.close()
                
        self.pools.clear()
        self.active_connections.clear()
        self.connection_counts.clear()
        logger.info("Connection pool stopped")
        
    @asynccontextmanager
    async def get_connection(self, service_address: str):
        """Get a connection from the pool."""
        connection = await self._acquire_connection(service_address)
        try:
            yield connection
        finally:
            await self._release_connection(service_address, connection)
            
    async def _acquire_connection(self, service_address: str) -> MockGrpcConnection:
        """Acquire a connection from the pool."""
        # Initialize pools for new service
        if service_address not in self.pools:
            self.pools[service_address] = []
            self.active_connections[service_address] = set()
            self.connection_counts[service_address] = 0
            
        # Try to get idle connection
        available_connections = [
            conn for conn in self.pools[service_address]
            if conn.is_healthy()
        ]
        
        if available_connections:
            connection = available_connections[0]
            self.pools[service_address].remove(connection)
        else:
            # Check connection limit
            total_connections = (
                len(self.pools[service_address]) +
                len(self.active_connections[service_address])
            )
            
            if total_connections >= self.config.max_connections:
                raise ConnectionPoolExhaustedError(
                    f"Connection pool exhausted for {service_address}. "
                    f"Max connections: {self.config.max_connections}"
                )
                
            # Create new connection
            connection = MockGrpcConnection(service_address)
            self.connection_counts[service_address] += 1
            
        # Mark as active
        self.active_connections[service_address].add(connection)
        return connection
        
    async def _release_connection(self, service_address: str, connection: MockGrpcConnection) -> None:
        """Release a connection back to the pool."""
        if service_address in self.active_connections:
            self.active_connections[service_address].discard(connection)
            
        if connection.is_healthy():
            # Return to pool
            if service_address not in self.pools:
                self.pools[service_address] = []
            self.pools[service_address].append(connection)
        else:
            # Close unhealthy connection
            await connection.close()
            
    async def _cleanup_loop(self) -> None:
        """Background cleanup of old/unhealthy connections."""
        while self._running:
            try:
                await self._cleanup_connections()
                await asyncio.sleep(60)  # Cleanup every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection cleanup error: {e}")
                await asyncio.sleep(30)
                
    async def _cleanup_connections(self) -> None:
        """Clean up old and unhealthy connections."""
        for service_address, pool in self.pools.items():
            healthy_connections = []
            
            for conn in pool:
                if conn.is_healthy():
                    healthy_connections.append(conn)
                else:
                    await conn.close()
                    
            self.pools[service_address] = healthy_connections
            
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        stats = {}
        
        for service_address in self.pools:
            idle_count = len(self.pools[service_address])
            active_count = len(self.active_connections.get(service_address, set()))
            total_created = self.connection_counts.get(service_address, 0)
            
            stats[service_address] = {
                "idle_connections": idle_count,
                "active_connections": active_count,
                "total_connections": idle_count + active_count,
                "total_created": total_created,
                "max_connections": self.config.max_connections
            }
            
        return stats
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the connection pool."""
        total_connections = sum(
            len(pool) + len(active)
            for pool, active in zip(
                self.pools.values(),
                self.active_connections.values()
            )
        )
        
        return {
            "status": "healthy" if self._running else "stopped",
            "total_services": len(self.pools),
            "total_connections": total_connections,
            "max_connections_per_service": self.config.max_connections,
            "pools": await self.get_pool_stats()
        } 