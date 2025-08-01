#!/usr/bin/env python3
"""
Multi-API Test Scenarios for Universal API Bridge

This module tests the bridge with various API patterns and integrations:
- News APIs (NewsData.io, Currents, NewsAPI.org)
- REST API patterns (CRUD operations, search, filtering)
- Different payload sizes and complexities
- Real-world usage scenarios
- Error handling and resilience testing
"""

import asyncio
import time
import logging
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bridge import UniversalAPIBridge
from config import UnifiedBridgeConfig
from performance_test_suite import PerformanceMetrics, ResourceMonitor

logger = logging.getLogger(__name__)

@dataclass
class APITestScenario:
    """Defines a specific API testing scenario."""
    
    name: str
    description: str
    api_type: str  # 'news', 'crud', 'search', 'file', 'analytics'
    endpoint_pattern: str
    request_variations: List[Dict[str, Any]]
    expected_behavior: Dict[str, Any]
    load_profile: Dict[str, int]  # concurrent_users, requests_per_user


class NewsAPITester:
    """Test news API integrations through the bridge."""
    
    def __init__(self, bridge: UniversalAPIBridge):
        self.bridge = bridge
        self.news_sources = ['newsdata', 'currents', 'newsapi']
        
    async def test_news_api_scenarios(self) -> Dict[str, Any]:
        """Test various news API scenarios."""
        
        scenarios = [
            {
                'name': 'Latest News Retrieval',
                'requests': [
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/latest',
                        'query_params': {'source': 'newsdata', 'limit': '10'},
                        'description': 'Get latest news from NewsData.io'
                    },
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/latest',
                        'query_params': {'source': 'currents', 'limit': '15'},
                        'description': 'Get latest news from Currents API'
                    },
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/latest',
                        'query_params': {'source': 'newsapi', 'limit': '20'},
                        'description': 'Get latest news from NewsAPI.org'
                    }
                ]
            },
            {
                'name': 'News Search Functionality',
                'requests': [
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/search',
                        'query_params': {'source': 'newsdata', 'q': 'technology', 'limit': '5'},
                        'description': 'Search technology news'
                    },
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/search',
                        'query_params': {'source': 'currents', 'q': 'business', 'category': 'business'},
                        'description': 'Search business news with category filter'
                    },
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/search',
                        'query_params': {'source': 'newsapi', 'q': 'science', 'sortBy': 'popularity'},
                        'description': 'Search science news sorted by popularity'
                    }
                ]
            },
            {
                'name': 'Category-based News',
                'requests': [
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/category/business',
                        'query_params': {'source': 'newsdata', 'limit': '8'},
                        'description': 'Get business category news'
                    },
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/category/technology',
                        'query_params': {'source': 'currents', 'country': 'us'},
                        'description': 'Get US technology news'
                    },
                    {
                        'method': 'GET',
                        'path': '/api/v1/news/category/sports',
                        'query_params': {'source': 'newsapi', 'language': 'en'},
                        'description': 'Get English sports news'
                    }
                ]
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            print(f"\n📰 Testing News API Scenario: {scenario['name']}")
            
            scenario_results = {
                'requests_tested': len(scenario['requests']),
                'request_results': [],
                'performance_summary': {}
            }
            
            latencies = []
            successes = 0
            
            for request_config in scenario['requests']:
                print(f"   📋 {request_config['description']}")
                
                start_time = time.perf_counter()
                
                try:
                    response = await self.bridge.process_request(**request_config)
                    
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    latencies.append(latency_ms)
                    
                    success = 'error' not in response
                    if success:
                        successes += 1
                    
                    # Analyze response
                    analysis = self._analyze_news_response(response, request_config)
                    
                    scenario_results['request_results'].append({
                        'request': request_config['description'],
                        'success': success,
                        'latency_ms': latency_ms,
                        'analysis': analysis
                    })
                    
                    status = "✅" if success else "❌"
                    print(f"     {status} Latency: {latency_ms:.1f}ms, Success: {success}")
                    
                except Exception as e:
                    print(f"     ❌ Error: {e}")
                    scenario_results['request_results'].append({
                        'request': request_config['description'],
                        'success': False,
                        'error': str(e)
                    })
            
            # Calculate scenario performance summary
            if latencies:
                scenario_results['performance_summary'] = {
                    'avg_latency_ms': sum(latencies) / len(latencies),
                    'min_latency_ms': min(latencies),
                    'max_latency_ms': max(latencies),
                    'success_rate': successes / len(scenario['requests']),
                    'total_requests': len(scenario['requests'])
                }
            
            results[scenario['name']] = scenario_results
        
        return results
    
    def _analyze_news_response(self, response: Dict[str, Any], 
                             request_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze news API response for quality and correctness."""
        
        analysis = {
            'response_received': True,
            'has_data': 'data' in response,
            'has_performance_metrics': False,
            'routing_successful': False,
            'bridge_features_active': []
        }
        
        # Check for bridge performance metadata
        if '_bridge_metadata' in response:
            analysis['has_performance_metrics'] = True
            bridge_meta = response['_bridge_metadata']
            analysis['processing_time_us'] = bridge_meta.get('processing_time_us', 0)
            analysis['optimization_level'] = bridge_meta.get('optimization_level', 'unknown')
        
        # Check gateway routing
        if '_gateway_performance' in response:
            analysis['routing_successful'] = True
            gw_perf = response['_gateway_performance']
            analysis['service_routed_to'] = gw_perf.get('service_name', 'unknown')
            analysis['pattern_matched'] = gw_perf.get('pattern_matched', False)
        
        # Check for active optimizations
        if '_grpc_performance' in response:
            grpc_perf = response['_grpc_performance']
            if grpc_perf.get('is_hot_path', False):
                analysis['bridge_features_active'].append('hot_path')
            
            optimizations = grpc_perf.get('optimizations_applied', [])
            analysis['bridge_features_active'].extend(optimizations)
        
        # Check MCP layer performance
        if '_mcp_performance' in response:
            mcp_perf = response['_mcp_performance']
            analysis['mcp_latency_us'] = mcp_perf.get('total_latency_us', 0)
            analysis['load_balancing_active'] = 'selected_instance' in mcp_perf
        
        return analysis


class CRUDAPITester:
    """Test CRUD operations through the bridge."""
    
    def __init__(self, bridge: UniversalAPIBridge):
        self.bridge = bridge
        
    async def test_crud_operations(self) -> Dict[str, Any]:
        """Test various CRUD operation patterns."""
        
        crud_scenarios = [
            {
                'name': 'User Management CRUD',
                'base_path': '/api/v1/users',
                'operations': [
                    {
                        'operation': 'CREATE',
                        'method': 'POST',
                        'path': '/api/v1/users',
                        'body': {
                            'name': 'John Doe',
                            'email': 'john@example.com',
                            'role': 'user'
                        }
                    },
                    {
                        'operation': 'READ_LIST',
                        'method': 'GET',
                        'path': '/api/v1/users',
                        'query_params': {'limit': '10', 'offset': '0'}
                    },
                    {
                        'operation': 'READ_SINGLE',
                        'method': 'GET',
                        'path': '/api/v1/users/123',
                        'query_params': {}
                    },
                    {
                        'operation': 'UPDATE',
                        'method': 'PUT',
                        'path': '/api/v1/users/123',
                        'body': {
                            'name': 'John Smith',
                            'email': 'john.smith@example.com'
                        }
                    },
                    {
                        'operation': 'PARTIAL_UPDATE',
                        'method': 'PATCH',
                        'path': '/api/v1/users/123',
                        'body': {'last_login': '2025-01-01T00:00:00Z'}
                    },
                    {
                        'operation': 'DELETE',
                        'method': 'DELETE',
                        'path': '/api/v1/users/123',
                        'query_params': {}
                    }
                ]
            },
            {
                'name': 'Product Catalog CRUD',
                'base_path': '/api/v1/products',
                'operations': [
                    {
                        'operation': 'CREATE_PRODUCT',
                        'method': 'POST',
                        'path': '/api/v1/products',
                        'body': {
                            'name': 'Laptop Pro',
                            'category': 'electronics',
                            'price': 1299.99,
                            'specifications': {
                                'cpu': 'Intel i7',
                                'ram': '16GB',
                                'storage': '512GB SSD'
                            },
                            'tags': ['laptop', 'professional', 'high-performance']
                        }
                    },
                    {
                        'operation': 'SEARCH_PRODUCTS',
                        'method': 'GET',
                        'path': '/api/v1/products/search',
                        'query_params': {
                            'q': 'laptop',
                            'category': 'electronics',
                            'min_price': '1000',
                            'max_price': '2000'
                        }
                    },
                    {
                        'operation': 'GET_PRODUCT_DETAILS',
                        'method': 'GET',
                        'path': '/api/v1/products/prod-123',
                        'query_params': {'include': 'specifications,reviews'}
                    },
                    {
                        'operation': 'UPDATE_INVENTORY',
                        'method': 'PATCH',
                        'path': '/api/v1/products/prod-123/inventory',
                        'body': {'quantity': 50, 'location': 'warehouse-A'}
                    }
                ]
            }
        ]
        
        results = {}
        
        for scenario in crud_scenarios:
            print(f"\n🔧 Testing CRUD Scenario: {scenario['name']}")
            
            scenario_results = await self._execute_crud_scenario(scenario)
            results[scenario['name']] = scenario_results
        
        return results
    
    async def _execute_crud_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CRUD scenario and measure performance."""
        
        operation_results = []
        latencies = []
        successes = 0
        
        for operation in scenario['operations']:
            print(f"   📋 Testing {operation['operation']}")
            
            start_time = time.perf_counter()
            
            try:
                # Prepare request
                request_params = {
                    'method': operation['method'],
                    'path': operation['path'],
                    'headers': {'Content-Type': 'application/json'}
                }
                
                if 'body' in operation:
                    request_params['body'] = operation['body']
                
                if 'query_params' in operation:
                    request_params['query_params'] = operation['query_params']
                
                # Execute request
                response = await self.bridge.process_request(**request_params)
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                latencies.append(latency_ms)
                
                success = 'error' not in response
                if success:
                    successes += 1
                
                # Analyze operation-specific behavior
                operation_analysis = self._analyze_crud_operation(operation, response)
                
                operation_results.append({
                    'operation': operation['operation'],
                    'method': operation['method'],
                    'path': operation['path'],
                    'success': success,
                    'latency_ms': latency_ms,
                    'analysis': operation_analysis
                })
                
                status = "✅" if success else "❌"
                print(f"     {status} {operation['method']} {operation['path']} - {latency_ms:.1f}ms")
                
            except Exception as e:
                print(f"     ❌ {operation['operation']} failed: {e}")
                operation_results.append({
                    'operation': operation['operation'],
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'scenario_name': scenario['name'],
            'total_operations': len(scenario['operations']),
            'successful_operations': successes,
            'operation_results': operation_results,
            'performance_summary': {
                'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
                'success_rate': successes / len(scenario['operations']),
                'total_latency_ms': sum(latencies)
            }
        }
    
    def _analyze_crud_operation(self, operation: Dict[str, Any], 
                              response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CRUD operation response."""
        
        analysis = {
            'operation_type': operation['operation'],
            'response_appropriate': False,
            'bridge_routing': False,
            'optimization_applied': False
        }
        
        # Check if response is appropriate for operation type
        if operation['operation'] in ['CREATE', 'UPDATE', 'PARTIAL_UPDATE']:
            # Should have data or confirmation
            analysis['response_appropriate'] = 'data' in response or 'status' in response
        elif operation['operation'] in ['READ_LIST', 'READ_SINGLE', 'SEARCH_PRODUCTS']:
            # Should have data
            analysis['response_appropriate'] = 'data' in response
        elif operation['operation'] == 'DELETE':
            # Should have status confirmation
            analysis['response_appropriate'] = 'status' in response or 'error' not in response
        
        # Check bridge routing
        if '_gateway_performance' in response:
            analysis['bridge_routing'] = True
            gw_perf = response['_gateway_performance']
            analysis['service_name'] = gw_perf.get('service_name', 'unknown')
            analysis['pattern_matched'] = gw_perf.get('pattern_matched', False)
        
        # Check optimizations
        if '_grpc_performance' in response:
            grpc_perf = response['_grpc_performance']
            analysis['optimization_applied'] = len(grpc_perf.get('optimizations_applied', [])) > 0
            analysis['is_hot_path'] = grpc_perf.get('is_hot_path', False)
        
        return analysis


class LoadTestingScenarios:
    """Advanced load testing scenarios for the bridge."""
    
    def __init__(self, bridge: UniversalAPIBridge):
        self.bridge = bridge
        
    async def run_load_scenarios(self) -> Dict[str, Any]:
        """Run various load testing scenarios."""
        
        scenarios = [
            {
                'name': 'Burst Load Test',
                'description': 'Sudden spike in traffic',
                'pattern': 'burst',
                'duration_seconds': 30,
                'concurrent_users': [1, 5, 20, 50, 20, 5, 1],  # Burst pattern
                'requests_per_second': 100
            },
            {
                'name': 'Sustained High Load',
                'description': 'Continuous high traffic',
                'pattern': 'sustained',
                'duration_seconds': 60,
                'concurrent_users': [50] * 12,  # 60 seconds / 5 second intervals
                'requests_per_second': 200
            },
            {
                'name': 'Gradual Ramp Up',
                'description': 'Gradual increase in load',
                'pattern': 'ramp',
                'duration_seconds': 45,
                'concurrent_users': [5, 10, 15, 25, 35, 50, 75, 100, 75],  # Ramp up then down
                'requests_per_second': 150
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            print(f"\n⚡ Running Load Scenario: {scenario['name']}")
            print(f"   {scenario['description']}")
            
            scenario_results = await self._execute_load_scenario(scenario)
            results[scenario['name']] = scenario_results
        
        return results
    
    async def _execute_load_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a load testing scenario."""
        
        all_results = []
        resource_monitor = ResourceMonitor()
        await resource_monitor.start_monitoring()
        
        start_time = time.perf_counter()
        
        try:
            interval_duration = scenario['duration_seconds'] / len(scenario['concurrent_users'])
            
            for i, user_count in enumerate(scenario['concurrent_users']):
                print(f"   📊 Phase {i+1}: {user_count} concurrent users")
                
                # Generate requests for this phase
                phase_tasks = []
                for user_id in range(user_count):
                    task = asyncio.create_task(
                        self._simulate_load_user(user_id, interval_duration)
                    )
                    phase_tasks.append(task)
                
                # Wait for phase to complete
                phase_results = await asyncio.gather(*phase_tasks, return_exceptions=True)
                
                # Collect results
                for result in phase_results:
                    if not isinstance(result, Exception):
                        all_results.extend(result)
                
                # Brief pause between phases
                if i < len(scenario['concurrent_users']) - 1:
                    await asyncio.sleep(0.5)
            
            end_time = time.perf_counter()
            
            # Analyze results
            resource_stats = resource_monitor.get_resource_stats()
            
            return self._analyze_load_results(scenario, all_results, 
                                            end_time - start_time, resource_stats)
            
        finally:
            await resource_monitor.stop_monitoring()
    
    async def _simulate_load_user(self, user_id: int, duration: float) -> List[Dict[str, Any]]:
        """Simulate a single user during load test."""
        
        user_results = []
        end_time = time.perf_counter() + duration
        request_count = 0
        
        while time.perf_counter() < end_time:
            request_count += 1
            
            # Vary request types
            request_patterns = [
                {
                    'method': 'GET',
                    'path': f'/api/v1/load/test/{user_id}',
                    'query_params': {'request': str(request_count)}
                },
                {
                    'method': 'POST',
                    'path': '/api/v1/load/data',
                    'body': {
                        'user_id': user_id,
                        'request_id': request_count,
                        'data': [random.randint(1, 100) for _ in range(10)]
                    }
                },
                {
                    'method': 'PUT',
                    'path': f'/api/v1/load/update/{user_id}',
                    'body': {'timestamp': time.time(), 'value': random.random()}
                }
            ]
            
            pattern = random.choice(request_patterns)
            
            start_time = time.perf_counter()
            
            try:
                response = await self.bridge.process_request(**pattern)
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                success = 'error' not in response
                
                user_results.append({
                    'user_id': user_id,
                    'request_id': request_count,
                    'latency_ms': latency_ms,
                    'success': success,
                    'timestamp': time.perf_counter()
                })
                
            except Exception as e:
                user_results.append({
                    'user_id': user_id,
                    'request_id': request_count,
                    'success': False,
                    'error': str(e),
                    'timestamp': time.perf_counter()
                })
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)
        
        return user_results
    
    def _analyze_load_results(self, scenario: Dict[str, Any], results: List[Dict[str, Any]],
                            duration: float, resource_stats: Dict[str, float]) -> Dict[str, Any]:
        """Analyze load test results."""
        
        if not results:
            return {'error': 'No results to analyze'}
        
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', True)]
        
        latencies = [r['latency_ms'] for r in successful_results if 'latency_ms' in r]
        
        analysis = {
            'scenario_name': scenario['name'],
            'total_requests': len(results),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'success_rate': len(successful_results) / len(results) if results else 0,
            'duration_seconds': duration,
            'throughput_rps': len(successful_results) / duration if duration > 0 else 0,
            'resource_utilization': resource_stats
        }
        
        if latencies:
            latencies.sort()
            analysis['latency_stats'] = {
                'min_ms': min(latencies),
                'max_ms': max(latencies),
                'avg_ms': sum(latencies) / len(latencies),
                'p95_ms': latencies[int(len(latencies) * 0.95)],
                'p99_ms': latencies[int(len(latencies) * 0.99)]
            }
        
        return analysis


class MultiAPITestSuite:
    """Comprehensive multi-API testing suite."""
    
    def __init__(self):
        self.bridge = None
        self.test_results = {}
        
    async def run_all_api_tests(self) -> Dict[str, Any]:
        """Run comprehensive multi-API testing."""
        
        print("\n🌐 MULTI-API TESTING SUITE - Universal API Bridge v2.0")
        print("=" * 80)
        
        try:
            # Initialize bridge
            await self._initialize_bridge()
            
            # Test 1: News API Integration
            print("\n📰 Phase 1: News API Integration Testing")
            news_tester = NewsAPITester(self.bridge)
            self.test_results['news_apis'] = await news_tester.test_news_api_scenarios()
            
            # Test 2: CRUD Operations
            print("\n🔧 Phase 2: CRUD Operations Testing")
            crud_tester = CRUDAPITester(self.bridge)
            self.test_results['crud_operations'] = await crud_tester.test_crud_operations()
            
            # Test 3: Load Testing Scenarios
            print("\n⚡ Phase 3: Load Testing Scenarios")
            load_tester = LoadTestingScenarios(self.bridge)
            self.test_results['load_scenarios'] = await load_tester.run_load_scenarios()
            
            # Generate comprehensive summary
            summary = self._generate_test_summary()
            self.test_results['summary'] = summary
            
            print(f"\n✅ Multi-API testing completed successfully!")
            self._display_final_summary(summary)
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Multi-API testing failed: {e}")
            raise
        finally:
            if self.bridge:
                await self.bridge.stop()
    
    async def _initialize_bridge(self):
        """Initialize bridge for testing."""
        
        config = UnifiedBridgeConfig.create_ultra_high_performance()
        self.bridge = UniversalAPIBridge(config)
        
        # Start bridge in test mode
        self.bridge.is_running = True
        self.bridge.start_time = time.time()
        await self.bridge.monitor.start_monitoring()
        
        print("✅ Universal API Bridge initialized for multi-API testing")
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        
        summary = {
            'total_test_categories': len(self.test_results),
            'test_categories': list(self.test_results.keys()),
            'overall_success_rate': 0.0,
            'performance_highlights': [],
            'issues_identified': [],
            'recommendations': []
        }
        
        # Analyze news API results
        if 'news_apis' in self.test_results:
            news_results = self.test_results['news_apis']
            total_news_requests = sum(
                result['requests_tested'] for result in news_results.values()
            )
            successful_news = sum(
                len([r for r in result['request_results'] if r.get('success', False)])
                for result in news_results.values()
            )
            
            summary['news_api_summary'] = {
                'total_requests': total_news_requests,
                'successful_requests': successful_news,
                'success_rate': successful_news / total_news_requests if total_news_requests > 0 else 0
            }
        
        # Analyze CRUD results
        if 'crud_operations' in self.test_results:
            crud_results = self.test_results['crud_operations']
            total_crud_operations = sum(
                result['total_operations'] for result in crud_results.values()
            )
            successful_crud = sum(
                result['successful_operations'] for result in crud_results.values()
            )
            
            summary['crud_summary'] = {
                'total_operations': total_crud_operations,
                'successful_operations': successful_crud,
                'success_rate': successful_crud / total_crud_operations if total_crud_operations > 0 else 0
            }
        
        # Analyze load test results
        if 'load_scenarios' in self.test_results:
            load_results = self.test_results['load_scenarios']
            
            total_load_requests = sum(
                result.get('total_requests', 0) for result in load_results.values()
            )
            successful_load = sum(
                result.get('successful_requests', 0) for result in load_results.values()
            )
            
            summary['load_test_summary'] = {
                'total_requests': total_load_requests,
                'successful_requests': successful_load,
                'success_rate': successful_load / total_load_requests if total_load_requests > 0 else 0
            }
        
        # Calculate overall success rate
        total_all_requests = sum([
            summary.get('news_api_summary', {}).get('total_requests', 0),
            summary.get('crud_summary', {}).get('total_operations', 0),
            summary.get('load_test_summary', {}).get('total_requests', 0)
        ])
        
        total_successful = sum([
            summary.get('news_api_summary', {}).get('successful_requests', 0),
            summary.get('crud_summary', {}).get('successful_operations', 0),
            summary.get('load_test_summary', {}).get('successful_requests', 0)
        ])
        
        summary['overall_success_rate'] = total_successful / total_all_requests if total_all_requests > 0 else 0
        summary['total_requests_across_all_tests'] = total_all_requests
        summary['total_successful_across_all_tests'] = total_successful
        
        # Generate recommendations
        summary['recommendations'] = self._generate_recommendations(summary)
        
        return summary
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        
        recommendations = []
        
        if summary['overall_success_rate'] > 0.95:
            recommendations.append("✅ Excellent overall performance across all API types")
        elif summary['overall_success_rate'] > 0.85:
            recommendations.append("✅ Good overall performance with minor optimization opportunities")
        else:
            recommendations.append("⚠️ Performance issues detected, optimization recommended")
        
        # Specific recommendations based on test results
        if 'news_api_summary' in summary:
            news_rate = summary['news_api_summary']['success_rate']
            if news_rate < 0.9:
                recommendations.append("📰 News API integration needs attention")
        
        if 'crud_summary' in summary:
            crud_rate = summary['crud_summary']['success_rate']
            if crud_rate < 0.9:
                recommendations.append("🔧 CRUD operations performance could be improved")
        
        if 'load_test_summary' in summary:
            load_rate = summary['load_test_summary']['success_rate']
            if load_rate < 0.8:
                recommendations.append("⚡ Consider load testing optimization")
        
        recommendations.extend([
            "🎯 Monitor P99 latency for production readiness",
            "📊 Enable all optimizations for maximum performance",
            "🔍 Implement comprehensive monitoring in production"
        ])
        
        return recommendations
    
    def _display_final_summary(self, summary: Dict[str, Any]):
        """Display final test summary."""
        
        print(f"\n📊 MULTI-API TESTING SUMMARY:")
        print(f"   • Test Categories: {summary['total_test_categories']}")
        print(f"   • Total Requests: {summary['total_requests_across_all_tests']:,}")
        print(f"   • Successful Requests: {summary['total_successful_across_all_tests']:,}")
        print(f"   • Overall Success Rate: {summary['overall_success_rate']*100:.1f}%")
        
        if 'news_api_summary' in summary:
            news = summary['news_api_summary']
            print(f"   • News API Success Rate: {news['success_rate']*100:.1f}%")
        
        if 'crud_summary' in summary:
            crud = summary['crud_summary']
            print(f"   • CRUD Operations Success Rate: {crud['success_rate']*100:.1f}%")
        
        if 'load_test_summary' in summary:
            load = summary['load_test_summary']
            print(f"   • Load Test Success Rate: {load['success_rate']*100:.1f}%")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in summary['recommendations']:
            print(f"   {rec}")


async def main():
    """Run the multi-API testing suite."""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_suite = MultiAPITestSuite()
    
    try:
        results = await test_suite.run_all_api_tests()
        
        print(f"\n🎉 MULTI-API TESTING COMPLETED SUCCESSFULLY!")
        
        return results
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Multi-API testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Multi-API testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 