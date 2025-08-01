#!/usr/bin/env python3
"""
gRPC vs REST Performance Comparison Benchmark

This module provides comprehensive comparison between:
- Universal API Bridge (gRPC backend)
- Traditional REST API implementations
- Direct API calls without bridge

Performance metrics compared:
- Latency (P50, P95, P99, P99.9)
- Throughput (RPS)
- Resource utilization (CPU, Memory)
- Error rates
- Scalability under load
"""

import asyncio
import time
import logging
import aiohttp
import statistics
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import random
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bridge import UniversalAPIBridge
from config import UnifiedBridgeConfig
from performance_test_suite import PerformanceMetrics, ResourceMonitor

logger = logging.getLogger(__name__)

@dataclass
class ComparisonScenario:
    """Defines a scenario for gRPC vs REST comparison."""
    
    name: str
    description: str
    request_count: int
    concurrent_requests: int
    payload_size_kb: float
    complexity_level: str  # 'simple', 'medium', 'complex'
    
    # Request pattern for testing
    method: str = "POST"
    path: str = "/api/v1/test"
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}


class MockRESTAPIServer:
    """Mock traditional REST API server for comparison."""
    
    def __init__(self):
        self.request_count = 0
        self.processing_times = []
        
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate traditional REST API processing."""
        
        start_time = time.perf_counter()
        self.request_count += 1
        
        # Simulate processing delay based on complexity
        payload_size = len(str(request_data))
        
        if payload_size < 1000:
            # Simple request - 2-5ms processing
            processing_delay = random.uniform(0.002, 0.005)
        elif payload_size < 10000:
            # Medium request - 5-15ms processing
            processing_delay = random.uniform(0.005, 0.015)
        else:
            # Complex request - 15-50ms processing
            processing_delay = random.uniform(0.015, 0.050)
        
        # Add network simulation delay
        network_delay = random.uniform(0.001, 0.003)  # 1-3ms network
        
        await asyncio.sleep(processing_delay + network_delay)
        
        processing_time = time.perf_counter() - start_time
        self.processing_times.append(processing_time * 1000)  # Convert to ms
        
        return {
            'status': 'success',
            'data': {
                'processed_at': time.time(),
                'request_size': payload_size,
                'processing_time_ms': processing_time * 1000,
                'server_type': 'traditional_rest'
            },
            'request_id': f'rest_req_{self.request_count}'
        }


class DirectAPIClient:
    """Direct API client without any middleware for baseline comparison."""
    
    def __init__(self):
        self.request_count = 0
        
    async def call_api(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Direct API call with minimal overhead."""
        
        start_time = time.perf_counter()
        self.request_count += 1
        
        # Minimal processing - just echo back with timestamp
        await asyncio.sleep(0.0001)  # 0.1ms minimal processing
        
        processing_time = time.perf_counter() - start_time
        
        return {
            'status': 'success',
            'data': request_data,
            'processing_time_ms': processing_time * 1000,
            'client_type': 'direct_api',
            'request_id': f'direct_req_{self.request_count}'
        }


class PerformanceComparator:
    """Compare performance between different API approaches."""
    
    def __init__(self):
        self.bridge = None
        self.rest_server = MockRESTAPIServer()
        self.direct_client = DirectAPIClient()
        
    async def run_comparison_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive comparison benchmark."""
        
        print("\n📊 gRPC vs REST PERFORMANCE COMPARISON BENCHMARK")
        print("=" * 80)
        
        # Initialize bridge
        await self._initialize_bridge()
        
        # Define comparison scenarios
        scenarios = [
            ComparisonScenario(
                name="Small Payload - Simple Processing",
                description="Small JSON payloads with simple processing",
                request_count=1000,
                concurrent_requests=10,
                payload_size_kb=0.5,
                complexity_level="simple"
            ),
            
            ComparisonScenario(
                name="Medium Payload - Standard Processing", 
                description="Medium JSON payloads with standard processing",
                request_count=500,
                concurrent_requests=20,
                payload_size_kb=5.0,
                complexity_level="medium"
            ),
            
            ComparisonScenario(
                name="Large Payload - Complex Processing",
                description="Large JSON payloads with complex processing",
                request_count=200,
                concurrent_requests=15,
                payload_size_kb=50.0,
                complexity_level="complex"
            ),
            
            ComparisonScenario(
                name="High Concurrency - Mixed Load",
                description="High concurrent load with mixed payload sizes",
                request_count=100,
                concurrent_requests=100,
                payload_size_kb=10.0,
                complexity_level="medium"
            )
        ]
        
        comparison_results = {}
        
        for scenario in scenarios:
            print(f"\n🧪 Running Comparison: {scenario.name}")
            print(f"   {scenario.description}")
            print(f"   Requests: {scenario.request_count}, Concurrency: {scenario.concurrent_requests}")
            
            # Run comparison for this scenario
            scenario_results = await self._run_scenario_comparison(scenario)
            comparison_results[scenario.name] = scenario_results
            
            # Display results
            self._display_scenario_results(scenario.name, scenario_results)
        
        # Generate comprehensive comparison report
        final_report = self._generate_comparison_report(comparison_results)
        
        print(f"\n✅ gRPC vs REST comparison completed!")
        
        return final_report
    
    async def _initialize_bridge(self):
        """Initialize Universal API Bridge for comparison."""
        
        config = UnifiedBridgeConfig.create_ultra_high_performance()
        self.bridge = UniversalAPIBridge(config)
        
        # Start bridge in test mode
        self.bridge.is_running = True
        self.bridge.start_time = time.time()
        await self.bridge.monitor.start_monitoring()
        
        print("✅ Universal API Bridge initialized for comparison")
    
    async def _run_scenario_comparison(self, scenario: ComparisonScenario) -> Dict[str, Any]:
        """Run performance comparison for a specific scenario."""
        
        # Generate test payload based on scenario
        test_payload = self._generate_test_payload(scenario)
        
        # Test 1: Universal API Bridge (gRPC backend)
        print("   🚀 Testing Universal API Bridge (gRPC backend)...")
        bridge_results = await self._test_bridge_performance(scenario, test_payload)
        
        # Test 2: Traditional REST API
        print("   🌐 Testing Traditional REST API...")
        rest_results = await self._test_rest_performance(scenario, test_payload)
        
        # Test 3: Direct API (baseline)
        print("   ⚡ Testing Direct API (baseline)...")
        direct_results = await self._test_direct_performance(scenario, test_payload)
        
        return {
            'scenario': scenario,
            'universal_api_bridge': bridge_results,
            'traditional_rest': rest_results,
            'direct_api': direct_results,
            'test_payload_size_kb': len(str(test_payload)) / 1024
        }
    
    def _generate_test_payload(self, scenario: ComparisonScenario) -> Dict[str, Any]:
        """Generate test payload based on scenario requirements."""
        
        # Base payload
        payload = {
            'scenario': scenario.name,
            'complexity': scenario.complexity_level,
            'timestamp': time.time()
        }
        
        # Add data to reach target size
        target_size_bytes = int(scenario.payload_size_kb * 1024)
        
        if scenario.complexity_level == "simple":
            # Simple flat structure
            payload['data'] = {
                'items': [f'item_{i}' for i in range(50)],
                'metadata': {'simple': True}
            }
        elif scenario.complexity_level == "medium":
            # Nested structure with arrays
            payload['data'] = {
                'users': [
                    {
                        'id': i,
                        'name': f'user_{i}',
                        'profile': {
                            'settings': [f'setting_{j}' for j in range(10)],
                            'preferences': {'theme': 'dark', 'lang': 'en'}
                        }
                    } for i in range(20)
                ],
                'statistics': {f'metric_{i}': random.randint(1, 1000) for i in range(50)}
            }
        else:  # complex
            # Deep nested structure with large arrays
            payload['data'] = {
                'complex_structure': {
                    'level1': {
                        'level2': {
                            'level3': {
                                'large_dataset': [
                                    {
                                        'id': i,
                                        'data': [random.random() for _ in range(20)],
                                        'metadata': {
                                            'tags': [f'tag_{j}' for j in range(10)],
                                            'attributes': {f'attr_{k}': f'value_{k}' for k in range(5)}
                                        }
                                    } for i in range(50)
                                ]
                            }
                        }
                    }
                }
            }
        
        # Pad to reach target size if needed
        current_size = len(str(payload))
        if current_size < target_size_bytes:
            padding_size = target_size_bytes - current_size
            payload['padding'] = 'x' * max(0, padding_size - 100)  # Leave room for JSON formatting
        
        return payload
    
    async def _test_bridge_performance(self, scenario: ComparisonScenario, 
                                     test_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test Universal API Bridge performance."""
        
        latencies = []
        successes = 0
        failures = 0
        
        # Resource monitoring
        resource_monitor = ResourceMonitor()
        await resource_monitor.start_monitoring()
        
        start_time = time.perf_counter()
        
        try:
            # Create concurrent tasks
            tasks = []
            for i in range(scenario.request_count):
                task = asyncio.create_task(
                    self._bridge_request(scenario, test_payload, i)
                )
                tasks.append(task)
                
                # Control concurrency
                if len(tasks) >= scenario.concurrent_requests:
                    # Wait for some tasks to complete
                    done_tasks = await asyncio.gather(*tasks[:scenario.concurrent_requests//2], return_exceptions=True)
                    
                    for result in done_tasks:
                        if isinstance(result, Exception):
                            failures += 1
                        else:
                            successes += 1
                            latencies.append(result)
                    
                    # Keep remaining tasks
                    tasks = tasks[scenario.concurrent_requests//2:]
            
            # Wait for remaining tasks
            if tasks:
                done_tasks = await asyncio.gather(*tasks, return_exceptions=True)
                for result in done_tasks:
                    if isinstance(result, Exception):
                        failures += 1
                    else:
                        successes += 1
                        latencies.append(result)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Get resource stats
            resource_stats = resource_monitor.get_resource_stats()
            
            return self._calculate_performance_stats(
                "Universal API Bridge", latencies, successes, failures, duration, resource_stats
            )
            
        finally:
            await resource_monitor.stop_monitoring()
    
    async def _bridge_request(self, scenario: ComparisonScenario, 
                            test_payload: Dict[str, Any], request_id: int) -> float:
        """Execute single request through bridge."""
        
        start_time = time.perf_counter()
        
        response = await self.bridge.process_request(
            method=scenario.method,
            path=scenario.path,
            headers=scenario.headers,
            body=test_payload,
            query_params={'request_id': str(request_id)}
        )
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        if 'error' in response:
            raise Exception(f"Bridge request failed: {response['error']}")
        
        return latency_ms
    
    async def _test_rest_performance(self, scenario: ComparisonScenario, 
                                   test_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test traditional REST API performance."""
        
        latencies = []
        successes = 0
        failures = 0
        
        resource_monitor = ResourceMonitor()
        await resource_monitor.start_monitoring()
        
        start_time = time.perf_counter()
        
        try:
            # Create semaphore to control concurrency
            semaphore = asyncio.Semaphore(scenario.concurrent_requests)
            
            async def rest_request(request_id: int):
                async with semaphore:
                    try:
                        request_start = time.perf_counter()
                        
                        # Simulate REST API call
                        response = await self.rest_server.handle_request({
                            **test_payload,
                            'request_id': request_id
                        })
                        
                        latency_ms = (time.perf_counter() - request_start) * 1000
                        return latency_ms
                        
                    except Exception as e:
                        raise e
            
            # Execute all requests
            tasks = [rest_request(i) for i in range(scenario.request_count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    failures += 1
                else:
                    successes += 1
                    latencies.append(result)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            resource_stats = resource_monitor.get_resource_stats()
            
            return self._calculate_performance_stats(
                "Traditional REST", latencies, successes, failures, duration, resource_stats
            )
            
        finally:
            await resource_monitor.stop_monitoring()
    
    async def _test_direct_performance(self, scenario: ComparisonScenario, 
                                     test_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test direct API performance (baseline)."""
        
        latencies = []
        successes = 0
        failures = 0
        
        resource_monitor = ResourceMonitor()
        await resource_monitor.start_monitoring()
        
        start_time = time.perf_counter()
        
        try:
            semaphore = asyncio.Semaphore(scenario.concurrent_requests)
            
            async def direct_request(request_id: int):
                async with semaphore:
                    try:
                        request_start = time.perf_counter()
                        
                        response = await self.direct_client.call_api({
                            **test_payload,
                            'request_id': request_id
                        })
                        
                        latency_ms = (time.perf_counter() - request_start) * 1000
                        return latency_ms
                        
                    except Exception as e:
                        raise e
            
            tasks = [direct_request(i) for i in range(scenario.request_count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    failures += 1
                else:
                    successes += 1
                    latencies.append(result)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            resource_stats = resource_monitor.get_resource_stats()
            
            return self._calculate_performance_stats(
                "Direct API", latencies, successes, failures, duration, resource_stats
            )
            
        finally:
            await resource_monitor.stop_monitoring()
    
    def _calculate_performance_stats(self, api_type: str, latencies: List[float], 
                                   successes: int, failures: int, duration: float,
                                   resource_stats: Dict[str, float]) -> Dict[str, Any]:
        """Calculate performance statistics."""
        
        if not latencies:
            return {
                'api_type': api_type,
                'total_requests': successes + failures,
                'successful_requests': successes,
                'failed_requests': failures,
                'success_rate': 0.0,
                'error': 'No successful requests'
            }
        
        latencies.sort()
        
        def percentile(data, p):
            index = int(len(data) * p / 100)
            return data[min(index, len(data) - 1)]
        
        return {
            'api_type': api_type,
            'total_requests': successes + failures,
            'successful_requests': successes,
            'failed_requests': failures,
            'success_rate': successes / (successes + failures),
            'duration_seconds': duration,
            'throughput_rps': successes / duration,
            'latency_stats': {
                'min_ms': min(latencies),
                'max_ms': max(latencies),
                'avg_ms': statistics.mean(latencies),
                'median_ms': statistics.median(latencies),
                'p95_ms': percentile(latencies, 95),
                'p99_ms': percentile(latencies, 99),
                'p99_9_ms': percentile(latencies, 99.9)
            },
            'resource_utilization': resource_stats
        }
    
    def _display_scenario_results(self, scenario_name: str, results: Dict[str, Any]):
        """Display comparison results for a scenario."""
        
        print(f"\n📊 Results for {scenario_name}:")
        
        # Safely extract latency stats with proper error handling
        try:
            bridge_stats = results.get('universal_api_bridge', {}).get('latency_stats', {})
            rest_stats = results.get('traditional_rest', {}).get('latency_stats', {})
            direct_stats = results.get('direct_api', {}).get('latency_stats', {})
            
            bridge_p99 = bridge_stats.get('p99', 0)
            rest_p99 = rest_stats.get('p99', 0)
            direct_p99 = direct_stats.get('p99', 0)
            
            print(f"\n   Latency Comparison (P99):")
            print(f"     🚀 Universal API Bridge: {bridge_p99:.2f}ms")
            print(f"     🌐 Traditional REST:     {rest_p99:.2f}ms")
            print(f"     ⚡ Direct API:          {direct_p99:.2f}ms")
            
            # Calculate improvements
            if rest_p99 > 0:
                bridge_vs_rest_improvement = ((rest_p99 - bridge_p99) / rest_p99) * 100
            else:
                bridge_vs_rest_improvement = 0
                
            if direct_p99 > 0:
                bridge_vs_direct_overhead = ((bridge_p99 - direct_p99) / direct_p99) * 100
            else:
                bridge_vs_direct_overhead = 0
        except Exception as e:
            print(f"   ❌ Error displaying results: {e}")
            print(f"   📊 Results structure: {results}")
            return
        
        print(f"\n   Performance Analysis:")
        if bridge_vs_rest_improvement > 0:
            print(f"     ✅ Bridge is {bridge_vs_rest_improvement:.1f}% FASTER than traditional REST")
        else:
            print(f"     ❌ Bridge is {abs(bridge_vs_rest_improvement):.1f}% slower than traditional REST")
        
        print(f"     📊 Bridge overhead vs direct: {bridge_vs_direct_overhead:.1f}%")
        
        # Throughput comparison
        bridge_rps = results.get('universal_api_bridge', {}).get('throughput_rps', 0)
        rest_rps = results.get('traditional_rest', {}).get('throughput_rps', 0)
        direct_rps = results.get('direct_api', {}).get('throughput_rps', 0)
        
        print(f"\n   Throughput Comparison:")
        print(f"     🚀 Universal API Bridge: {bridge_rps:.0f} RPS")
        print(f"     🌐 Traditional REST:     {rest_rps:.0f} RPS")
        print(f"     ⚡ Direct API:          {direct_rps:.0f} RPS")
        
        if rest_rps > 0:
            throughput_improvement = ((bridge_rps - rest_rps) / rest_rps) * 100
        else:
            throughput_improvement = 0
            
        if throughput_improvement > 0:
            print(f"     ✅ Bridge has {throughput_improvement:.1f}% HIGHER throughput")
        else:
            print(f"     ❌ Bridge has {abs(throughput_improvement):.1f}% lower throughput")
    
    def _generate_comparison_report(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive comparison report."""
        
        # Aggregate statistics across all scenarios
        bridge_latencies = []
        rest_latencies = []
        direct_latencies = []
        
        bridge_throughputs = []
        rest_throughputs = []
        
        for scenario_name, results in comparison_results.items():
            bridge_p99 = results['universal_api_bridge']['latency_stats']['p99_ms']
            rest_p99 = results['traditional_rest']['latency_stats']['p99_ms']
            direct_p99 = results['direct_api']['latency_stats']['p99_ms']
            
            bridge_latencies.append(bridge_p99)
            rest_latencies.append(rest_p99)
            direct_latencies.append(direct_p99)
            
            bridge_throughputs.append(results['universal_api_bridge']['throughput_rps'])
            rest_throughputs.append(results['traditional_rest']['throughput_rps'])
        
        # Calculate overall performance metrics
        avg_bridge_latency = statistics.mean(bridge_latencies)
        avg_rest_latency = statistics.mean(rest_latencies)
        avg_direct_latency = statistics.mean(direct_latencies)
        
        avg_bridge_throughput = statistics.mean(bridge_throughputs)
        avg_rest_throughput = statistics.mean(rest_throughputs)
        
        # Calculate improvements
        latency_improvement = ((avg_rest_latency - avg_bridge_latency) / avg_rest_latency) * 100
        throughput_improvement = ((avg_bridge_throughput - avg_rest_throughput) / avg_rest_throughput) * 100
        overhead_vs_direct = ((avg_bridge_latency - avg_direct_latency) / avg_direct_latency) * 100
        
        return {
            'summary': {
                'total_scenarios_tested': len(comparison_results),
                'avg_latency_improvement_vs_rest': latency_improvement,
                'avg_throughput_improvement_vs_rest': throughput_improvement,
                'avg_overhead_vs_direct': overhead_vs_direct
            },
            'detailed_results': comparison_results,
            'recommendations': self._generate_recommendations(latency_improvement, throughput_improvement, overhead_vs_direct)
        }
    
    def _generate_recommendations(self, latency_improvement: float, 
                                throughput_improvement: float, overhead: float) -> List[str]:
        """Generate recommendations based on benchmark results."""
        
        recommendations = []
        
        if latency_improvement > 20:
            recommendations.append("✅ Universal API Bridge shows EXCELLENT latency improvements over traditional REST")
        elif latency_improvement > 0:
            recommendations.append("✅ Universal API Bridge shows good latency improvements over traditional REST")
        else:
            recommendations.append("⚠️ Universal API Bridge latency needs optimization compared to traditional REST")
        
        if throughput_improvement > 50:
            recommendations.append("✅ Universal API Bridge demonstrates SUPERIOR throughput capabilities")
        elif throughput_improvement > 0:
            recommendations.append("✅ Universal API Bridge shows improved throughput over traditional REST")
        else:
            recommendations.append("⚠️ Universal API Bridge throughput could be improved")
        
        if overhead < 50:
            recommendations.append("✅ Universal API Bridge maintains reasonable overhead compared to direct API calls")
        else:
            recommendations.append("⚠️ Universal API Bridge has significant overhead - consider optimization")
        
        # Additional recommendations
        recommendations.extend([
            "🎯 Consider enabling all optimizations for maximum performance",
            "📊 Monitor P99 latency in production workloads",
            "⚡ Use hot path detection for critical endpoints",
            "🧮 Leverage mathematical optimization features for high-volume scenarios"
        ])
        
        return recommendations


async def main():
    """Run the gRPC vs REST comparison benchmark."""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    comparator = PerformanceComparator()
    
    try:
        results = await comparator.run_comparison_benchmark()
        
        print(f"\n🎉 gRPC vs REST COMPARISON COMPLETED!")
        print(f"\n📋 FINAL SUMMARY:")
        print(f"   • Scenarios tested: {results['summary']['total_scenarios_tested']}")
        print(f"   • Avg latency improvement: {results['summary']['avg_latency_improvement_vs_rest']:.1f}%")
        print(f"   • Avg throughput improvement: {results['summary']['avg_throughput_improvement_vs_rest']:.1f}%")
        print(f"   • Overhead vs direct API: {results['summary']['avg_overhead_vs_direct']:.1f}%")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"   {rec}")
        
        return results
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Comparison benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Comparison benchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 