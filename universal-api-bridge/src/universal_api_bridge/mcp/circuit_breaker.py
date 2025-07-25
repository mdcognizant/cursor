"""
Advanced Circuit Breaker implementation for massive scale (100k+ APIs).

This module implements enterprise-grade circuit breaker patterns including:
- Hystrix-style circuit breaker with distributed state
- Adaptive failure detection and recovery
- Bulkhead pattern for service isolation
- Timeout and retry patterns integration
- Health-based circuit management
- Performance metrics and monitoring
- Distributed coordination for cluster-wide circuit state
"""

import asyncio
import logging
import time
import math
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import statistics
import weakref
import json

import redis.asyncio as aioredis
from prometheus_client import Counter, Histogram, Gauge

from ..config import MCPConfig
from ..exceptions import CircuitBreakerError, ServiceUnavailableError, TimeoutError

logger = logging.getLogger(__name__)

# Metrics
circuit_breaker_state_changes = Counter(
    'circuit_breaker_state_changes_total',
    'Total circuit breaker state changes',
    ['service', 'from_state', 'to_state']
)

circuit_breaker_requests = Counter(
    'circuit_breaker_requests_total',
    'Total requests through circuit breaker',
    ['service', 'state', 'result']
)

circuit_breaker_failure_rate = Gauge(
    'circuit_breaker_failure_rate',
    'Current failure rate',
    ['service']
)

circuit_breaker_response_time = Histogram(
    'circuit_breaker_response_time_seconds',
    'Circuit breaker response time',
    ['service', 'state']
)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Circuit is open, failing fast
    HALF_OPEN = "half_open" # Testing if service recovered


class FailureType(Enum):
    """Types of failures that can trigger circuit breaker."""
    TIMEOUT = "timeout"
    ERROR = "error"
    SLOW_RESPONSE = "slow_response"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"


@dataclass
class CircuitBreakerConfig:
    """Enhanced circuit breaker configuration."""
    # Basic thresholds
    failure_threshold: int = 5
    recovery_threshold: int = 3
    timeout_seconds: float = 30.0
    
    # Advanced thresholds
    failure_rate_threshold: float = 0.5  # 50% failure rate
    minimum_requests: int = 10  # Minimum requests before checking failure rate
    slow_call_threshold: float = 5.0  # Seconds for slow call
    slow_call_rate_threshold: float = 0.8  # 80% slow calls
    
    # Time windows
    failure_window_seconds: int = 60  # Window for failure rate calculation
    half_open_max_calls: int = 10  # Max calls in half-open state
    open_state_duration: int = 60  # How long to stay open before trying half-open
    
    # Adaptive behavior
    enable_adaptive_threshold: bool = True
    max_failure_threshold: int = 20
    min_failure_threshold: int = 3
    threshold_adjustment_factor: float = 0.1
    
    # Distributed coordination
    enable_distributed_state: bool = True
    state_sync_interval: int = 5  # Seconds between state sync
    distributed_state_ttl: int = 30  # TTL for distributed state
    
    # Bulkhead configuration
    enable_bulkhead: bool = True
    max_concurrent_calls: int = 100
    queue_capacity: int = 200
    queue_timeout: float = 1.0


@dataclass
class CallResult:
    """Result of a service call."""
    success: bool
    duration: float
    failure_type: Optional[FailureType] = None
    timestamp: float = field(default_factory=time.time)
    response_size: int = 0
    error_message: Optional[str] = None


@dataclass
class CircuitMetrics:
    """Circuit breaker metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    slow_requests: int = 0
    
    current_failure_rate: float = 0.0
    current_slow_call_rate: float = 0.0
    average_response_time: float = 0.0
    
    state_changes: int = 0
    last_state_change: float = 0.0
    time_in_current_state: float = 0.0
    
    # Adaptive metrics
    adaptive_threshold: int = 5
    recent_performance_trend: float = 0.0


class BulkheadSemaphore:
    """Bulkhead pattern implementation for service isolation."""
    
    def __init__(self, max_concurrent: int, queue_capacity: int, queue_timeout: float):
        self.max_concurrent = max_concurrent
        self.queue_capacity = queue_capacity
        self.queue_timeout = queue_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue_size = 0
        self.rejected_count = 0
    
    async def acquire(self) -> bool:
        """Acquire a permit from the bulkhead."""
        if self.queue_size >= self.queue_capacity:
            self.rejected_count += 1
            return False
        
        self.queue_size += 1
        try:
            acquired = await asyncio.wait_for(
                self.semaphore.acquire(),
                timeout=self.queue_timeout
            )
            return acquired
        except asyncio.TimeoutError:
            return False
        finally:
            self.queue_size -= 1
    
    def release(self) -> None:
        """Release a permit back to the bulkhead."""
        self.semaphore.release()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics."""
        return {
            "max_concurrent": self.max_concurrent,
            "available_permits": self.semaphore._value,
            "queue_size": self.queue_size,
            "queue_capacity": self.queue_capacity,
            "rejected_count": self.rejected_count
        }


class AdvancedCircuitBreaker:
    """Advanced circuit breaker with Hystrix-style features."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig, redis_client=None):
        self.name = name
        self.config = config
        self.redis_client = redis_client
        
        # State management
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        
        # Metrics and tracking
        self.metrics = CircuitMetrics()
        self.call_history: deque = deque(maxlen=1000)  # Keep last 1000 calls
        self.response_times: deque = deque(maxlen=100)  # Keep last 100 response times
        
        # Bulkhead for service isolation
        self.bulkhead = None
        if config.enable_bulkhead:
            self.bulkhead = BulkheadSemaphore(
                config.max_concurrent_calls,
                config.queue_capacity,
                config.queue_timeout
            )
        
        # Distributed state management
        self.distributed_state_key = f"circuit_breaker:{name}:state"
        self.last_state_sync = 0.0
        
        # Background tasks
        self.background_tasks: set = set()
        self.started = False
        
        logger.info(f"Advanced circuit breaker '{name}' initialized")
    
    async def start(self) -> None:
        """Start the circuit breaker background tasks."""
        if self.started:
            return
        
        self.started = True
        
        # Start background tasks
        if self.config.enable_distributed_state and self.redis_client:
            sync_task = asyncio.create_task(self._sync_distributed_state())
            self.background_tasks.add(sync_task)
        
        metrics_task = asyncio.create_task(self._update_metrics())
        self.background_tasks.add(metrics_task)
        
        cleanup_task = asyncio.create_task(self._cleanup_old_data())
        self.background_tasks.add(cleanup_task)
        
        logger.info(f"Circuit breaker '{self.name}' started")
    
    async def stop(self) -> None:
        """Stop the circuit breaker."""
        self.started = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        logger.info(f"Circuit breaker '{self.name}' stopped")
    
    async def call(self, func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
        """Execute a function call through the circuit breaker."""
        call_start = time.time()
        
        # Check if circuit allows the call
        if not await self._is_call_permitted():
            circuit_breaker_requests.labels(
                service=self.name, 
                state=self.state.value, 
                result="rejected"
            ).inc()
            raise CircuitBreakerError(f"Circuit breaker '{self.name}' is {self.state.value}")
        
        # Acquire bulkhead permit if enabled
        if self.bulkhead:
            if not await self.bulkhead.acquire():
                circuit_breaker_requests.labels(
                    service=self.name, 
                    state=self.state.value, 
                    result="bulkhead_rejected"
                ).inc()
                raise CircuitBreakerError(f"Bulkhead full for service '{self.name}'")
        
        try:
            # Execute the function with timeout
            call_timeout = timeout or self.config.timeout_seconds
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=call_timeout)
            
            # Record successful call
            call_duration = time.time() - call_start
            await self._record_success(call_duration)
            
            circuit_breaker_requests.labels(
                service=self.name, 
                state=self.state.value, 
                result="success"
            ).inc()
            
            circuit_breaker_response_time.labels(
                service=self.name, 
                state=self.state.value
            ).observe(call_duration)
            
            return result
            
        except asyncio.TimeoutError:
            call_duration = time.time() - call_start
            await self._record_failure(call_duration, FailureType.TIMEOUT, "Function call timed out")
            
            circuit_breaker_requests.labels(
                service=self.name, 
                state=self.state.value, 
                result="timeout"
            ).inc()
            
            raise TimeoutError(f"Call to '{self.name}' timed out after {call_timeout}s")
            
        except Exception as e:
            call_duration = time.time() - call_start
            await self._record_failure(call_duration, FailureType.ERROR, str(e))
            
            circuit_breaker_requests.labels(
                service=self.name, 
                state=self.state.value, 
                result="error"
            ).inc()
            
            raise
            
        finally:
            if self.bulkhead:
                self.bulkhead.release()
    
    async def _is_call_permitted(self) -> bool:
        """Check if a call is permitted based on current circuit state."""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if current_time - self.last_state_change >= self.config.open_state_duration:
                await self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            if self.half_open_calls < self.config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False
    
    async def _record_success(self, duration: float) -> None:
        """Record a successful call."""
        call_result = CallResult(success=True, duration=duration)
        self.call_history.append(call_result)
        self.response_times.append(duration)
        
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        
        # Check for slow calls
        if duration > self.config.slow_call_threshold:
            self.metrics.slow_requests += 1
        
        # State transitions based on success
        if self.state == CircuitState.HALF_OPEN:
            if self.consecutive_successes >= self.config.recovery_threshold:
                await self._transition_to_closed()
    
    async def _record_failure(self, duration: float, failure_type: FailureType, error_message: str) -> None:
        """Record a failed call."""
        call_result = CallResult(
            success=False, 
            duration=duration, 
            failure_type=failure_type,
            error_message=error_message
        )
        self.call_history.append(call_result)
        
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        
        if failure_type == FailureType.TIMEOUT:
            self.metrics.timeout_requests += 1
        
        # Check if we should open the circuit
        await self._check_circuit_opening_conditions()
    
    async def _check_circuit_opening_conditions(self) -> None:
        """Check if circuit should be opened based on failure conditions."""
        if self.state == CircuitState.OPEN:
            return
        
        current_time = time.time()
        
        # Get recent calls within the failure window
        recent_calls = [
            call for call in self.call_history 
            if current_time - call.timestamp <= self.config.failure_window_seconds
        ]
        
        if len(recent_calls) < self.config.minimum_requests:
            return
        
        # Calculate failure rates
        failed_calls = [call for call in recent_calls if not call.success]
        slow_calls = [call for call in recent_calls if call.duration > self.config.slow_call_threshold]
        
        failure_rate = len(failed_calls) / len(recent_calls)
        slow_call_rate = len(slow_calls) / len(recent_calls)
        
        self.metrics.current_failure_rate = failure_rate
        self.metrics.current_slow_call_rate = slow_call_rate
        
        # Update Prometheus metrics
        circuit_breaker_failure_rate.labels(service=self.name).set(failure_rate)
        
        # Check opening conditions
        should_open = False
        
        # Condition 1: Failure rate threshold exceeded
        if failure_rate >= self.config.failure_rate_threshold:
            logger.warning(f"Circuit '{self.name}' failure rate {failure_rate:.2%} exceeds threshold {self.config.failure_rate_threshold:.2%}")
            should_open = True
        
        # Condition 2: Slow call rate threshold exceeded
        if slow_call_rate >= self.config.slow_call_rate_threshold:
            logger.warning(f"Circuit '{self.name}' slow call rate {slow_call_rate:.2%} exceeds threshold {self.config.slow_call_rate_threshold:.2%}")
            should_open = True
        
        # Condition 3: Consecutive failures threshold (traditional circuit breaker)
        adaptive_threshold = self._get_adaptive_threshold()
        if self.consecutive_failures >= adaptive_threshold:
            logger.warning(f"Circuit '{self.name}' consecutive failures {self.consecutive_failures} exceeds adaptive threshold {adaptive_threshold}")
            should_open = True
        
        if should_open:
            await self._transition_to_open()
    
    def _get_adaptive_threshold(self) -> int:
        """Get adaptive failure threshold based on recent performance."""
        if not self.config.enable_adaptive_threshold:
            return self.config.failure_threshold
        
        # Calculate recent performance trend
        if len(self.response_times) >= 10:
            recent_times = list(self.response_times)[-10:]
            avg_recent = statistics.mean(recent_times)
            
            # If recent performance is good, lower threshold (more sensitive)
            # If recent performance is poor, raise threshold (less sensitive)
            if avg_recent < self.config.slow_call_threshold * 0.5:
                # Good performance - be more sensitive
                adjustment = -1
            elif avg_recent > self.config.slow_call_threshold:
                # Poor performance - be less sensitive
                adjustment = 1
            else:
                adjustment = 0
            
            new_threshold = self.metrics.adaptive_threshold + adjustment
            new_threshold = max(self.config.min_failure_threshold, 
                              min(self.config.max_failure_threshold, new_threshold))
            
            self.metrics.adaptive_threshold = new_threshold
        
        return self.metrics.adaptive_threshold
    
    async def _transition_to_open(self) -> None:
        """Transition circuit to OPEN state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self.metrics.state_changes += 1
        self.metrics.last_state_change = self.last_state_change
        
        logger.warning(f"Circuit breaker '{self.name}' opened")
        
        circuit_breaker_state_changes.labels(
            service=self.name,
            from_state=old_state.value,
            to_state=self.state.value
        ).inc()
        
        # Sync state to distributed store
        await self._sync_state_to_distributed_store()
    
    async def _transition_to_half_open(self) -> None:
        """Transition circuit to HALF_OPEN state."""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.metrics.state_changes += 1
        self.metrics.last_state_change = self.last_state_change
        
        logger.info(f"Circuit breaker '{self.name}' half-opened")
        
        circuit_breaker_state_changes.labels(
            service=self.name,
            from_state=old_state.value,
            to_state=self.state.value
        ).inc()
        
        # Sync state to distributed store
        await self._sync_state_to_distributed_store()
    
    async def _transition_to_closed(self) -> None:
        """Transition circuit to CLOSED state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self.consecutive_failures = 0
        self.metrics.state_changes += 1
        self.metrics.last_state_change = self.last_state_change
        
        logger.info(f"Circuit breaker '{self.name}' closed")
        
        circuit_breaker_state_changes.labels(
            service=self.name,
            from_state=old_state.value,
            to_state=self.state.value
        ).inc()
        
        # Sync state to distributed store
        await self._sync_state_to_distributed_store()
    
    async def _sync_state_to_distributed_store(self) -> None:
        """Sync circuit state to distributed store."""
        if not self.config.enable_distributed_state or not self.redis_client:
            return
        
        try:
            state_data = {
                "state": self.state.value,
                "last_state_change": self.last_state_change,
                "consecutive_failures": self.consecutive_failures,
                "consecutive_successes": self.consecutive_successes,
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "current_failure_rate": self.metrics.current_failure_rate,
                    "adaptive_threshold": self.metrics.adaptive_threshold
                }
            }
            
            await self.redis_client.setex(
                self.distributed_state_key,
                self.config.distributed_state_ttl,
                json.dumps(state_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to sync circuit state to distributed store: {e}")
    
    async def _sync_distributed_state(self) -> None:
        """Background task to sync with distributed circuit state."""
        while self.started:
            try:
                current_time = time.time()
                
                if current_time - self.last_state_sync >= self.config.state_sync_interval:
                    await self._check_distributed_state()
                    self.last_state_sync = current_time
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Distributed state sync error: {e}")
                await asyncio.sleep(5)
    
    async def _check_distributed_state(self) -> None:
        """Check and potentially update from distributed state."""
        if not self.redis_client:
            return
        
        try:
            state_data = await self.redis_client.get(self.distributed_state_key)
            if state_data:
                remote_state = json.loads(state_data)
                remote_circuit_state = CircuitState(remote_state["state"])
                
                # If remote state is more restrictive (OPEN), adopt it
                if (self.state == CircuitState.CLOSED and 
                    remote_circuit_state == CircuitState.OPEN):
                    
                    logger.info(f"Adopting distributed OPEN state for circuit '{self.name}'")
                    await self._transition_to_open()
                
        except Exception as e:
            logger.error(f"Failed to check distributed state: {e}")
    
    async def _update_metrics(self) -> None:
        """Background task to update metrics."""
        while self.started:
            try:
                current_time = time.time()
                
                # Update time in current state
                self.metrics.time_in_current_state = current_time - self.last_state_change
                
                # Calculate average response time
                if self.response_times:
                    self.metrics.average_response_time = statistics.mean(self.response_times)
                
                # Update performance trend
                if len(self.response_times) >= 10:
                    recent_avg = statistics.mean(list(self.response_times)[-5:])
                    older_avg = statistics.mean(list(self.response_times)[-10:-5])
                    self.metrics.recent_performance_trend = recent_avg - older_avg
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_old_data(self) -> None:
        """Background task to clean up old data."""
        while self.started:
            try:
                current_time = time.time()
                
                # Remove old call history (older than failure window * 2)
                cutoff_time = current_time - (self.config.failure_window_seconds * 2)
                
                # Clean call history
                while (self.call_history and 
                       self.call_history[0].timestamp < cutoff_time):
                    self.call_history.popleft()
                
                await asyncio.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(60)
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive circuit breaker metrics."""
        current_time = time.time()
        
        # Calculate recent metrics
        recent_calls = [
            call for call in self.call_history 
            if current_time - call.timestamp <= self.config.failure_window_seconds
        ]
        
        recent_failures = len([call for call in recent_calls if not call.success])
        recent_successes = len([call for call in recent_calls if call.success])
        
        metrics = {
            "name": self.name,
            "state": self.state.value,
            "last_state_change": self.last_state_change,
            "time_in_current_state": current_time - self.last_state_change,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "half_open_calls": self.half_open_calls,
            
            # Overall metrics
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "timeout_requests": self.metrics.timeout_requests,
            "slow_requests": self.metrics.slow_requests,
            
            # Rates and averages
            "current_failure_rate": self.metrics.current_failure_rate,
            "current_slow_call_rate": self.metrics.current_slow_call_rate,
            "average_response_time": self.metrics.average_response_time,
            
            # Recent window metrics
            "recent_total_calls": len(recent_calls),
            "recent_failures": recent_failures,
            "recent_successes": recent_successes,
            "recent_failure_rate": recent_failures / len(recent_calls) if recent_calls else 0,
            
            # Adaptive behavior
            "adaptive_threshold": self.metrics.adaptive_threshold,
            "performance_trend": self.metrics.recent_performance_trend,
            
            # Configuration
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "failure_rate_threshold": self.config.failure_rate_threshold,
                "slow_call_threshold": self.config.slow_call_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "enable_adaptive_threshold": self.config.enable_adaptive_threshold,
                "enable_distributed_state": self.config.enable_distributed_state
            }
        }
        
        # Add bulkhead metrics if enabled
        if self.bulkhead:
            metrics["bulkhead"] = self.bulkhead.get_stats()
        
        return metrics
    
    async def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        logger.info(f"Resetting circuit breaker '{self.name}'")
        
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        
        # Reset metrics
        self.metrics = CircuitMetrics()
        self.call_history.clear()
        self.response_times.clear()
        
        circuit_breaker_state_changes.labels(
            service=self.name,
            from_state=old_state.value,
            to_state=self.state.value
        ).inc()
        
        # Sync reset state
        await self._sync_state_to_distributed_store()


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""
    
    def __init__(self, default_config: CircuitBreakerConfig, redis_client=None):
        self.default_config = default_config
        self.redis_client = redis_client
        self.circuit_breakers: Dict[str, AdvancedCircuitBreaker] = {}
        self.started = False
    
    async def start(self) -> None:
        """Start all circuit breakers."""
        if self.started:
            return
        
        self.started = True
        
        # Start all existing circuit breakers
        for cb in self.circuit_breakers.values():
            await cb.start()
        
        logger.info("Circuit breaker manager started")
    
    async def stop(self) -> None:
        """Stop all circuit breakers."""
        self.started = False
        
        # Stop all circuit breakers
        for cb in self.circuit_breakers.values():
            await cb.stop()
        
        logger.info("Circuit breaker manager stopped")
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> AdvancedCircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuit_breakers:
            cb_config = config or self.default_config
            self.circuit_breakers[name] = AdvancedCircuitBreaker(
                name, cb_config, self.redis_client
            )
            
            # Start the circuit breaker if manager is started
            if self.started:
                asyncio.create_task(self.circuit_breakers[name].start())
        
        return self.circuit_breakers[name]
    
    async def execute_with_circuit_breaker(self, service_name: str, func: Callable, 
                                         *args, timeout: Optional[float] = None, 
                                         config: Optional[CircuitBreakerConfig] = None, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        circuit_breaker = self.get_circuit_breaker(service_name, config)
        return await circuit_breaker.call(func, *args, timeout=timeout, **kwargs)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all circuit breakers."""
        return {
            name: cb.get_metrics() 
            for name, cb in self.circuit_breakers.items()
        }
    
    async def reset_circuit_breaker(self, name: str) -> bool:
        """Reset a specific circuit breaker."""
        if name in self.circuit_breakers:
            await self.circuit_breakers[name].reset()
            return True
        return False
    
    async def reset_all_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            await cb.reset()


# Backward compatibility aliases
CircuitBreaker = AdvancedCircuitBreaker 