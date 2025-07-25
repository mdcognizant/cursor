"""Load balancer for distributing requests across service instances."""

import random
import time
import logging
from typing import List, Optional, Dict, Any
from enum import Enum

from .registry import ServiceInstance

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"


class LoadBalancer:
    """Distributes requests across service instances."""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self._round_robin_counters: Dict[str, int] = {}
        self._connection_counts: Dict[str, int] = {}
        
    async def select_instance(self, service_name: str, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select an instance based on the load balancing strategy."""
        if not instances:
            return None
            
        if len(instances) == 1:
            return instances[0]
            
        try:
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_select(service_name, instances)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(service_name, instances)
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                return self._random_select(instances)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_select(instances)
            else:
                return instances[0]  # Fallback
                
        except Exception as e:
            logger.error(f"Load balancing error for {service_name}: {e}")
            return instances[0]  # Fallback to first instance
            
    def _round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round-robin selection."""
        if service_name not in self._round_robin_counters:
            self._round_robin_counters[service_name] = 0
            
        instance = instances[self._round_robin_counters[service_name] % len(instances)]
        self._round_robin_counters[service_name] += 1
        return instance
        
    def _weighted_round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round-robin selection."""
        # Create weighted list
        weighted_instances = []
        for instance in instances:
            weight = max(1, instance.weight)  # Ensure minimum weight of 1
            weighted_instances.extend([instance] * weight)
            
        if not weighted_instances:
            return instances[0]
            
        if service_name not in self._round_robin_counters:
            self._round_robin_counters[service_name] = 0
            
        instance = weighted_instances[self._round_robin_counters[service_name] % len(weighted_instances)]
        self._round_robin_counters[service_name] += 1
        return instance
        
    def _random_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Random selection."""
        return random.choice(instances)
        
    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections selection."""
        min_connections = float('inf')
        selected_instance = instances[0]
        
        for instance in instances:
            connections = self._connection_counts.get(instance.address, 0)
            if connections < min_connections:
                min_connections = connections
                selected_instance = instance
                
        return selected_instance
        
    async def on_request_start(self, instance: ServiceInstance) -> None:
        """Called when a request starts to an instance."""
        address = instance.address
        self._connection_counts[address] = self._connection_counts.get(address, 0) + 1
        
    async def on_request_end(self, instance: ServiceInstance) -> None:
        """Called when a request ends to an instance."""
        address = instance.address
        if address in self._connection_counts:
            self._connection_counts[address] = max(0, self._connection_counts[address] - 1)
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        return {
            "strategy": self.strategy.value,
            "connection_counts": dict(self._connection_counts),
            "round_robin_counters": dict(self._round_robin_counters)
        } 