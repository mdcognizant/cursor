#!/usr/bin/env python3
"""
Universal API Bridge v2.0 - Complete Testing Suite Runner

This is the main entry point for comprehensive testing of the Universal API Bridge.
It orchestrates all test suites and generates a complete performance analysis report.

Test Suites Included:
1. Comprehensive Performance Testing
2. gRPC vs REST Comparison 
3. Multi-API Integration Testing
4. Comprehensive Report Generation

Usage:
    python run_all_tests.py [--quick] [--report-only] [--verbose]
"""

import asyncio
import logging
import time
import argparse
import sys
import os
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from performance_test_suite import PerformanceTestSuite
from grpc_vs_rest_benchmark import PerformanceComparator
from multi_api_test_scenarios import MultiAPITestSuite
from performance_report_generator import PerformanceReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UniversalAPIBridgeTestRunner:
    """Complete test runner for Universal API Bridge v2.0."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.test_results = {}
        self.execution_times = {}
        
        # Test suite instances
        self.performance_suite = None
        self.grpc_comparator = None
        self.multi_api_suite = None
        self.report_generator = PerformanceReportGenerator()
        
        # Configuration options
        self.quick_mode = self.config.get('quick_mode', False)
        self.verbose = self.config.get('verbose', False)
        self.report_only = self.config.get('report_only', False)
        
        # Adjust logging level based on verbosity
        if self.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete Universal API Bridge test suite."""
        
        print("\n🚀 UNIVERSAL API BRIDGE v2.0 - COMPLETE TESTING SUITE")
        print("=" * 100)
        print(f"⚙️  Configuration: {'Quick Mode' if self.quick_mode else 'Full Testing'}")
        print(f"📝 Verbose Logging: {'Enabled' if self.verbose else 'Disabled'}")
        print(f"📋 Report Only: {'Yes' if self.report_only else 'No'}")
        print("=" * 100)
        
        overall_start_time = time.perf_counter()
        
        try:
            if not self.report_only:
                # Phase 1: Performance Testing Suite
                await self._run_performance_tests()
                
                # Phase 2: gRPC vs REST Comparison
                await self._run_grpc_vs_rest_comparison()
                
                # Phase 3: Multi-API Integration Testing
                await self._run_multi_api_tests()
            
            # Phase 4: Generate Comprehensive Report
            await self._generate_comprehensive_report()
            
            # Calculate total execution time
            total_time = time.perf_counter() - overall_start_time
            self.execution_times['total'] = total_time
            
            # Display final summary
            self._display_final_summary()
            
            return {
                'test_results': self.test_results,
                'execution_times': self.execution_times,
                'configuration': self.config,
                'success': True
            }
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Testing interrupted by user")
            return {'success': False, 'error': 'User interruption'}
            
        except Exception as e:
            logger.error(f"Testing suite failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    async def _run_performance_tests(self):
        """Run comprehensive performance testing."""
        
        print(f"\n📊 PHASE 1: COMPREHENSIVE PERFORMANCE TESTING")
        print("-" * 80)
        
        phase_start = time.perf_counter()
        
        try:
            self.performance_suite = PerformanceTestSuite()
            
            if self.quick_mode:
                # Reduce test scenarios for quick mode
                original_scenarios = self.performance_suite.test_scenarios
                self.performance_suite.test_scenarios = original_scenarios[:3]  # First 3 scenarios
                print("⚡ Quick mode: Running reduced test scenarios")
            
            # Run performance tests
            performance_results = await self.performance_suite.run_all_tests()
            
            self.test_results['performance_tests'] = performance_results
            self.execution_times['performance_tests'] = time.perf_counter() - phase_start
            
            # Quick analysis
            total_requests = sum(r.total_requests for r in performance_results)
            avg_success_rate = sum(r.success_rate for r in performance_results) / len(performance_results)
            avg_latency = sum(r.avg_latency_ms for r in performance_results) / len(performance_results)
            
            print(f"\n✅ Performance Testing Completed!")
            print(f"   • Scenarios: {len(performance_results)}")
            print(f"   • Total Requests: {total_requests:,}")
            print(f"   • Average Success Rate: {avg_success_rate*100:.1f}%")
            print(f"   • Average Latency: {avg_latency:.2f}ms")
            print(f"   • Execution Time: {self.execution_times['performance_tests']:.1f}s")
            
        except Exception as e:
            logger.error(f"Performance testing failed: {e}")
            self.test_results['performance_tests'] = {'error': str(e)}
            raise
    
    async def _run_grpc_vs_rest_comparison(self):
        """Run gRPC vs REST performance comparison."""
        
        print(f"\n⚔️  PHASE 2: gRPC vs REST PERFORMANCE COMPARISON")
        print("-" * 80)
        
        phase_start = time.perf_counter()
        
        try:
            self.grpc_comparator = PerformanceComparator()
            
            # Run comparison benchmark
            grpc_results = await self.grpc_comparator.run_comparison_benchmark()
            
            self.test_results['grpc_vs_rest'] = grpc_results
            self.execution_times['grpc_vs_rest'] = time.perf_counter() - phase_start
            
            # Quick analysis
            if 'summary' in grpc_results:
                summary = grpc_results['summary']
                latency_improvement = summary.get('avg_latency_improvement_vs_rest', 0)
                throughput_improvement = summary.get('avg_throughput_improvement_vs_rest', 0)
                
                print(f"\n✅ gRPC vs REST Comparison Completed!")
                print(f"   • Scenarios Tested: {summary.get('total_scenarios_tested', 0)}")
                print(f"   • Latency Improvement: {latency_improvement:+.1f}%")
                print(f"   • Throughput Improvement: {throughput_improvement:+.1f}%")
                print(f"   • Execution Time: {self.execution_times['grpc_vs_rest']:.1f}s")
                
                # Performance assessment
                if latency_improvement > 20:
                    print(f"   🟢 gRPC shows SIGNIFICANT performance advantage")
                elif latency_improvement > 0:
                    print(f"   🟡 gRPC shows moderate performance advantage")
                else:
                    print(f"   🔴 gRPC performance needs optimization")
            
        except Exception as e:
            logger.error(f"gRPC vs REST comparison failed: {e}")
            self.test_results['grpc_vs_rest'] = {'error': str(e)}
            raise
    
    async def _run_multi_api_tests(self):
        """Run multi-API integration testing."""
        
        print(f"\n🌐 PHASE 3: MULTI-API INTEGRATION TESTING")
        print("-" * 80)
        
        phase_start = time.perf_counter()
        
        try:
            self.multi_api_suite = MultiAPITestSuite()
            
            # Run multi-API tests
            api_results = await self.multi_api_suite.run_all_api_tests()
            
            self.test_results['multi_api_tests'] = api_results
            self.execution_times['multi_api_tests'] = time.perf_counter() - phase_start
            
            # Quick analysis
            if 'summary' in api_results:
                summary = api_results['summary']
                overall_success = summary.get('overall_success_rate', 0)
                total_requests = summary.get('total_requests_across_all_tests', 0)
                
                print(f"\n✅ Multi-API Integration Testing Completed!")
                print(f"   • Test Categories: {summary.get('total_test_categories', 0)}")
                print(f"   • Total Requests: {total_requests:,}")
                print(f"   • Overall Success Rate: {overall_success*100:.1f}%")
                print(f"   • Execution Time: {self.execution_times['multi_api_tests']:.1f}s")
                
                # Integration assessment
                if overall_success > 0.95:
                    print(f"   🟢 EXCELLENT multi-API compatibility")
                elif overall_success > 0.85:
                    print(f"   🟡 GOOD multi-API compatibility")
                else:
                    print(f"   🔴 Multi-API compatibility needs improvement")
            
        except Exception as e:
            logger.error(f"Multi-API testing failed: {e}")
            self.test_results['multi_api_tests'] = {'error': str(e)}
            raise
    
    async def _generate_comprehensive_report(self):
        """Generate comprehensive performance report."""
        
        print(f"\n📋 PHASE 4: COMPREHENSIVE REPORT GENERATION")
        print("-" * 80)
        
        phase_start = time.perf_counter()
        
        try:
            # Extract results for report generation
            performance_results = self.test_results.get('performance_tests', [])
            grpc_results = self.test_results.get('grpc_vs_rest', {})
            api_results = self.test_results.get('multi_api_tests', {})
            
            # Generate comprehensive report
            report_content = self.report_generator.generate_comprehensive_report(
                performance_results, grpc_results, api_results
            )
            
            # Save report to file
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            report_filename = f"universal_api_bridge_test_report_{timestamp}.md"
            
            saved_filename = self.report_generator.save_report_to_file(
                report_content, report_filename
            )
            
            self.test_results['report'] = {
                'content': report_content,
                'filename': saved_filename,
                'generated_at': timestamp
            }
            
            self.execution_times['report_generation'] = time.perf_counter() - phase_start
            
            print(f"\n✅ Comprehensive Report Generated!")
            print(f"   • Report File: {saved_filename}")
            print(f"   • Report Size: {len(report_content):,} characters")
            print(f"   • Generation Time: {self.execution_times['report_generation']:.1f}s")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            self.test_results['report'] = {'error': str(e)}
            raise
    
    def _display_final_summary(self):
        """Display final test suite summary."""
        
        print(f"\n🎉 UNIVERSAL API BRIDGE v2.0 - TESTING SUITE COMPLETED!")
        print("=" * 100)
        
        # Execution time summary
        print(f"\n⏱️  EXECUTION TIME SUMMARY:")
        total_time = self.execution_times.get('total', 0)
        
        for phase, duration in self.execution_times.items():
            if phase != 'total':
                percentage = (duration / total_time) * 100 if total_time > 0 else 0
                print(f"   • {phase.replace('_', ' ').title()}: {duration:.1f}s ({percentage:.1f}%)")
        
        print(f"   • Total Execution Time: {total_time:.1f}s")
        
        # Test results summary
        print(f"\n📊 TEST RESULTS SUMMARY:")
        
        # Performance tests summary
        if 'performance_tests' in self.test_results and not isinstance(self.test_results['performance_tests'], dict):
            perf_results = self.test_results['performance_tests']
            total_perf_requests = sum(r.total_requests for r in perf_results)
            avg_success_rate = sum(r.success_rate for r in perf_results) / len(perf_results)
            print(f"   • Performance Tests: {len(perf_results)} scenarios, {total_perf_requests:,} requests, {avg_success_rate*100:.1f}% success")
        
        # gRPC comparison summary
        if 'grpc_vs_rest' in self.test_results and 'summary' in self.test_results['grpc_vs_rest']:
            grpc_summary = self.test_results['grpc_vs_rest']['summary']
            improvement = grpc_summary.get('avg_latency_improvement_vs_rest', 0)
            print(f"   • gRPC vs REST: {improvement:+.1f}% latency improvement")
        
        # Multi-API summary
        if 'multi_api_tests' in self.test_results and 'summary' in self.test_results['multi_api_tests']:
            api_summary = self.test_results['multi_api_tests']['summary']
            api_success = api_summary.get('overall_success_rate', 0)
            api_requests = api_summary.get('total_requests_across_all_tests', 0)
            print(f"   • Multi-API Tests: {api_requests:,} requests, {api_success*100:.1f}% success")
        
        # Report summary
        if 'report' in self.test_results and 'filename' in self.test_results['report']:
            report_file = self.test_results['report']['filename']
            print(f"   • Comprehensive Report: {report_file}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        
        # Calculate overall performance score
        performance_score = 0
        total_components = 0
        
        # Performance test score
        if 'performance_tests' in self.test_results and not isinstance(self.test_results['performance_tests'], dict):
            perf_results = self.test_results['performance_tests']
            avg_success = sum(r.success_rate for r in perf_results) / len(perf_results)
            performance_score += avg_success * 30  # 30% weight
            total_components += 30
        
        # gRPC improvement score
        if 'grpc_vs_rest' in self.test_results and 'summary' in self.test_results['grpc_vs_rest']:
            improvement = self.test_results['grpc_vs_rest']['summary'].get('avg_latency_improvement_vs_rest', 0)
            grpc_score = min(100, max(0, improvement + 50)) / 100  # Normalize around 50% improvement
            performance_score += grpc_score * 35  # 35% weight
            total_components += 35
        
        # Multi-API score
        if 'multi_api_tests' in self.test_results and 'summary' in self.test_results['multi_api_tests']:
            api_success = self.test_results['multi_api_tests']['summary'].get('overall_success_rate', 0)
            performance_score += api_success * 35  # 35% weight
            total_components += 35
        
        # Calculate final score
        if total_components > 0:
            final_score = performance_score / total_components * 100
            
            if final_score >= 90:
                assessment = "🟢 EXCELLENT - Production Ready"
                grade = "A"
            elif final_score >= 80:
                assessment = "🟡 GOOD - Minor optimizations recommended"
                grade = "B"
            elif final_score >= 70:
                assessment = "🟠 SATISFACTORY - Optimization needed"
                grade = "C"
            else:
                assessment = "🔴 NEEDS IMPROVEMENT - Significant work required"
                grade = "D"
            
            print(f"   • Performance Score: {final_score:.1f}/100 (Grade: {grade})")
            print(f"   • Assessment: {assessment}")
        
        # Next steps
        print(f"\n📋 NEXT STEPS:")
        print(f"   1. 📖 Review the comprehensive performance report")
        print(f"   2. 🔧 Implement recommended optimizations")
        print(f"   3. 📊 Set up production monitoring")
        print(f"   4. 🚀 Plan production deployment strategy")
        
        print(f"\n💡 The Universal API Bridge v2.0 testing is now complete!")
        print(f"   Thank you for using the comprehensive testing suite! 🎯")


def parse_arguments():
    """Parse command line arguments."""
    
    parser = argparse.ArgumentParser(
        description="Universal API Bridge v2.0 - Complete Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run full testing suite
  python run_all_tests.py --quick            # Run quick testing (reduced scenarios)
  python run_all_tests.py --verbose          # Run with detailed logging
  python run_all_tests.py --report-only      # Generate report only (skip tests)
        """
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick testing with reduced scenarios'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging and detailed output'
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report only, skip running tests'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for reports (default: current directory)'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the testing suite."""
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Create configuration
    config = {
        'quick_mode': args.quick,
        'verbose': args.verbose,
        'report_only': args.report_only,
        'output_dir': args.output_dir
    }
    
    # Create and run test suite
    test_runner = UniversalAPIBridgeTestRunner(config)
    
    try:
        results = await test_runner.run_complete_test_suite()
        
        if results['success']:
            print(f"\n🎊 ALL TESTING COMPLETED SUCCESSFULLY! 🎊")
            sys.exit(0)
        else:
            print(f"\n❌ Testing failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Testing interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the complete testing suite
    asyncio.run(main()) 