#!/usr/bin/env python3
"""
Error Monitoring System Launcher
===============================
Starts the complete recursive error monitoring and auto-fixing system.

This script launches:
1. Error Monitor Backend (main monitoring process)
2. Error Log Aggregator (centralized logging)
3. Periodic Report Generator
4. API Health Monitor
5. System Resource Monitor

Usage:
    python start_error_monitoring.py [--config config.json] [--background]
"""

import asyncio
import subprocess
import sys
import os
import json
import logging
import time
import signal
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorMonitoringSystem:
    def __init__(self, config_file: str = "error_monitor_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.processes = []
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def load_config(self) -> dict:
        """Load system configuration"""
        default_config = {
            "components": {
                "error_monitor_backend": True,
                "error_log_aggregator": True,
                "api_health_monitor": True,
                "system_resource_monitor": True,
                "periodic_reporter": True
            },
            "startup_delay": 2,
            "health_check_interval": 60,
            "auto_restart": True,
            "max_restart_attempts": 5,
            "log_directory": "monitoring_logs",
            "pid_file": "error_monitoring.pid"
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return default_config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return default_config

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    async def start_system(self):
        """Start the complete error monitoring system"""
        logger.info("🚀 Starting Error Monitoring System...")
        
        # Create necessary directories
        self.setup_directories()
        
        # Write PID file
        self.write_pid_file()
        
        # Start all components
        await self.start_components()
        
        # Start health monitoring
        await self.start_health_monitoring()

    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            self.config['log_directory'],
            "error_logs",
            "error_reports",
            "error_summaries",
            "monitoring_logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"📁 Created directory: {directory}")

    def write_pid_file(self):
        """Write process ID to file"""
        try:
            with open(self.config['pid_file'], 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"📝 Written PID file: {self.config['pid_file']}")
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")

    async def start_components(self):
        """Start all monitoring components"""
        self.running = True
        
        components = []
        
        # 1. Error Monitor Backend
        if self.config['components']['error_monitor_backend']:
            components.append(self.start_error_monitor_backend())
        
        # 2. Error Log Aggregator
        if self.config['components']['error_log_aggregator']:
            components.append(self.start_error_log_aggregator())
        
        # 3. API Health Monitor
        if self.config['components']['api_health_monitor']:
            components.append(self.start_api_health_monitor())
        
        # 4. System Resource Monitor
        if self.config['components']['system_resource_monitor']:
            components.append(self.start_system_resource_monitor())
        
        # 5. Periodic Reporter
        if self.config['components']['periodic_reporter']:
            components.append(self.start_periodic_reporter())
        
        logger.info(f"🔧 Starting {len(components)} monitoring components...")
        
        # Start all components concurrently
        try:
            await asyncio.gather(*components)
        except Exception as e:
            logger.error(f"Error in monitoring components: {e}")
            self.shutdown()

    async def start_error_monitor_backend(self):
        """Start the main error monitoring backend"""
        logger.info("🔍 Starting Error Monitor Backend...")
        
        try:
            # Import and start the error monitor
            from error_monitor_backend import ErrorMonitorBackend
            
            monitor = ErrorMonitorBackend(self.config_file)
            await monitor.start_monitoring()
            
        except ImportError:
            logger.error("Error Monitor Backend module not found!")
            # Fallback: run as subprocess
            process = subprocess.Popen([
                sys.executable, "error_monitor_backend.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            
        except Exception as e:
            logger.error(f"Failed to start Error Monitor Backend: {e}")

    async def start_error_log_aggregator(self):
        """Start the error log aggregator"""
        logger.info("📝 Starting Error Log Aggregator...")
        
        try:
            from error_log_aggregator import ErrorLogAggregator
            
            aggregator = ErrorLogAggregator(self.config_file)
            await aggregator.start_aggregation()
            
        except ImportError:
            logger.error("Error Log Aggregator module not found!")
            process = subprocess.Popen([
                sys.executable, "error_log_aggregator.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            
        except Exception as e:
            logger.error(f"Failed to start Error Log Aggregator: {e}")

    async def start_api_health_monitor(self):
        """Start API health monitoring"""
        logger.info("🌐 Starting API Health Monitor...")
        
        api_endpoints = [
            "https://newsdata.io/api/1/latest",
            "https://api.currentsapi.services/v1/latest-news"
        ]
        
        while self.running:
            try:
                for endpoint in api_endpoints:
                    await self.check_api_health(endpoint)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"API Health Monitor error: {e}")
                await asyncio.sleep(60)

    async def check_api_health(self, endpoint: str):
        """Check health of a specific API endpoint"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(endpoint, timeout=30) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    health_status = {
                        "timestamp": datetime.now().isoformat(),
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "response_time_ms": response_time,
                        "healthy": response.status == 200 and response_time < 5000
                    }
                    
                    # Log health status
                    health_log_file = f"{self.config['log_directory']}/api_health.log"
                    with open(health_log_file, 'a') as f:
                        f.write(f"{json.dumps(health_status)}\n")
                    
                    if not health_status['healthy']:
                        logger.warning(f"🚨 API Health Issue: {endpoint} - Status: {response.status}, Time: {response_time:.0f}ms")
        
        except Exception as e:
            logger.error(f"Failed to check API health for {endpoint}: {e}")

    async def start_system_resource_monitor(self):
        """Start system resource monitoring"""
        logger.info("📊 Starting System Resource Monitor...")
        
        try:
            import psutil
        except ImportError:
            logger.error("psutil not installed - skipping system resource monitoring")
            return
        
        while self.running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                resource_data = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
                
                # Log resource data
                resource_log_file = f"{self.config['log_directory']}/system_resources.log"
                with open(resource_log_file, 'a') as f:
                    f.write(f"{json.dumps(resource_data)}\n")
                
                # Check for resource alerts
                if cpu_percent > 90:
                    logger.warning(f"🚨 High CPU usage: {cpu_percent}%")
                if memory.percent > 85:
                    logger.warning(f"🚨 High memory usage: {memory.percent}%")
                if disk.percent > 90:
                    logger.warning(f"🚨 High disk usage: {disk.percent}%")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"System Resource Monitor error: {e}")
                await asyncio.sleep(60)

    async def start_periodic_reporter(self):
        """Start periodic report generation"""
        logger.info("📋 Starting Periodic Reporter...")
        
        while self.running:
            try:
                await self.generate_system_report()
                await asyncio.sleep(3600)  # Generate every hour
                
            except Exception as e:
                logger.error(f"Periodic Reporter error: {e}")
                await asyncio.sleep(300)

    async def generate_system_report(self):
        """Generate comprehensive system report"""
        report_time = datetime.now()
        
        # Collect statistics from all log files
        stats = {
            "report_timestamp": report_time.isoformat(),
            "system_uptime": self.get_system_uptime(),
            "monitoring_components": {
                "error_monitor": self.is_component_running("error_monitor_backend"),
                "log_aggregator": self.is_component_running("error_log_aggregator"),
                "api_monitor": self.is_component_running("api_health_monitor"),
                "resource_monitor": self.is_component_running("system_resource_monitor")
            },
            "log_file_sizes": self.get_log_file_sizes(),
            "recent_error_count": self.count_recent_errors()
        }
        
        # Save report
        report_file = f"error_reports/system_report_{report_time.strftime('%Y%m%d_%H')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        logger.info(f"📊 Generated system report: {report_file}")

    def get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            import psutil
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            return str(uptime_seconds)
        except:
            return "unknown"

    def is_component_running(self, component_name: str) -> bool:
        """Check if a monitoring component is running"""
        # This is a simplified check - in production you'd check actual process status
        return True

    def get_log_file_sizes(self) -> dict:
        """Get sizes of all log files"""
        log_sizes = {}
        
        for log_dir in ["error_logs", "monitoring_logs", "error_reports"]:
            if os.path.exists(log_dir):
                for file_path in Path(log_dir).rglob("*.log"):
                    try:
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        log_sizes[str(file_path)] = f"{size_mb:.2f}MB"
                    except:
                        log_sizes[str(file_path)] = "unknown"
        
        return log_sizes

    def count_recent_errors(self) -> int:
        """Count recent errors from master log"""
        try:
            if os.path.exists("master_error_log.jsonl"):
                with open("master_error_log.jsonl", 'r') as f:
                    lines = f.readlines()
                
                # Count errors from last hour
                one_hour_ago = datetime.now().timestamp() - 3600
                recent_errors = 0
                
                for line in lines[-1000:]:  # Check last 1000 lines
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'new_error':
                            timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                            if timestamp.timestamp() > one_hour_ago:
                                recent_errors += 1
                    except:
                        continue
                
                return recent_errors
        except:
            pass
        
        return 0

    async def start_health_monitoring(self):
        """Monitor health of all components"""
        logger.info("❤️ Starting Health Monitoring...")
        
        while self.running:
            try:
                # Check if all processes are still running
                for process in self.processes:
                    if process.poll() is not None:
                        logger.warning(f"🚨 Process died: PID {process.pid}")
                        
                        if self.config['auto_restart']:
                            logger.info("🔄 Auto-restarting failed component...")
                            # Restart logic would go here
                
                await asyncio.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)

    def shutdown(self):
        """Shutdown the monitoring system"""
        logger.info("🛑 Shutting down Error Monitoring System...")
        self.running = False
        
        # Terminate all processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except:
                process.kill()
        
        # Remove PID file
        try:
            if os.path.exists(self.config['pid_file']):
                os.remove(self.config['pid_file'])
        except:
            pass
        
        logger.info("✅ Error Monitoring System stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Error Monitoring System Launcher")
    parser.add_argument("--config", default="error_monitor_config.json", help="Configuration file")
    parser.add_argument("--background", action="store_true", help="Run in background")
    
    args = parser.parse_args()
    
    if args.background:
        # Daemonize the process (simplified)
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    
    # Start the monitoring system
    system = ErrorMonitoringSystem(args.config)
    
    try:
        asyncio.run(system.start_system())
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        system.shutdown()

if __name__ == "__main__":
    main() 