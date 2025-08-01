#!/usr/bin/env python3
"""
Universal API Bridge Optimization with Shell Monitor Integration.

This script integrates the shell monitor addon to track and optimize the 
Universal API Bridge performance, ensuring no hangs or performance issues
during the optimization process.

FEATURES:
✅ Shell monitor integration for reliable command execution
✅ Timeout protection for long-running optimization tasks
✅ Performance tracking during code optimization
✅ Comprehensive diagnostics and monitoring
✅ Automated cleanup and recovery
✅ Real-time progress tracking
"""

import os
import sys
import time
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Add shell monitor to path
sys.path.append(str(Path(__file__).parent.parent / "Cursor" / "shellmonitor"))

try:
    from monitor import ShellMonitor, CommandResult
    from diagnostics import ShellDiagnostics
    MONITOR_AVAILABLE = True
except ImportError:
    print("⚠️  Shell monitor not available - using fallback mode")
    MONITOR_AVAILABLE = False

# Set environment for compatibility
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

@dataclass
class OptimizationTask:
    """Represents an optimization task with monitoring."""
    name: str
    command: str
    timeout: int = 120
    expected_duration: float = 10.0
    critical: bool = False
    completed: bool = False
    duration: float = 0.0
    success: bool = False
    output: str = ""
    error: str = ""

class MonitoredOptimizer:
    """Universal API Bridge optimizer with shell monitor integration."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.monitor = None
        self.diagnostics = None
        
        # Initialize shell monitor if available
        if MONITOR_AVAILABLE:
            self.monitor = ShellMonitor(
                timeout=300,  # 5 minute default timeout
                verbose=True,
                log_file=str(self.project_root / "optimization_monitor.log")
            )
            self.diagnostics = ShellDiagnostics()
            print("✅ Shell monitor initialized")
        else:
            print("⚠️  Shell monitor not available - using standard execution")
        
        # Optimization tasks queue
        self.tasks = self._define_optimization_tasks()
        self.results = {}
        
    def _define_optimization_tasks(self) -> List[OptimizationTask]:
        """Define the optimization tasks to be executed with monitoring."""
        return [
            # Dependency installation and setup
            OptimizationTask(
                name="install_core_dependencies",
                command="pip install fastapi uvicorn pydantic pydantic-settings python-dotenv click",
                timeout=180,
                expected_duration=30.0,
                critical=True
            ),
            OptimizationTask(
                name="install_security_deps",
                command="pip install cryptography pyjwt geoip2 maxminddb",
                timeout=120,
                expected_duration=20.0,
                critical=True
            ),
            OptimizationTask(
                name="install_distributed_deps", 
                command="pip install redis etcd3 python-consul kubernetes",
                timeout=180,
                expected_duration=40.0,
                critical=True
            ),
            OptimizationTask(
                name="install_monitoring_deps",
                command="pip install opentelemetry-api opentelemetry-sdk prometheus-client",
                timeout=120,
                expected_duration=25.0,
                critical=True
            ),
            OptimizationTask(
                name="install_performance_deps",
                command="pip install psutil memory-profiler locust circuitbreaker",
                timeout=120,
                expected_duration=20.0,
                critical=False
            ),
            OptimizationTask(
                name="install_testing_deps",
                command="pip install pytest pytest-asyncio pytest-mock pytest-cov",
                timeout=90,
                expected_duration=15.0,
                critical=True
            ),
            
            # Package installation
            OptimizationTask(
                name="install_package_editable",
                command="pip install -e .",
                timeout=60,
                expected_duration=10.0,
                critical=True
            ),
            
            # Code optimization and analysis
            OptimizationTask(
                name="run_performance_analysis",
                command="python performance_optimization.py",
                timeout=600,  # 10 minutes for comprehensive analysis
                expected_duration=120.0,
                critical=False
            ),
            
            # Testing with monitoring
            OptimizationTask(
                name="test_security_comprehensive",
                command="python -m pytest tests/test_security_comprehensive.py -v",
                timeout=300,
                expected_duration=60.0,
                critical=False
            ),
            OptimizationTask(
                name="test_rest_to_grpc_conversion",
                command="python -m pytest tests/test_rest_to_grpc_conversion.py -v",
                timeout=300,
                expected_duration=45.0,
                critical=False
            ),
            OptimizationTask(
                name="test_end_to_end_scenarios", 
                command="python -m pytest tests/test_end_to_end_scenarios.py -v",
                timeout=400,
                expected_duration=90.0,
                critical=False
            ),
            
            # Validation and demos
            OptimizationTask(
                name="run_standalone_demo",
                command="python standalone_demo.py",
                timeout=180,
                expected_duration=30.0,
                critical=False
            ),
            OptimizationTask(
                name="validate_100k_scalability",
                command="python -c \"from universal_api_bridge.config import create_massive_scale_config; print('100k config:', create_massive_scale_config(100000).mcp.max_services)\"",
                timeout=30,
                expected_duration=5.0,
                critical=True
            )
        ]
    
    async def run_optimization_suite(self) -> Dict[str, Any]:
        """Run the complete optimization suite with monitoring."""
        print("🚀 Universal API Bridge - Monitored Optimization Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run system diagnostics first
        if self.diagnostics:
            print("\n🔍 Running system diagnostics...")
            await self._run_diagnostics()
        
        # Execute optimization tasks
        print(f"\n⚡ Executing {len(self.tasks)} optimization tasks...")
        successful_tasks = 0
        failed_tasks = 0
        
        for i, task in enumerate(self.tasks, 1):
            print(f"\n📋 Task {i}/{len(self.tasks)}: {task.name}")
            print(f"   Command: {task.command}")
            print(f"   Timeout: {task.timeout}s | Expected: {task.expected_duration}s")
            
            # Execute task with monitoring
            result = await self._execute_monitored_task(task)
            self.results[task.name] = result
            
            if result.success:
                successful_tasks += 1
                status = "✅ SUCCESS"
                if result.duration > task.expected_duration * 2:
                    status += " (⚠️  SLOW)"
            else:
                failed_tasks += 1
                status = "❌ FAILED"
                if task.critical:
                    status += " (🚨 CRITICAL)"
            
            print(f"   Result: {status} | Duration: {result.duration:.1f}s")
            
            # Stop on critical failure
            if not result.success and task.critical:
                print(f"\n🚨 Critical task failed: {task.name}")
                print("🛑 Stopping optimization suite")
                break
        
        # Generate comprehensive report
        total_duration = time.time() - start_time
        report = await self._generate_optimization_report(
            successful_tasks, failed_tasks, total_duration
        )
        
        print(f"\n🎯 OPTIMIZATION SUITE COMPLETE")
        print("=" * 50)
        print(f"✅ Successful: {successful_tasks}/{len(self.tasks)}")
        print(f"❌ Failed: {failed_tasks}/{len(self.tasks)}")
        print(f"⏱️  Total Duration: {total_duration:.1f}s")
        print(f"📊 Success Rate: {(successful_tasks/len(self.tasks)*100):.1f}%")
        
        return report
    
    async def _execute_monitored_task(self, task: OptimizationTask) -> OptimizationTask:
        """Execute a task with shell monitor protection."""
        if self.monitor:
            # Use shell monitor for protected execution
            result = self.monitor.run_command(
                task.command,
                timeout=task.timeout,
                cwd=str(self.project_root)
            )
            
            task.completed = True
            task.duration = result.duration or 0.0
            task.success = result.returncode == 0 and not result.timed_out
            task.output = result.stdout
            task.error = result.stderr
            
            if result.timed_out:
                task.error = f"Command timed out after {task.timeout}s"
                print(f"   ⏰ TIMEOUT: Command exceeded {task.timeout}s limit")
            
        else:
            # Fallback to standard execution
            try:
                import subprocess
                start_time = time.time()
                
                result = subprocess.run(
                    task.command.split(),
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=task.timeout
                )
                
                task.completed = True
                task.duration = time.time() - start_time
                task.success = result.returncode == 0
                task.output = result.stdout
                task.error = result.stderr
                
            except subprocess.TimeoutExpired:
                task.completed = True
                task.duration = task.timeout
                task.success = False
                task.error = f"Command timed out after {task.timeout}s"
            except Exception as e:
                task.completed = True
                task.duration = time.time() - start_time if 'start_time' in locals() else 0
                task.success = False
                task.error = str(e)
        
        return task
    
    async def _run_diagnostics(self) -> None:
        """Run system diagnostics with the shell monitor."""
        if not self.diagnostics:
            return
        
        try:
            print("   🔍 System performance check...")
            perf_report = self.diagnostics.run_performance_tests()
            
            print("   🔍 Environment analysis...")
            env_report = self.diagnostics.analyze_environment()
            
            print("   🔍 Command performance tests...")
            cmd_report = self.diagnostics.test_command_performance()
            
            # Save diagnostics report
            diagnostics_report = {
                "timestamp": time.time(),
                "performance": perf_report,
                "environment": env_report,
                "commands": cmd_report
            }
            
            with open(self.project_root / "optimization_diagnostics.json", "w") as f:
                json.dump(diagnostics_report, f, indent=2)
            
            print("   ✅ Diagnostics complete - saved to optimization_diagnostics.json")
            
        except Exception as e:
            print(f"   ⚠️  Diagnostics failed: {e}")
    
    async def _generate_optimization_report(self, successful: int, failed: int, duration: float) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        report = {
            "timestamp": time.time(),
            "optimization_suite": {
                "total_tasks": len(self.tasks),
                "successful_tasks": successful,
                "failed_tasks": failed,
                "success_rate": successful / len(self.tasks) if self.tasks else 0,
                "total_duration": duration
            },
            "task_results": {},
            "performance_summary": {},
            "recommendations": []
        }
        
        # Add task details
        total_expected = sum(task.expected_duration for task in self.tasks)
        total_actual = sum(task.duration for task in self.tasks if task.completed)
        
        for task in self.tasks:
            report["task_results"][task.name] = {
                "success": task.success,
                "duration": task.duration,
                "expected_duration": task.expected_duration,
                "performance_ratio": task.duration / task.expected_duration if task.expected_duration > 0 else 1.0,
                "critical": task.critical,
                "timed_out": "timeout" in task.error.lower() if task.error else False
            }
        
        # Performance summary
        report["performance_summary"] = {
            "expected_total_duration": total_expected,
            "actual_total_duration": total_actual,
            "performance_efficiency": total_expected / total_actual if total_actual > 0 else 1.0,
            "slow_tasks": [
                task.name for task in self.tasks 
                if task.completed and task.duration > task.expected_duration * 2
            ]
        }
        
        # Generate recommendations
        if failed > 0:
            report["recommendations"].append("🔧 Review failed tasks and resolve dependency issues")
        
        if report["performance_summary"]["performance_efficiency"] < 0.5:
            report["recommendations"].append("⚡ System performance is below expected - consider optimizing environment")
        
        if len(report["performance_summary"]["slow_tasks"]) > 0:
            report["recommendations"].append(f"🐌 {len(report['performance_summary']['slow_tasks'])} tasks were slower than expected")
        
        # Save report
        with open(self.project_root / "MONITORED_OPTIMIZATION_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def get_monitor_history(self) -> List[Dict]:
        """Get command execution history from monitor."""
        if self.monitor:
            return [cmd.to_dict() for cmd in self.monitor.history]
        return []
    
    def print_monitor_summary(self) -> None:
        """Print shell monitor summary."""
        if self.monitor:
            self.monitor.print_summary()

async def main():
    """Main optimization workflow with shell monitor integration."""
    print("🔍 Universal API Bridge - Monitored Optimization")
    print("=" * 60)
    
    # Initialize monitored optimizer
    optimizer = MonitoredOptimizer(".")
    
    try:
        # Run complete optimization suite
        report = await optimizer.run_optimization_suite()
        
        # Print monitor summary
        print("\n📊 Shell Monitor Summary:")
        optimizer.print_monitor_summary()
        
        # Show final recommendations
        if report.get("recommendations"):
            print("\n💡 Optimization Recommendations:")
            for rec in report["recommendations"]:
                print(f"   {rec}")
        
        print(f"\n📋 Detailed reports saved:")
        print(f"   - MONITORED_OPTIMIZATION_REPORT.json")
        print(f"   - optimization_diagnostics.json")
        print(f"   - optimization_monitor.log")
        
        print(f"\n🏆 Optimization complete with shell monitor protection!")
        
        return report
        
    except KeyboardInterrupt:
        print("\n\n🛑 Optimization interrupted by user")
        optimizer.print_monitor_summary()
        return None
    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        optimizer.print_monitor_summary()
        return None

if __name__ == "__main__":
    # Run optimization with shell monitor
    asyncio.run(main()) 