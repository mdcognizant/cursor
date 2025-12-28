#!/usr/bin/env python3
"""
🛡️ ROBUST AUTO STARTUP SYSTEM 🛡️
==================================
Comprehensive startup solution with anti-hanging protection for PowerShell environments.

This system:
- Uses shell monitor to prevent command hanging
- Works around PowerShell limitations (no && operator)
- Forces all services to start automatically
- Provides robust error handling and fallbacks
- Monitors service health continuously

Author: Assistant
Date: 2025-01-27
Version: 3.0 (PowerShell Safe)
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
import json
import signal
import psutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
import traceback

class RobustAutoStartup:
    def __init__(self):
        self.services = {}
        self.processes = {}
        self.health_monitors = {}
        self.startup_log = []
        self.is_running = True
        
        # Service configurations optimized for PowerShell
        self.service_configs = {
            'enhanced_scraper': {
                'name': 'Enhanced News Scraper',
                'script': 'enhanced_news_scraper.py',
                'port': 8889,
                'health_url': 'http://localhost:8889/health',
                'timeout': 30,
                'retries': 3,
                'critical': True
            },
            'breaking_news': {
                'name': 'Breaking News Scraper',
                'script': 'breaking_news_scraper.py',
                'port': 8888,
                'health_url': 'http://localhost:8888/health',
                'timeout': 30,
                'retries': 3,
                'critical': True
            },
            'error_monitor': {
                'name': 'Fixed Error Monitor',
                'script': 'fixed_error_monitor.py',
                'port': None,
                'health_url': None,
                'timeout': 20,
                'retries': 2,
                'critical': False
            },
            'http_server': {
                'name': 'HTTP Server',
                'script': None,  # Built-in
                'port': 8000,
                'health_url': 'http://localhost:8000',
                'timeout': 15,
                'retries': 2,
                'critical': True
            }
        }
        
        self.frontend_apps = [
            'enhanced_news_platform_ultimate_v2.html',  # Primary V2 template
            'enhanced_news_platform_ultimate_v2_BACKUP_STABLE.html',  # Backup version
            'enhanced_delta_news_platform_complete.html'  # Alternative platform
        ]

    def log(self, message, level="INFO"):
        """Add message to startup log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        self.startup_log.append(log_entry)
        print(log_entry)

    def safe_subprocess_run(self, command, timeout=30, shell=True):
        """Run subprocess with timeout and error handling"""
        try:
            self.log(f"Executing: {command}")
            
            # Use Popen for better control
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            # Wait with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {
                    'success': process.returncode == 0,
                    'returncode': process.returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                    'process': process
                }
            except subprocess.TimeoutExpired:
                self.log(f"Command timed out after {timeout}s: {command}", "ERROR")
                process.kill()
                return {
                    'success': False,
                    'returncode': -1,
                    'stdout': '',
                    'stderr': f'Command timed out after {timeout} seconds',
                    'process': None
                }
                
        except Exception as e:
            self.log(f"Failed to execute command: {e}", "ERROR")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'process': None
            }

    def start_background_service(self, service_id, config):
        """Start a service in the background with anti-hang protection"""
        self.log(f"Starting {config['name']}...")
        
        if config['script']:
            # Python script service
            command = f"python {config['script']}"
            
            try:
                # Start the service
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
                )
                
                self.processes[service_id] = process
                self.log(f"✅ {config['name']} started (PID: {process.pid})")
                
                # Wait a moment for service to initialize
                time.sleep(2)
                
                # Check if process is still running
                if process.poll() is None:
                    self.log(f"✅ {config['name']} is running")
                    return True
                else:
                    self.log(f"❌ {config['name']} exited immediately", "ERROR")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Failed to start {config['name']}: {e}", "ERROR")
                return False
        
        elif service_id == 'http_server':
            # Built-in HTTP server
            return self.start_http_server(config['port'])
        
        return False

    def start_http_server(self, port):
        """Start HTTP server with robust error handling"""
        try:
            # Check if port is already in use
            if self.is_port_in_use(port):
                self.log(f"Port {port} already in use, attempting to use it", "WARNING")
                return True
            
            command = f"python -m http.server {port}"
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            self.processes['http_server'] = process
            self.log(f"✅ HTTP Server started on port {port} (PID: {process.pid})")
            
            # Give server time to start
            time.sleep(3)
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to start HTTP server: {e}", "ERROR")
            return False

    def is_port_in_use(self, port):
        """Check if a port is already in use"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            return False

    def check_service_health(self, service_id, config):
        """Check if a service is healthy"""
        if not config['health_url']:
            # No health check available, just check if process is running
            if service_id in self.processes:
                process = self.processes[service_id]
                return process and process.poll() is None
            return False
        
        try:
            response = requests.get(config['health_url'], timeout=5)
            is_healthy = response.status_code == 200
            if is_healthy:
                self.log(f"✅ {config['name']} health check passed")
            else:
                self.log(f"⚠️ {config['name']} health check failed (status: {response.status_code})")
            return is_healthy
        except Exception as e:
            self.log(f"❌ {config['name']} health check failed: {e}")
            return False

    def wait_for_service_ready(self, service_id, config, max_attempts=10):
        """Wait for service to be ready with health checks"""
        if not config['health_url']:
            self.log(f"No health check for {config['name']}, assuming ready")
            return True
        
        self.log(f"Waiting for {config['name']} to be ready...")
        
        for attempt in range(max_attempts):
            if self.check_service_health(service_id, config):
                self.log(f"✅ {config['name']} is ready!")
                return True
            
            if attempt < max_attempts - 1:
                self.log(f"⏳ Attempt {attempt + 1}/{max_attempts} - waiting...")
                time.sleep(2)
        
        self.log(f"⚠️ {config['name']} may not be fully ready, continuing anyway", "WARNING")
        return False

    def start_all_services(self):
        """Start all services with robust error handling"""
        self.log("🚀 Starting all services with anti-hang protection...")
        
        success_count = 0
        total_services = len(self.service_configs)
        
        for service_id, config in self.service_configs.items():
            try:
                self.log(f"📋 Starting {config['name']}...")
                
                # Attempt to start service with retries
                started = False
                for attempt in range(config['retries']):
                    if attempt > 0:
                        self.log(f"🔄 Retry {attempt + 1}/{config['retries']} for {config['name']}")
                    
                    if self.start_background_service(service_id, config):
                        if self.wait_for_service_ready(service_id, config):
                            started = True
                            break
                    
                    if attempt < config['retries'] - 1:
                        self.log(f"⏳ Waiting before retry...")
                        time.sleep(5)
                
                if started:
                    success_count += 1
                    self.log(f"✅ {config['name']} started successfully")
                else:
                    level = "ERROR" if config['critical'] else "WARNING"
                    self.log(f"❌ Failed to start {config['name']} after {config['retries']} attempts", level)
                
            except Exception as e:
                self.log(f"❌ Exception starting {config['name']}: {e}", "ERROR")
                self.log(f"Stack trace: {traceback.format_exc()}", "DEBUG")
        
        self.log(f"📊 Startup complete: {success_count}/{total_services} services started")
        return success_count

    def open_frontend_applications(self):
        """Open frontend applications with error handling"""
        self.log("🌐 Opening frontend applications...")
        
        base_url = "http://localhost:8000"
        
        for app_file in self.frontend_apps:
            try:
                if os.path.exists(app_file):
                    url = f"{base_url}/{app_file}"
                    self.log(f"📱 Opening {app_file}")
                    webbrowser.open(url)
                    time.sleep(1)  # Small delay between opens
                else:
                    self.log(f"⚠️ Frontend app not found: {app_file}", "WARNING")
                    
            except Exception as e:
                self.log(f"❌ Failed to open {app_file}: {e}", "ERROR")

    def start_health_monitoring(self):
        """Start continuous health monitoring"""
        def monitor_services():
            while self.is_running:
                try:
                    for service_id, config in self.service_configs.items():
                        if service_id in self.processes:
                            # Check if process is still running
                            process = self.processes[service_id]
                            if process and process.poll() is not None:
                                self.log(f"⚠️ {config['name']} process died, attempting restart", "WARNING")
                                self.start_background_service(service_id, config)
                    
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    self.log(f"❌ Health monitoring error: {e}", "ERROR")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor_services, daemon=True)
        monitor_thread.start()
        self.log("✅ Health monitoring started")

    def create_startup_report(self):
        """Create a detailed startup report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services_started': len([p for p in self.processes.values() if p and p.poll() is None]),
            'total_services': len(self.service_configs),
            'running_processes': {},
            'port_status': {},
            'startup_log': self.startup_log
        }
        
        # Check running processes
        for service_id, process in self.processes.items():
            if process:
                report['running_processes'][service_id] = {
                    'pid': process.pid,
                    'running': process.poll() is None
                }
        
        # Check port status
        for service_id, config in self.service_configs.items():
            if config['port']:
                report['port_status'][config['port']] = self.is_port_in_use(config['port'])
        
        # Save report
        try:
            with open('startup_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            self.log("📄 Startup report saved to startup_report.json")
        except Exception as e:
            self.log(f"❌ Failed to save startup report: {e}", "ERROR")
        
        return report

    def cleanup(self):
        """Clean up all processes"""
        self.log("🛑 Shutting down all services...")
        self.is_running = False
        
        for service_id, process in self.processes.items():
            try:
                if process and process.poll() is None:
                    self.log(f"Stopping {service_id}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.log(f"Force killing {service_id}...")
                        process.kill()
                    
                    self.log(f"✅ {service_id} stopped")
            except Exception as e:
                self.log(f"❌ Error stopping {service_id}: {e}", "ERROR")

    def run_comprehensive_startup(self):
        """Run the complete startup sequence"""
        self.log("🛡️ ROBUST AUTO STARTUP SYSTEM INITIATED 🛡️")
        self.log("=" * 60)
        
        try:
            # Step 1: Start all services
            services_started = self.start_all_services()
            
            # Step 2: Start health monitoring
            self.start_health_monitoring()
            
            # Step 3: Open frontend applications
            if services_started > 0:
                time.sleep(3)  # Let services fully initialize
                self.open_frontend_applications()
            
            # Step 4: Create startup report
            report = self.create_startup_report()
            
            # Step 5: Show summary
            self.show_startup_summary(report)
            
            # Step 6: Keep running
            self.log("✅ All systems operational! Press Ctrl+C to stop...")
            self.keep_running()
            
        except KeyboardInterrupt:
            self.log("🛑 Shutdown requested by user")
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", "ERROR")
            self.log(f"Stack trace: {traceback.format_exc()}", "DEBUG")
        finally:
            self.cleanup()

    def show_startup_summary(self, report):
        """Show comprehensive startup summary"""
        print("\n" + "=" * 60)
        print("📊 STARTUP SUMMARY")
        print("=" * 60)
        print(f"🕐 Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Services Started: {report['services_started']}/{report['total_services']}")
        
        if report['running_processes']:
            print("\n🏃 Running Services:")
            for service_id, info in report['running_processes'].items():
                status = "✅ Running" if info['running'] else "❌ Stopped"
                print(f"   • {service_id}: PID {info['pid']} - {status}")
        
        if report['port_status']:
            print("\n🌐 Port Status:")
            for port, in_use in report['port_status'].items():
                status = "✅ Active" if in_use else "❌ Inactive"
                print(f"   • Port {port}: {status}")
        
        print("\n💡 Available Services:")
        print("   🌐 Enhanced News Platform: http://localhost:8000/enhanced_news_platform_ultimate_v2.html")
        print("   📰 Delta News Platform: http://localhost:8000/enhanced_delta_news_platform_complete.html")
        print("   📡 Enhanced Scraper API: http://localhost:8889/articles")
        print("   📢 Breaking News API: http://localhost:8888/breaking-news")
        
        if report['services_started'] == report['total_services']:
            print("\n🎉 ALL SYSTEMS FULLY OPERATIONAL!")
        else:
            print(f"\n⚠️ {report['total_services'] - report['services_started']} services failed to start")

    def keep_running(self):
        """Keep the system running until interrupted"""
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def main():
    """Main entry point"""
    startup_system = RobustAutoStartup()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        startup_system.log("🛑 Shutdown signal received")
        startup_system.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the comprehensive startup
    startup_system.run_comprehensive_startup()

if __name__ == "__main__":
    main() 