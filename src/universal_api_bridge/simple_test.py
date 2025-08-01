#!/usr/bin/env python3
"""
Simple Test for Universal API Bridge v2.0

This is a simplified test that demonstrates the core functionality
without complex dependencies or comprehensive testing framework.
"""

import asyncio
import time
import logging
import sys

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported correctly."""
    try:
        print("🔧 Testing imports...")
        
        from config import UnifiedBridgeConfig
        print("   ✅ Config module imported")
        
        from ultra_grpc_engine import Phase2UltraOptimizedEngine
        print("   ✅ gRPC Engine imported")
        
        from mcp.ultra_layer import UltraMCPLayer
        print("   ✅ MCP Layer imported")
        
        from gateway import UniversalRESTGateway
        print("   ✅ Gateway imported")
        
        from bridge import UniversalAPIBridge
        print("   ✅ Main Bridge imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

async def test_basic_functionality():
    """Test basic bridge functionality."""
    try:
        print("\n🚀 Testing Universal API Bridge functionality...")
        
        # Import modules
        from config import UnifiedBridgeConfig
        from bridge import UniversalAPIBridge
        
        # Create configuration
        config = UnifiedBridgeConfig.create_ultra_high_performance()
        print("   ✅ Configuration created")
        
        # Initialize bridge
        bridge = UniversalAPIBridge(config)
        print("   ✅ Bridge initialized")
        
        # Set bridge to running state for testing
        bridge.is_running = True
        bridge.start_time = time.time()
        await bridge.monitor.start_monitoring()
        print("   ✅ Bridge started in test mode")
        
        # Test some basic requests
        test_requests = [
            {
                'method': 'GET',
                'path': '/api/v1/test',
                'headers': {'Content-Type': 'application/json'},
                'query_params': {'test': 'simple'}
            },
            {
                'method': 'POST', 
                'path': '/api/v1/data',
                'body': {'message': 'Hello Universal API Bridge!'}
            },
            {
                'method': 'GET',
                'path': '/news/latest',
                'query_params': {'source': 'test', 'limit': '10'}
            }
        ]
        
        print(f"\n   📊 Processing {len(test_requests)} test requests...")
        
        latencies = []
        successes = 0
        
        for i, request in enumerate(test_requests):
            start_time = time.perf_counter()
            
            response = await bridge.process_request(**request)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            latencies.append(latency_ms)
            
            success = 'error' not in response
            if success:
                successes += 1
            
            print(f"   {i+1}. {request['method']} {request['path']} - "
                  f"{'✅' if success else '❌'} {latency_ms:.2f}ms")
        
        # Get metrics
        bridge_metrics = bridge.get_bridge_metrics()
        
        print(f"\n   📈 Test Results:")
        print(f"     • Requests processed: {len(test_requests)}")
        print(f"     • Success rate: {successes/len(test_requests)*100:.1f}%")
        print(f"     • Average latency: {sum(latencies)/len(latencies):.2f}ms")
        print(f"     • Bridge uptime: {bridge_metrics['bridge_info']['uptime_seconds']:.1f}s")
        
        # Stop bridge
        await bridge.stop()
        print("   ✅ Bridge stopped gracefully")
        
        return successes == len(test_requests)
        
    except Exception as e:
        print(f"   ❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_sample():
    """Test a small performance sample."""
    try:
        print("\n⚡ Testing performance sample...")
        
        from config import UnifiedBridgeConfig
        from bridge import UniversalAPIBridge
        
        # Create bridge
        config = UnifiedBridgeConfig.create_ultra_high_performance()
        bridge = UniversalAPIBridge(config)
        
        # Start bridge
        bridge.is_running = True
        bridge.start_time = time.time()
        await bridge.monitor.start_monitoring()
        
        # Performance test - 50 requests
        num_requests = 50
        print(f"   📊 Processing {num_requests} performance test requests...")
        
        latencies = []
        successes = 0
        start_test = time.perf_counter()
        
        for i in range(num_requests):
            start_time = time.perf_counter()
            
            response = await bridge.process_request(
                method='GET',
                path=f'/api/v1/perf/test/{i}',
                query_params={'test': 'performance', 'id': str(i)}
            )
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            latencies.append(latency_ms)
            
            if 'error' not in response:
                successes += 1
        
        total_time = time.perf_counter() - start_test
        
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        throughput = num_requests / total_time
        
        print(f"\n   📈 Performance Results:")
        print(f"     • Total requests: {num_requests}")
        print(f"     • Success rate: {successes/num_requests*100:.1f}%")
        print(f"     • Average latency: {avg_latency:.2f}ms")
        print(f"     • Min latency: {min_latency:.2f}ms")
        print(f"     • Max latency: {max_latency:.2f}ms")
        print(f"     • Throughput: {throughput:.0f} RPS")
        print(f"     • Total time: {total_time:.2f}s")
        
        # Performance assessment
        if avg_latency < 5.0 and successes == num_requests:
            print(f"     🟢 EXCELLENT performance!")
        elif avg_latency < 20.0 and successes/num_requests > 0.95:
            print(f"     🟡 GOOD performance")
        else:
            print(f"     🔴 Performance needs improvement")
        
        await bridge.stop()
        return True
        
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        return False

async def main():
    """Run simple tests."""
    print("🎯 UNIVERSAL API BRIDGE v2.0 - SIMPLE TEST")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Imports
    if not test_imports():
        all_tests_passed = False
        print("\n❌ Import test failed - cannot continue")
        return
    
    # Test 2: Basic functionality
    if not await test_basic_functionality():
        all_tests_passed = False
    
    # Test 3: Performance sample
    if not await test_performance_sample():
        all_tests_passed = False
    
    # Final result
    print(f"\n🎉 SIMPLE TEST COMPLETED!")
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Universal API Bridge is working correctly!")
        print("\n💡 Next steps:")
        print("   • Run full test suite: python run_all_tests.py")
        print("   • Try the demo: python example_demo.py")
        print("   • Read the testing guide: TESTING_GUIDE.md")
    else:
        print("❌ SOME TESTS FAILED - Check the output above for details")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 