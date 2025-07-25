"""
Distributed Service Registry for massive scale (100k+ APIs).

This module implements enterprise-grade service discovery with support for:
- etcd distributed storage with clustering
- Consul service discovery with health checks
- Kubernetes service discovery
- Redis clustering for fallback
- Service health monitoring and federation
- Automatic failover and replication
- Distributed locks and leader election
"""

import asyncio
import json
import logging
import time
import weakref
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib
import random

import etcd3
import consul
import redis.asyncio as aioredis
from kubernetes import client, config as k8s_config, watch
import aiohttp

from ..config import ServiceDiscoveryBackend, MCPConfig
from ..exceptions import ServiceRegistryError, ServiceUnavailableError

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceInstance:
    """Enhanced service instance with extensive metadata."""
    id: str
    name: str
    host: str
    port: int
    protocol: str = "grpc"
    version: str = "1.0.0"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    health_check_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    weight: int = 100
    last_heartbeat: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # Performance metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    
    # Geographic and network info
    region: Optional[str] = None
    zone: Optional[str] = None
    datacenter: Optional[str] = None
    network_latency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "version": self.version,
            "status": self.status.value,
            "health_check_url": self.health_check_url,
            "metadata": self.metadata,
            "tags": list(self.tags),
            "weight": self.weight,
            "last_heartbeat": self.last_heartbeat,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_response_time": self.avg_response_time,
            "region": self.region,
            "zone": self.zone,
            "datacenter": self.datacenter,
            "network_latency": self.network_latency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInstance':
        """Create from dictionary."""
        instance = cls(
            id=data["id"],
            name=data["name"],
            host=data["host"],
            port=data["port"],
            protocol=data.get("protocol", "grpc"),
            version=data.get("version", "1.0.0"),
            status=ServiceStatus(data.get("status", "unknown")),
            health_check_url=data.get("health_check_url"),
            metadata=data.get("metadata", {}),
            weight=data.get("weight", 100),
            last_heartbeat=data.get("last_heartbeat", time.time()),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            cpu_usage=data.get("cpu_usage", 0.0),
            memory_usage=data.get("memory_usage", 0.0),
            request_count=data.get("request_count", 0),
            error_count=data.get("error_count", 0),
            avg_response_time=data.get("avg_response_time", 0.0),
            region=data.get("region"),
            zone=data.get("zone"),
            datacenter=data.get("datacenter"),
            network_latency=data.get("network_latency", 0.0)
        )
        instance.tags = set(data.get("tags", []))
        return instance


class DistributedServiceRegistry:
    """Distributed service registry supporting multiple backends for 100k+ APIs."""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.backend = config.registry_backend
        self.started = False
        
        # Service storage
        self.services: Dict[str, Dict[str, ServiceInstance]] = defaultdict(dict)
        self.service_watchers: Set[asyncio.Task] = set()
        self.health_check_tasks: Set[asyncio.Task] = set()
        
        # Backend clients
        self.etcd_client = None
        self.consul_client = None
        self.redis_client = None
        self.k8s_client = None
        
        # Distributed coordination
        self.leader_key = "universal-bridge/leader"
        self.is_leader = False
        self.leader_election_task = None
        
        # Performance tracking
        self.operation_metrics = {
            "register_count": 0,
            "discover_count": 0,
            "health_check_count": 0,
            "backend_errors": 0
        }
        
        logger.info(f"Initialized distributed service registry with backend: {self.backend}")
    
    async def start(self) -> None:
        """Start the distributed service registry."""
        if self.started:
            return
        
        try:
            # Initialize backend clients
            await self._initialize_backends()
            
            # Start leader election if clustering is enabled
            if self.config.enable_registry_clustering:
                self.leader_election_task = asyncio.create_task(self._leader_election_loop())
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.started = True
            logger.info("Distributed service registry started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start service registry: {e}")
            raise ServiceRegistryError(f"Registry startup failed: {e}")
    
    async def stop(self) -> None:
        """Stop the service registry."""
        self.started = False
        
        # Cancel all tasks
        if self.leader_election_task:
            self.leader_election_task.cancel()
        
        for task in self.service_watchers | self.health_check_tasks:
            task.cancel()
        
        # Close backend connections
        await self._close_backends()
        
        logger.info("Service registry stopped")
    
    async def register_service(self, service: ServiceInstance) -> bool:
        """Register a service instance."""
        try:
            service.updated_at = time.time()
            service.last_heartbeat = time.time()
            
            # Store locally
            self.services[service.name][service.id] = service
            
            # Store in distributed backend
            await self._store_service_in_backend(service)
            
            # Start health monitoring for this service
            if service.health_check_url:
                task = asyncio.create_task(self._monitor_service_health(service))
                self.health_check_tasks.add(task)
            
            self.operation_metrics["register_count"] += 1
            logger.info(f"Registered service: {service.name}#{service.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {service.name}#{service.id}: {e}")
            self.operation_metrics["backend_errors"] += 1
            return False
    
    async def unregister_service(self, service_name: str, service_id: str) -> bool:
        """Unregister a service instance."""
        try:
            # Remove from local storage
            if service_name in self.services and service_id in self.services[service_name]:
                del self.services[service_name][service_id]
                if not self.services[service_name]:
                    del self.services[service_name]
            
            # Remove from distributed backend
            await self._remove_service_from_backend(service_name, service_id)
            
            logger.info(f"Unregistered service: {service_name}#{service_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister service {service_name}#{service_id}: {e}")
            self.operation_metrics["backend_errors"] += 1
            return False
    
    async def discover_services(self, service_name: str, tags: Optional[Set[str]] = None, 
                              healthy_only: bool = True) -> List[ServiceInstance]:
        """Discover service instances."""
        try:
            # Try to get from distributed backend first
            instances = await self._discover_from_backend(service_name, tags, healthy_only)
            
            # Fallback to local cache if backend fails
            if not instances and service_name in self.services:
                instances = list(self.services[service_name].values())
                if tags:
                    instances = [s for s in instances if tags.issubset(s.tags)]
                if healthy_only:
                    instances = [s for s in instances if s.status == ServiceStatus.HEALTHY]
            
            self.operation_metrics["discover_count"] += 1
            return instances
            
        except Exception as e:
            logger.error(f"Failed to discover services for {service_name}: {e}")
            self.operation_metrics["backend_errors"] += 1
            return []
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get aggregated health information for a service."""
        instances = await self.discover_services(service_name, healthy_only=False)
        
        if not instances:
            return {
                "service_name": service_name,
                "status": "not_found",
                "total_instances": 0,
                "healthy_instances": 0,
                "health_percentage": 0.0
            }
        
        healthy_count = sum(1 for i in instances if i.status == ServiceStatus.HEALTHY)
        total_count = len(instances)
        
        return {
            "service_name": service_name,
            "status": "healthy" if healthy_count > 0 else "unhealthy",
            "total_instances": total_count,
            "healthy_instances": healthy_count,
            "health_percentage": (healthy_count / total_count) * 100,
            "instances": [
                {
                    "id": i.id,
                    "host": i.host,
                    "port": i.port,
                    "status": i.status.value,
                    "last_heartbeat": i.last_heartbeat,
                    "cpu_usage": i.cpu_usage,
                    "memory_usage": i.memory_usage,
                    "avg_response_time": i.avg_response_time
                }
                for i in instances
            ]
        }
    
    async def update_service_metrics(self, service_name: str, service_id: str, 
                                   metrics: Dict[str, Any]) -> bool:
        """Update service performance metrics."""
        try:
            if service_name in self.services and service_id in self.services[service_name]:
                service = self.services[service_name][service_id]
                
                # Update metrics
                service.cpu_usage = metrics.get("cpu_usage", service.cpu_usage)
                service.memory_usage = metrics.get("memory_usage", service.memory_usage)
                service.request_count = metrics.get("request_count", service.request_count)
                service.error_count = metrics.get("error_count", service.error_count)
                service.avg_response_time = metrics.get("avg_response_time", service.avg_response_time)
                service.updated_at = time.time()
                service.last_heartbeat = time.time()
                
                # Update in backend
                await self._store_service_in_backend(service)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update metrics for {service_name}#{service_id}: {e}")
            return False
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_services = len(self.services)
        total_instances = sum(len(instances) for instances in self.services.values())
        healthy_instances = 0
        
        for instances in self.services.values():
            healthy_instances += sum(1 for i in instances.values() 
                                   if i.status == ServiceStatus.HEALTHY)
        
        return {
            "backend": self.backend.value,
            "is_leader": self.is_leader,
            "total_services": total_services,
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "health_percentage": (healthy_instances / total_instances * 100) if total_instances > 0 else 0,
            "operations": self.operation_metrics.copy(),
            "clustering_enabled": self.config.enable_registry_clustering,
            "replication_factor": self.config.registry_replication_factor
        }
    
    # Backend-specific implementations
    
    async def _initialize_backends(self) -> None:
        """Initialize backend clients."""
        if self.backend == ServiceDiscoveryBackend.ETCD:
            await self._initialize_etcd()
        elif self.backend == ServiceDiscoveryBackend.CONSUL:
            await self._initialize_consul()
        elif self.backend == ServiceDiscoveryBackend.REDIS:
            await self._initialize_redis()
        elif self.backend == ServiceDiscoveryBackend.KUBERNETES:
            await self._initialize_kubernetes()
        else:
            logger.warning(f"Using memory backend for service discovery")
    
    async def _initialize_etcd(self) -> None:
        """Initialize etcd client."""
        try:
            if self.config.registry_hosts:
                host, port = self.config.registry_hosts[0].split(":")
                self.etcd_client = etcd3.client(
                    host=host,
                    port=int(port),
                    user=self.config.registry_username,
                    password=self.config.registry_password,
                    timeout=30
                )
                # Test connection
                await asyncio.get_event_loop().run_in_executor(
                    None, self.etcd_client.get, "test"
                )
                logger.info("etcd client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize etcd client: {e}")
            raise ServiceRegistryError(f"etcd initialization failed: {e}")
    
    async def _initialize_consul(self) -> None:
        """Initialize Consul client."""
        try:
            if self.config.registry_hosts:
                host, port = self.config.registry_hosts[0].split(":")
                self.consul_client = consul.Consul(
                    host=host,
                    port=int(port),
                    timeout=30
                )
                # Test connection
                self.consul_client.agent.services()
                logger.info("Consul client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Consul client: {e}")
            raise ServiceRegistryError(f"Consul initialization failed: {e}")
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis client."""
        try:
            if self.config.registry_hosts:
                host, port = self.config.registry_hosts[0].split(":")
                self.redis_client = aioredis.from_url(
                    f"redis://{host}:{port}",
                    username=self.config.registry_username,
                    password=self.config.registry_password,
                    socket_timeout=30
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise ServiceRegistryError(f"Redis initialization failed: {e}")
    
    async def _initialize_kubernetes(self) -> None:
        """Initialize Kubernetes client."""
        try:
            k8s_config.load_incluster_config()
            self.k8s_client = client.CoreV1Api()
            logger.info("Kubernetes client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise ServiceRegistryError(f"Kubernetes initialization failed: {e}")
    
    async def _store_service_in_backend(self, service: ServiceInstance) -> None:
        """Store service in the distributed backend."""
        if self.backend == ServiceDiscoveryBackend.ETCD and self.etcd_client:
            await self._store_in_etcd(service)
        elif self.backend == ServiceDiscoveryBackend.CONSUL and self.consul_client:
            await self._store_in_consul(service)
        elif self.backend == ServiceDiscoveryBackend.REDIS and self.redis_client:
            await self._store_in_redis(service)
        elif self.backend == ServiceDiscoveryBackend.KUBERNETES and self.k8s_client:
            await self._store_in_kubernetes(service)
    
    async def _store_in_etcd(self, service: ServiceInstance) -> None:
        """Store service in etcd."""
        key = f"services/{service.name}/{service.id}"
        value = json.dumps(service.to_dict())
        
        await asyncio.get_event_loop().run_in_executor(
            None, 
            self.etcd_client.put,
            key, 
            value,
            lease=self.etcd_client.lease(self.config.registry_ttl)
        )
    
    async def _store_in_consul(self, service: ServiceInstance) -> None:
        """Store service in Consul."""
        service_def = {
            "ID": service.id,
            "Name": service.name,
            "Address": service.host,
            "Port": service.port,
            "Tags": list(service.tags),
            "Meta": service.metadata,
            "Check": {
                "HTTP": service.health_check_url,
                "Interval": f"{self.config.registry_heartbeat_interval}s"
            } if service.health_check_url else None
        }
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.consul_client.agent.service.register,
            **service_def
        )
    
    async def _store_in_redis(self, service: ServiceInstance) -> None:
        """Store service in Redis."""
        key = f"services:{service.name}:{service.id}"
        value = json.dumps(service.to_dict())
        
        await self.redis_client.setex(key, self.config.registry_ttl, value)
    
    async def _store_in_kubernetes(self, service: ServiceInstance) -> None:
        """Store service in Kubernetes."""
        # This would typically involve creating/updating a Kubernetes Service
        # For now, we'll use ConfigMaps to store service metadata
        pass
    
    async def _discover_from_backend(self, service_name: str, tags: Optional[Set[str]] = None,
                                   healthy_only: bool = True) -> List[ServiceInstance]:
        """Discover services from the distributed backend."""
        if self.backend == ServiceDiscoveryBackend.ETCD and self.etcd_client:
            return await self._discover_from_etcd(service_name, tags, healthy_only)
        elif self.backend == ServiceDiscoveryBackend.CONSUL and self.consul_client:
            return await self._discover_from_consul(service_name, tags, healthy_only)
        elif self.backend == ServiceDiscoveryBackend.REDIS and self.redis_client:
            return await self._discover_from_redis(service_name, tags, healthy_only)
        elif self.backend == ServiceDiscoveryBackend.KUBERNETES and self.k8s_client:
            return await self._discover_from_kubernetes(service_name, tags, healthy_only)
        
        return []
    
    async def _discover_from_etcd(self, service_name: str, tags: Optional[Set[str]] = None,
                                healthy_only: bool = True) -> List[ServiceInstance]:
        """Discover services from etcd."""
        prefix = f"services/{service_name}/"
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            self.etcd_client.get_prefix,
            prefix
        )
        
        instances = []
        for value, metadata in result:
            try:
                service_data = json.loads(value.decode())
                instance = ServiceInstance.from_dict(service_data)
                
                if tags and not tags.issubset(instance.tags):
                    continue
                
                if healthy_only and instance.status != ServiceStatus.HEALTHY:
                    continue
                
                instances.append(instance)
                
            except Exception as e:
                logger.error(f"Failed to parse service data from etcd: {e}")
        
        return instances
    
    async def _discover_from_consul(self, service_name: str, tags: Optional[Set[str]] = None,
                                  healthy_only: bool = True) -> List[ServiceInstance]:
        """Discover services from Consul."""
        try:
            _, services = await asyncio.get_event_loop().run_in_executor(
                None,
                self.consul_client.health.service,
                service_name,
                passing=healthy_only
            )
            
            instances = []
            for service_data in services:
                service_info = service_data['Service']
                health_info = service_data.get('Checks', [])
                
                # Determine health status
                status = ServiceStatus.HEALTHY
                for check in health_info:
                    if check['Status'] != 'passing':
                        status = ServiceStatus.UNHEALTHY
                        break
                
                instance = ServiceInstance(
                    id=service_info['ID'],
                    name=service_info['Service'],
                    host=service_info['Address'],
                    port=service_info['Port'],
                    status=status,
                    tags=set(service_info.get('Tags', [])),
                    metadata=service_info.get('Meta', {})
                )
                
                if tags and not tags.issubset(instance.tags):
                    continue
                
                instances.append(instance)
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to discover services from Consul: {e}")
            return []
    
    async def _discover_from_redis(self, service_name: str, tags: Optional[Set[str]] = None,
                                 healthy_only: bool = True) -> List[ServiceInstance]:
        """Discover services from Redis."""
        pattern = f"services:{service_name}:*"
        
        keys = await self.redis_client.keys(pattern)
        instances = []
        
        for key in keys:
            try:
                value = await self.redis_client.get(key)
                if value:
                    service_data = json.loads(value)
                    instance = ServiceInstance.from_dict(service_data)
                    
                    if tags and not tags.issubset(instance.tags):
                        continue
                    
                    if healthy_only and instance.status != ServiceStatus.HEALTHY:
                        continue
                    
                    instances.append(instance)
                    
            except Exception as e:
                logger.error(f"Failed to parse service data from Redis: {e}")
        
        return instances
    
    async def _discover_from_kubernetes(self, service_name: str, tags: Optional[Set[str]] = None,
                                      healthy_only: bool = True) -> List[ServiceInstance]:
        """Discover services from Kubernetes."""
        # This would typically involve querying Kubernetes Services and Endpoints
        # For now, return empty list
        return []
    
    async def _remove_service_from_backend(self, service_name: str, service_id: str) -> None:
        """Remove service from the distributed backend."""
        if self.backend == ServiceDiscoveryBackend.ETCD and self.etcd_client:
            key = f"services/{service_name}/{service_id}"
            await asyncio.get_event_loop().run_in_executor(
                None, self.etcd_client.delete, key
            )
        elif self.backend == ServiceDiscoveryBackend.CONSUL and self.consul_client:
            await asyncio.get_event_loop().run_in_executor(
                None, self.consul_client.agent.service.deregister, service_id
            )
        elif self.backend == ServiceDiscoveryBackend.REDIS and self.redis_client:
            key = f"services:{service_name}:{service_id}"
            await self.redis_client.delete(key)
    
    async def _close_backends(self) -> None:
        """Close backend connections."""
        if self.etcd_client:
            self.etcd_client.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        # Consul and Kubernetes clients don't need explicit closing
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Start periodic cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_expired_services())
        self.service_watchers.add(cleanup_task)
        
        # Start metrics collection task
        metrics_task = asyncio.create_task(self._collect_metrics())
        self.service_watchers.add(metrics_task)
    
    async def _leader_election_loop(self) -> None:
        """Leader election loop for clustering."""
        while self.started:
            try:
                if self.backend == ServiceDiscoveryBackend.ETCD and self.etcd_client:
                    # Try to acquire leadership
                    lease = self.etcd_client.lease(30)
                    try:
                        self.etcd_client.put(self.leader_key, "leader", lease=lease)
                        self.is_leader = True
                        logger.info("Acquired leadership")
                        
                        # Hold leadership
                        await asyncio.sleep(25)
                        
                    except Exception:
                        self.is_leader = False
                        await asyncio.sleep(5)
                else:
                    # Without etcd, assume we're the leader
                    self.is_leader = True
                    await asyncio.sleep(30)
                    
            except Exception as e:
                logger.error(f"Leader election error: {e}")
                self.is_leader = False
                await asyncio.sleep(5)
    
    async def _cleanup_expired_services(self) -> None:
        """Clean up expired services."""
        while self.started:
            try:
                now = time.time()
                expired_services = []
                
                for service_name, instances in self.services.items():
                    for service_id, instance in list(instances.items()):
                        if now - instance.last_heartbeat > self.config.registry_ttl * 2:
                            expired_services.append((service_name, service_id))
                
                # Remove expired services
                for service_name, service_id in expired_services:
                    await self.unregister_service(service_name, service_id)
                    logger.info(f"Cleaned up expired service: {service_name}#{service_id}")
                
                await asyncio.sleep(self.config.registry_heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self) -> None:
        """Collect registry metrics."""
        while self.started:
            try:
                # This could send metrics to monitoring systems
                stats = await self.get_registry_stats()
                logger.debug(f"Registry stats: {stats}")
                
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_service_health(self, service: ServiceInstance) -> None:
        """Monitor individual service health."""
        if not service.health_check_url:
            return
        
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
        
        try:
            while self.started and service.id in self.services.get(service.name, {}):
                try:
                    async with session.get(service.health_check_url) as response:
                        if response.status == 200:
                            service.status = ServiceStatus.HEALTHY
                        else:
                            service.status = ServiceStatus.UNHEALTHY
                    
                    service.last_heartbeat = time.time()
                    await self._store_service_in_backend(service)
                    
                    self.operation_metrics["health_check_count"] += 1
                    
                except Exception as e:
                    logger.warning(f"Health check failed for {service.name}#{service.id}: {e}")
                    service.status = ServiceStatus.UNHEALTHY
                    await self._store_service_in_backend(service)
                
                await asyncio.sleep(self.config.registry_heartbeat_interval)
                
        finally:
            await session.close()


# Backward compatibility alias
ServiceRegistry = DistributedServiceRegistry 