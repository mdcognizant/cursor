#!/usr/bin/env python3
"""
Multi-Armed Bandit Load Balancer for Optimal Server Selection
Implementation of HTML Document Section 4: "Adaptive Load Balancing & Scheduling"

Mathematical Foundation:
UCB1 Algorithm: Select server i with highest:
UCB1(i) = X̄ᵢ + √(2 ln n / nᵢ)

Where:
- X̄ᵢ = average reward (1/latency) for server i
- n = total selections across all servers
- nᵢ = selections for server i

This mathematically maximizes reward (throughput) while minimizing latency.
"""

import asyncio
import time
import logging
import math
import statistics
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from threading import Lock, RLock
import uuid
import random

logger = logging.getLogger(__name__)

# =====================================================================================
# SERVER PERFORMANCE MODELING
# =====================================================================================

@dataclass
class ServerInstance:
    """Enhanced server instance with mathematical performance modeling."""
    
    id: str
    host: str
    port: int
    weight: float = 1.0
    
    # Thread-safe performance metrics
    _selection_count: int = field(default_factory=lambda: 0)
    _success_count: int = field(default_factory=lambda: 0)
    _total_latency_ms: float = field(default_factory=lambda: 0.0)
    _total_reward: float = field(default_factory=lambda: 0.0)
    _lock: Lock = field(default_factory=Lock)
    
    # Performance samples for analysis
    latency_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    reward_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Health and status
    is_healthy: bool = True
    last_health_check: float = field(default_factory=time.time)
    registration_time: float = field(default_factory=time.time)
    
    @property
    def selection_count(self) -> int:
        """Thread-safe access to selection count."""
        with self._lock:
            return self._selection_count
    
    @property
    def success_count(self) -> int:
        """Thread-safe access to success count."""
        with self._lock:
            return self._success_count
    
    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        with self._lock:
            if self._success_count == 0:
                return float('inf')
            return self._total_latency_ms / self._success_count
    
    @property
    def average_reward(self) -> float:
        """Calculate average reward (1/latency typically)."""
        with self._lock:
            if self._selection_count == 0:
                return 0.0
            return self._total_reward / self._selection_count
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        with self._lock:
            if self._selection_count == 0:
                return 1.0
            return self._success_count / self._selection_count
    
    def record_request_result(self, latency_ms: float, success: bool = True):
        """Record the result of a request to this server."""
        with self._lock:
            self._selection_count += 1
            
            if success:
                self._success_count += 1
                self._total_latency_ms += latency_ms
                
                # Calculate reward (1/latency - higher reward for lower latency)
                reward = 1.0 / max(latency_ms, 0.001)  # Avoid division by zero
                self._total_reward += reward
                
                # Store samples for analysis
                self.latency_samples.append(latency_ms)
                self.reward_samples.append(reward)
    
    def calculate_ucb1_score(self, total_selections: int, exploration_factor: float = 2.0) -> float:
        """
        Calculate UCB1 score for this server
        Reference: HTML Document multi-armed bandit algorithm
        """
        if self.selection_count == 0:
            return float('inf')  # Always try untested servers
        
        if not self.is_healthy:
            return -float('inf')  # Never select unhealthy servers
        
        # UCB1 formula: X̄ᵢ + √(c * ln(n) / nᵢ)
        avg_reward = self.average_reward
        exploration_bonus = math.sqrt(
            (exploration_factor * math.log(max(total_selections, 1))) / self.selection_count
        )
        
        return avg_reward + exploration_bonus
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        with self._lock:
            return {
                "server_id": self.id,
                "host": self.host,
                "port": self.port,
                "selection_count": self._selection_count,
                "success_count": self._success_count,
                "success_rate": self.success_rate,
                "average_latency_ms": self.average_latency_ms,
                "average_reward": self.average_reward,
                "is_healthy": self.is_healthy,
                "recent_latencies": list(self.latency_samples)[-10:] if self.latency_samples else []
            }


# =====================================================================================
# MULTI-ARMED BANDIT LOAD BALANCER
# =====================================================================================

class MultiArmedBanditLoadBalancer:
    """
    Advanced load balancer using multi-armed bandit algorithms
    Reference: HTML Document Section 4 - "Adaptive Load Balancing & Scheduling"
    """
    
    def __init__(self, exploration_factor: float = 2.0):
        self.servers: Dict[str, ServerInstance] = {}
        self.total_selections = 0
        self.exploration_factor = exploration_factor
        
        # Thread safety
        self._lock = RLock()
        
        # Performance tracking
        self.selection_history = deque(maxlen=1000)
        self.algorithm_stats = {
            "total_requests": 0,
            "optimal_selections": 0,
            "exploration_selections": 0,
            "regret_accumulation": 0.0
        }
        
        logger.info(f"Multi-Armed Bandit Load Balancer initialized (exploration_factor={exploration_factor})")
    
    def register_server(self, server_id: str, host: str, port: int, weight: float = 1.0):
        """Register a new server instance."""
        with self._lock:
            server = ServerInstance(
                id=server_id,
                host=host,
                port=port,
                weight=weight
            )
            self.servers[server_id] = server
            logger.info(f"Registered server {server_id} at {host}:{port}")
    
    def deregister_server(self, server_id: str):
        """Remove a server instance."""
        with self._lock:
            if server_id in self.servers:
                del self.servers[server_id]
                logger.info(f"Deregistered server {server_id}")
    
    def mark_server_health(self, server_id: str, is_healthy: bool):
        """Mark server as healthy or unhealthy."""
        with self._lock:
            if server_id in self.servers:
                self.servers[server_id].is_healthy = is_healthy
                self.servers[server_id].last_health_check = time.time()
                logger.info(f"Server {server_id} marked as {'healthy' if is_healthy else 'unhealthy'}")
    
    def select_server(self, request_context: Optional[Dict[str, Any]] = None) -> Optional[ServerInstance]:
        """
        Select optimal server using UCB1 multi-armed bandit algorithm
        Reference: HTML Document mathematical foundation
        """
        with self._lock:
            if not self.servers:
                return None
            
            healthy_servers = [s for s in self.servers.values() if s.is_healthy]
            if not healthy_servers:
                logger.warning("No healthy servers available")
                return None
            
            # Calculate UCB1 scores for all healthy servers
            server_scores = []
            for server in healthy_servers:
                ucb1_score = server.calculate_ucb1_score(
                    total_selections=self.total_selections,
                    exploration_factor=self.exploration_factor
                )
                server_scores.append((server, ucb1_score))
            
            # Select server with highest UCB1 score
            selected_server, best_score = max(server_scores, key=lambda x: x[1])
            
            # Update selection tracking
            self.total_selections += 1
            self.algorithm_stats["total_requests"] += 1
            
            # Determine if this was exploration or exploitation
            if selected_server.selection_count == 0:
                self.algorithm_stats["exploration_selections"] += 1
            else:
                # Check if this was the optimal choice (server with lowest average latency)
                best_performing_server = min(
                    [s for s in healthy_servers if s.selection_count > 0],
                    key=lambda s: s.average_latency_ms,
                    default=selected_server
                )
                
                if selected_server == best_performing_server:
                    self.algorithm_stats["optimal_selections"] += 1
            
            # Record selection in history
            self.selection_history.append({
                "timestamp": time.time(),
                "server_id": selected_server.id,
                "ucb1_score": best_score,
                "selection_count": selected_server.selection_count,
                "avg_latency": selected_server.average_latency_ms
            })
            
            return selected_server
    
    def record_request_result(self, server_id: str, latency_ms: float, success: bool = True):
        """Record the result of a request for learning."""
        with self._lock:
            if server_id in self.servers:
                self.servers[server_id].record_request_result(latency_ms, success)
                
                # Calculate regret (difference from optimal choice)
                if success:
                    optimal_latency = self._get_optimal_latency()
                    regret = max(0.0, latency_ms - optimal_latency)
                    self.algorithm_stats["regret_accumulation"] += regret
    
    def _get_optimal_latency(self) -> float:
        """Get the current optimal (lowest) average latency."""
        with self._lock:
            tested_servers = [s for s in self.servers.values() if s.selection_count > 0 and s.is_healthy]
            if not tested_servers:
                return 1.0  # Default if no data
            
            return min(s.average_latency_ms for s in tested_servers)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive load balancer statistics."""
        with self._lock:
            server_stats = {
                server_id: server.get_performance_stats()
                for server_id, server in self.servers.items()
            }
            
            # Calculate algorithm efficiency
            exploration_rate = (
                self.algorithm_stats["exploration_selections"] / 
                max(1, self.algorithm_stats["total_requests"])
            )
            
            exploitation_rate = (
                self.algorithm_stats["optimal_selections"] / 
                max(1, self.algorithm_stats["total_requests"])
            )
            
            avg_regret = (
                self.algorithm_stats["regret_accumulation"] / 
                max(1, self.algorithm_stats["total_requests"])
            )
            
            return {
                "algorithm": "UCB1 Multi-Armed Bandit",
                "total_selections": self.total_selections,
                "exploration_factor": self.exploration_factor,
                "server_count": len(self.servers),
                "healthy_server_count": sum(1 for s in self.servers.values() if s.is_healthy),
                "algorithm_performance": {
                    "exploration_rate": exploration_rate,
                    "exploitation_rate": exploitation_rate,
                    "average_regret_ms": avg_regret,
                    "efficiency_score": exploitation_rate * (1 - avg_regret / 100.0)  # Normalize regret
                },
                "server_statistics": server_stats,
                "recent_selections": list(self.selection_history)[-10:]
            }
    
    def optimize_exploration_factor(self):
        """
        Dynamically optimize exploration factor based on performance
        Reference: HTML Document adaptive optimization
        """
        with self._lock:
            if self.algorithm_stats["total_requests"] < 100:
                return  # Need sufficient data
            
            current_regret = (
                self.algorithm_stats["regret_accumulation"] / 
                self.algorithm_stats["total_requests"]
            )
            
            # Adjust exploration factor based on regret
            if current_regret > 10.0:  # High regret - need more exploration
                self.exploration_factor = min(5.0, self.exploration_factor * 1.1)
            elif current_regret < 2.0:  # Low regret - can reduce exploration
                self.exploration_factor = max(0.5, self.exploration_factor * 0.95)
            
            logger.debug(f"Adjusted exploration factor to {self.exploration_factor:.2f} (regret: {current_regret:.2f}ms)")


# =====================================================================================
# ENHANCED LOAD BALANCER WITH ADDITIONAL ALGORITHMS
# =====================================================================================

class EnhancedLoadBalancer(MultiArmedBanditLoadBalancer):
    """
    Enhanced load balancer with multiple algorithms and dynamic switching
    Reference: HTML Document advanced mathematical optimizations
    """
    
    def __init__(self, exploration_factor: float = 2.0):
        super().__init__(exploration_factor)
        
        # Algorithm selection
        self.available_algorithms = ["ucb1", "epsilon_greedy", "thompson_sampling"]
        self.current_algorithm = "ucb1"
        self.algorithm_performance = defaultdict(lambda: {"requests": 0, "total_latency": 0.0})
        
        # Algorithm switching parameters
        self.algorithm_evaluation_window = 100
        self.last_algorithm_switch = time.time()
        self.algorithm_switch_cooldown = 60.0  # seconds
    
    def select_server_with_algorithm(self, algorithm: str = None, request_context: Dict = None) -> Optional[ServerInstance]:
        """Select server using specified algorithm or auto-selected algorithm."""
        if algorithm is None:
            algorithm = self.current_algorithm
        
        with self._lock:
            healthy_servers = [s for s in self.servers.values() if s.is_healthy]
            if not healthy_servers:
                return None
            
            if algorithm == "ucb1":
                return self._select_ucb1(healthy_servers)
            elif algorithm == "epsilon_greedy":
                return self._select_epsilon_greedy(healthy_servers, epsilon=0.1)
            elif algorithm == "thompson_sampling":
                return self._select_thompson_sampling(healthy_servers)
            else:
                return self._select_ucb1(healthy_servers)  # Default fallback
    
    def _select_ucb1(self, healthy_servers: List[ServerInstance]) -> ServerInstance:
        """UCB1 selection (existing implementation)."""
        server_scores = []
        for server in healthy_servers:
            ucb1_score = server.calculate_ucb1_score(
                total_selections=self.total_selections,
                exploration_factor=self.exploration_factor
            )
            server_scores.append((server, ucb1_score))
        
        selected_server, _ = max(server_scores, key=lambda x: x[1])
        self.total_selections += 1
        return selected_server
    
    def _select_epsilon_greedy(self, healthy_servers: List[ServerInstance], epsilon: float = 0.1) -> ServerInstance:
        """Epsilon-greedy selection algorithm."""
        self.total_selections += 1
        
        if random.random() < epsilon:
            # Exploration: random selection
            return random.choice(healthy_servers)
        else:
            # Exploitation: select best performing server
            tested_servers = [s for s in healthy_servers if s.selection_count > 0]
            if not tested_servers:
                return random.choice(healthy_servers)
            
            return min(tested_servers, key=lambda s: s.average_latency_ms)
    
    def _select_thompson_sampling(self, healthy_servers: List[ServerInstance]) -> ServerInstance:
        """Thompson sampling selection algorithm."""
        # Simplified Thompson sampling using Beta distribution parameters
        self.total_selections += 1
        
        best_sample = -float('inf')
        best_server = None
        
        for server in healthy_servers:
            if server.selection_count == 0:
                # Untested server - give high priority
                sample = random.betavariate(1, 1)  # Uniform prior
            else:
                # Use success rate to parameterize Beta distribution
                alpha = server.success_count + 1
                beta = (server.selection_count - server.success_count) + 1
                sample = random.betavariate(alpha, beta)
                
                # Weight by inverse latency
                if server.average_latency_ms > 0:
                    sample *= (1.0 / server.average_latency_ms)
            
            if sample > best_sample:
                best_sample = sample
                best_server = server
        
        return best_server or healthy_servers[0]
    
    def auto_optimize_algorithm(self):
        """
        Automatically switch to the best performing algorithm
        Reference: HTML Document adaptive optimization
        """
        with self._lock:
            current_time = time.time()
            
            # Check cooldown
            if current_time - self.last_algorithm_switch < self.algorithm_switch_cooldown:
                return
            
            # Need sufficient data for each algorithm
            min_requests_per_algo = 50
            if any(self.algorithm_performance[algo]["requests"] < min_requests_per_algo 
                   for algo in self.available_algorithms):
                return
            
            # Calculate average latency for each algorithm
            algo_avg_latencies = {}
            for algo in self.available_algorithms:
                stats = self.algorithm_performance[algo]
                if stats["requests"] > 0:
                    algo_avg_latencies[algo] = stats["total_latency"] / stats["requests"]
            
            # Select best performing algorithm
            if algo_avg_latencies:
                best_algorithm = min(algo_avg_latencies.keys(), key=lambda a: algo_avg_latencies[a])
                
                if best_algorithm != self.current_algorithm:
                    old_algorithm = self.current_algorithm
                    self.current_algorithm = best_algorithm
                    self.last_algorithm_switch = current_time
                    
                    logger.info(f"Switched from {old_algorithm} to {best_algorithm} "
                              f"(avg latency: {algo_avg_latencies[best_algorithm]:.2f}ms)")


# =====================================================================================
# DEMO AND TESTING
# =====================================================================================

async def simulate_server_request(server: ServerInstance, base_latency: float = 10.0) -> float:
    """Simulate a request to a server with variable latency."""
    # Simulate different server characteristics
    server_multiplier = hash(server.id) % 100 / 100.0  # Consistent per-server multiplier
    latency_variation = random.uniform(0.8, 1.2)  # Random variation
    
    simulated_latency = base_latency * (1.0 + server_multiplier) * latency_variation
    
    # Simulate network delay
    await asyncio.sleep(simulated_latency / 1000.0)
    
    return simulated_latency


async def demo_multi_armed_bandit_lb():
    """Demonstrate multi-armed bandit load balancer."""
    print("Multi-Armed Bandit Load Balancer Demonstration")
    print("=" * 60)
    
    # Create load balancer
    lb = EnhancedLoadBalancer(exploration_factor=2.0)
    
    # Register servers with different characteristics
    servers = [
        ("server_fast", "10.0.0.1", 8001),
        ("server_medium", "10.0.0.2", 8002),
        ("server_slow", "10.0.0.3", 8003),
        ("server_unstable", "10.0.0.4", 8004)
    ]
    
    for server_id, host, port in servers:
        lb.register_server(server_id, host, port)
    
    print(f"Registered {len(servers)} servers")
    
    # Simulate requests
    request_count = 200
    results = []
    
    print(f"Simulating {request_count} requests...")
    
    for i in range(request_count):
        # Select server using UCB1
        selected_server = lb.select_server()
        
        if selected_server:
            start_time = time.perf_counter()
            
            # Simulate the request
            try:
                latency = await simulate_server_request(selected_server, base_latency=5.0)
                success = True
            except Exception:
                latency = 1000.0  # Timeout
                success = False
            
            # Record result
            lb.record_request_result(selected_server.id, latency, success)
            
            results.append({
                "server_id": selected_server.id,
                "latency_ms": latency,
                "success": success
            })
            
            # Occasionally optimize
            if i % 50 == 0 and i > 0:
                lb.optimize_exploration_factor()
                print(f"Completed {i} requests...")
    
    # Analyze results
    print("\nResults Analysis:")
    print("=" * 60)
    
    server_latencies = defaultdict(list)
    for result in results:
        if result["success"]:
            server_latencies[result["server_id"]].append(result["latency_ms"])
    
    for server_id, latencies in server_latencies.items():
        avg_latency = statistics.mean(latencies)
        selection_count = len(latencies)
        print(f"{server_id}: {selection_count} selections, avg latency: {avg_latency:.2f}ms")
    
    # Get comprehensive stats
    print("\nLoad Balancer Statistics:")
    print("=" * 60)
    stats = lb.get_comprehensive_stats()
    
    print(f"Algorithm: {stats['algorithm']}")
    print(f"Total selections: {stats['total_selections']}")
    print(f"Exploration rate: {stats['algorithm_performance']['exploration_rate']:.2%}")
    print(f"Exploitation rate: {stats['algorithm_performance']['exploitation_rate']:.2%}")
    print(f"Average regret: {stats['algorithm_performance']['average_regret_ms']:.2f}ms")
    print(f"Efficiency score: {stats['algorithm_performance']['efficiency_score']:.3f}")


if __name__ == "__main__":
    asyncio.run(demo_multi_armed_bandit_lb()) 