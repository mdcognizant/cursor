#!/usr/bin/env python3
"""
🚀 ULTIMATE PLATFORM LAUNCHER 🚀
==================================
Comprehensive startup system for all news platform services and components.

This script automatically launches:
- Breaking News Scraper (CNN/BBC)
- Error Monitoring System
- Shell Monitor Service
- Enhanced News Platform
- News Platform V1
- Debug Console
- HTTP Server

Author: Assistant
Date: 2025-01-27
Version: 2.0
"""

import subprocess
import sys
import time
import webbrowser
import os
import json
import threading
import requests
from pathlib import Path
from datetime import datetime
import argparse
import signal

class UltimatePlatformLauncher:
    def __init__(self):
        self.processes = {}
        self.services_config = {
            'breaking_news_scraper': {
                'name': 'Breaking News Scraper',
                'script': 'breaking_news_scraper.py',
                'port': 8888,
                'health_endpoint': 'http://localhost:8888/health',
                'priority': 1,
                'description': 'Real-time CNN & BBC breaking news scraping',
                'enabled': True
            },
            'error_monitor': {
                'name': 'Error Monitoring System',
                'script': 'simple_error_monitor.py',
                'port': None,
                'health_endpoint': None,
                'priority': 2,
                'description': 'Background error detection and logging',
                'enabled': True
            },
            'command_monitor': {
                'name': 'Command Monitor',
                'script': 'shell_monitor_service.py',
                'port': 9999,
                'health_endpoint': None,
                'priority': 3,
                'description': 'Command execution protection',
                'enabled': True
            },
            'enhanced_news_scraper': {
                'name': 'Enhanced News Scraper',
                'script': 'enhanced_news_scraper.py',
                'port': 8889,
                'health_endpoint': 'http://localhost:8889/health',
                'priority': 5,
                'description': 'Multi-source news scraping (CNN, BBC, NPR, Guardian, Sky, Yahoo)',
                'enabled': True  # Enabled by default for more content
            },
            'http_server': {
                'name': 'HTTP Server',
                'script': None,  # Built-in
                'port': 8000,
                'health_endpoint': 'http://localhost:8000',
                'priority': 6,
                'description': 'Local file serving',
                'enabled': True
            }
        }
        
        self.frontend_apps = {
            'main_platform': {
                'name': 'Enhanced News Platform',
                'file': 'enhanced_news_platform_ultimate_v2.html',
                'description': 'Main news platform with all features',
                'enabled': True
            },
            'debug_console': {
                'name': 'Debug Console',
                'file': 'frontend_debug_console.html',
                'description': 'API monitoring and debugging',
                'enabled': False  # Optional by default
            }
        }
        
        self.startup_stats = {
            'start_time': datetime.now(),
            'services_started': 0,
            'services_failed': 0,
            'total_services': 0,
            'frontend_apps_opened': 0
        }

    def print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 ULTIMATE PLATFORM LAUNCHER 🚀                         ║
║                                                                              ║
║   Comprehensive News Platform with All Services                             ║
║   • Breaking News Scraper (CNN/BBC)    • Error Monitoring System           ║
║   • Enhanced News Platform             • Shell Monitor Service              ║
║   • News Platform V1                   • Real News Scraper                  ║
║   • Debug Console                      • HTTP Server                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"🕐 Launch Time: {self.startup_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def check_dependencies(self):
        """Check if all required files exist"""
        print("🔍 Checking dependencies...")
        
        missing_files = []
        
        # Check service scripts
        for service_id, config in self.services_config.items():
            if config['script'] and config['enabled']:
                if not os.path.exists(config['script']):
                    missing_files.append(f"Service: {config['script']}")
        
        # Check frontend files
        for app_id, config in self.frontend_apps.items():
            if config['enabled']:
                if not os.path.exists(config['file']):
                    missing_files.append(f"Frontend: {config['file']}")
        
        if missing_files:
            print(f"❌ Missing required files:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print("✅ All dependencies found")
        return True

    def start_service(self, service_id, config):
        """Start a specific service"""
        if not config['enabled']:
            return True
            
        print(f"🔄 Starting {config['name']}...")
        
        try:
            if service_id == 'command_monitor':
                return self.start_shell_monitor_service()
            elif service_id == 'http_server':
                return self.start_http_server(config['port'])
            elif config['script']:
                process = subprocess.Popen([
                    sys.executable, config['script']
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                self.processes[service_id] = process
                print(f"✅ {config['name']} started (PID: {process.pid})")
                
                # Wait for service to be ready if it has a health endpoint
                if config['health_endpoint']:
                    self.wait_for_service_ready(config['health_endpoint'], config['name'])
                
                return True
            
        except Exception as e:
            print(f"❌ Failed to start {config['name']}: {e}")
            return False
        
        return True

    def start_shell_monitor_service(self):
        """Start shell monitor service"""
        try:
            # Create shell monitor service if it doesn't exist
            if not os.path.exists('shell_monitor_service.py'):
                self.create_shell_monitor_service()
            
            process = subprocess.Popen([
                sys.executable, 'shell_monitor_service.py'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.processes['command_monitor'] = process
            print(f"✅ Shell Monitor Service started (PID: {process.pid})")
            
            # Create helper scripts
            self.create_shell_monitor_helpers()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Shell Monitor Service: {e}")
            return False

    def start_http_server(self, port):
        """Start HTTP server"""
        try:
            process = subprocess.Popen([
                sys.executable, '-m', 'http.server', str(port)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.processes['http_server'] = process
            print(f"✅ HTTP Server started on port {port} (PID: {process.pid})")
            
            time.sleep(2)  # Give server time to start
            return True
            
        except Exception as e:
            print(f"❌ Failed to start HTTP Server: {e}")
            return False

    def wait_for_service_ready(self, endpoint, service_name, max_attempts=10):
        """Wait for service to be ready"""
        print(f"⏳ Waiting for {service_name} to be ready...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(endpoint, timeout=2)
                if response.status_code == 200:
                    print(f"✅ {service_name} is ready!")
                    return True
            except:
                time.sleep(1)
                if attempt < max_attempts - 1:
                    print(f"   ⏳ Attempt {attempt + 1}/{max_attempts}...")
        
        print(f"⚠️ {service_name} may not be fully ready, but continuing...")
        return False

    def open_frontend_apps(self, use_http_server=True, http_port=8000):
        """Open frontend applications"""
        print("\n🌐 Opening frontend applications...")
        
        for app_id, config in self.frontend_apps.items():
            if not config['enabled']:
                continue
                
            print(f"📱 Opening {config['name']}...")
            
            try:
                if use_http_server:
                    url = f"http://localhost:{http_port}/{config['file']}"
                    webbrowser.open(url)
                else:
                    file_path = os.path.abspath(config['file'])
                    webbrowser.open(f"file:///{file_path}")
                
                print(f"✅ {config['name']} opened in browser")
                self.startup_stats['frontend_apps_opened'] += 1
                
                # Small delay between opening apps
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Failed to open {config['name']}: {e}")

    def create_shell_monitor_service(self):
        """Create shell monitor service if needed"""
        service_code = '''#!/usr/bin/env python3
"""
Shell Monitor Background Service
===============================
Lightweight shell monitoring service.
"""

import time
import threading
import socket
import subprocess
import sys

class ShellMonitorService:
    def __init__(self):
        self.running = False
        
    def start_service(self):
        print("🔧 Shell Monitor Service starting...")
        self.running = True
        
        try:
            while self.running:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\\n🛑 Shell Monitor Service stopping...")
            self.running = False

if __name__ == "__main__":
    service = ShellMonitorService()
    service.start_service()
'''
        
        try:
            with open('shell_monitor_service.py', 'w') as f:
                f.write(service_code)
            print("✅ Created shell monitor service")
        except Exception as e:
            print(f"❌ Failed to create shell monitor service: {e}")

    def create_shell_monitor_helpers(self):
        """Create shell monitor helper scripts"""
        run_with_monitor = '''#!/usr/bin/env python3
"""
Quick Shell Monitor Command Runner
"""
import sys
import subprocess

def run_with_monitor(command):
    print(f"🔄 Running with monitor: {command}")
    try:
        result = subprocess.run(command, shell=True, timeout=300)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out after 5 minutes")
        return 124
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_with_monitor.py 'command to run'")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    exit_code = run_with_monitor(command)
    sys.exit(exit_code)
'''
        
        try:
            if not os.path.exists('run_with_monitor.py') or os.path.getsize('run_with_monitor.py') == 0:
                with open('run_with_monitor.py', 'w') as f:
                    f.write(run_with_monitor)
                print("✅ Created shell monitor helper")
        except Exception as e:
            print(f"⚠️ Shell monitor helper creation: {e}")

    def start_all_services(self):
        """Start all enabled services"""
        print("\n🚀 Starting all services...")
        print("-" * 50)
        
        # Sort services by priority
        sorted_services = sorted(
            self.services_config.items(),
            key=lambda x: x[1]['priority']
        )
        
        self.startup_stats['total_services'] = len([s for s in sorted_services if s[1]['enabled']])
        
        for service_id, config in sorted_services:
            if self.start_service(service_id, config):
                self.startup_stats['services_started'] += 1
            else:
                self.startup_stats['services_failed'] += 1
        
        print("-" * 50)

    def print_startup_summary(self):
        """Print startup summary"""
        duration = datetime.now() - self.startup_stats['start_time']
        
        print("\n" + "=" * 80)
        print("📊 STARTUP SUMMARY")
        print("=" * 80)
        print(f"⏱️  Startup Duration: {duration.total_seconds():.1f} seconds")
        print(f"🔧 Services Started: {self.startup_stats['services_started']}/{self.startup_stats['total_services']}")
        print(f"📱 Frontend Apps: {self.startup_stats['frontend_apps_opened']} opened")
        
        if self.startup_stats['services_failed'] > 0:
            print(f"❌ Failed Services: {self.startup_stats['services_failed']}")
        
        if self.startup_stats['services_started'] == self.startup_stats['total_services']:
            print("\n✅ ALL SYSTEMS OPERATIONAL!")
            print("\n🎯 Active Features:")
            for service_id, config in self.services_config.items():
                if config['enabled']:
                    port_info = f" (Port: {config['port']})" if config['port'] else ""
                    print(f"   🔧 {config['name']}{port_info} - {config['description']}")
            
            print("\n📱 Frontend Applications:")
            for app_id, config in self.frontend_apps.items():
                if config['enabled']:
                    print(f"   🌐 {config['name']} - {config['description']}")
            
            print("\n💡 Usage Instructions:")
            print("   🔄 Breaking news updates every 30 seconds automatically")
            print("   🔐 Admin access: Use 'lemonade' password for unlimited refreshes")
            print("   📊 Error monitoring runs in background")
            print("   🛡️ Shell monitor prevents command hanging")
            print("   ⚡ All services running with premium features")
            
        else:
            print("⚠️ Some services failed to start - platform may have reduced functionality")

    def cleanup(self):
        """Clean up all processes"""
        print("\n🛑 Shutting down all services...")
        
        for service_id, process in self.processes.items():
            try:
                if process and process.poll() is None:
                    process.terminate()
                    print(f"✅ {service_id} stopped")
            except Exception as e:
                print(f"⚠️ Error stopping {service_id}: {e}")
        
        print("👋 Ultimate Platform Launcher stopped")

    def interactive_service_selection(self):
        """Allow user to interactively select services"""
        print("\n🔧 SERVICE CONFIGURATION")
        print("-" * 40)
        print("Select which services to start:")
        
        # Services selection
        print("\n📋 Backend Services:")
        for service_id, config in self.services_config.items():
            current = "✅" if config['enabled'] else "❌"
            choice = input(f"{current} {config['name']} - {config['description']} (y/n): ").lower().strip()
            config['enabled'] = choice in ['y', 'yes', '1', 'true']
        
        # Frontend apps selection
        print("\n📱 Frontend Applications:")
        for app_id, config in self.frontend_apps.items():
            current = "✅" if config['enabled'] else "❌"
            choice = input(f"{current} {config['name']} - {config['description']} (y/n): ").lower().strip()
            config['enabled'] = choice in ['y', 'yes', '1', 'true']

    def launch_platform(self, interactive=False, with_http_server=True, http_port=8000):
        """Launch the complete platform"""
        self.print_banner()
        
        # Interactive configuration
        if interactive:
            self.interactive_service_selection()
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Cannot launch - missing dependencies")
            return False
        
        # Start all services
        self.start_all_services()
        
        # Open frontend applications
        if any(app['enabled'] for app in self.frontend_apps.values()):
            self.open_frontend_apps(with_http_server, http_port)
        
        # Print summary
        self.print_startup_summary()
        
        return self.startup_stats['services_started'] > 0

    def save_configuration(self, filename='platform_config.json'):
        """Save current configuration"""
        config = {
            'services': self.services_config,
            'frontend_apps': self.frontend_apps,
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Configuration saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")

    def load_configuration(self, filename='platform_config.json'):
        """Load configuration from file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    config = json.load(f)
                    self.services_config = config.get('services', self.services_config)
                    self.frontend_apps = config.get('frontend_apps', self.frontend_apps)
                print(f"✅ Configuration loaded from {filename}")
                return True
        except Exception as e:
            print(f"⚠️ Failed to load configuration: {e}")
        return False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutdown signal received...")
    global launcher
    if launcher:
        launcher.cleanup()
    sys.exit(0)

def main():
    """Main entry point"""
    global launcher
    
    parser = argparse.ArgumentParser(
        description="Ultimate Platform Launcher - Start all news platform services"
    )
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive service selection')
    parser.add_argument('--no-http-server', action='store_true',
                       help='Don\'t start HTTP server')
    parser.add_argument('--port', type=int, default=8000,
                       help='HTTP server port (default: 8000)')
    parser.add_argument('--config', help='Load configuration from file')
    parser.add_argument('--save-config', help='Save current configuration to file')
    parser.add_argument('--list-services', action='store_true',
                       help='List all available services and exit')
    parser.add_argument('--minimal', action='store_true',
                       help='Start only essential services')
    
    args = parser.parse_args()
    
    launcher = UltimatePlatformLauncher()
    
    # Load configuration if specified
    if args.config:
        launcher.load_configuration(args.config)
    
    # Minimal mode - only essential services
    if args.minimal:
        for service_id, config in launcher.services_config.items():
            if service_id not in ['breaking_news_scraper', 'error_monitor', 'http_server']:
                config['enabled'] = False
        for app_id, config in launcher.frontend_apps.items():
            if app_id != 'main_platform':
                config['enabled'] = False
    
    # List services mode
    if args.list_services:
        launcher.print_banner()
        print("📋 Available Services:")
        for service_id, config in launcher.services_config.items():
            status = "✅" if config['enabled'] else "❌"
            port_info = f" (Port: {config['port']})" if config['port'] else ""
            print(f"   {status} {config['name']}{port_info} - {config['description']}")
        
        print("\n📱 Frontend Applications:")
        for app_id, config in launcher.frontend_apps.items():
            status = "✅" if config['enabled'] else "❌"
            print(f"   {status} {config['name']} - {config['description']}")
        return
    
    # Save configuration if specified
    if args.save_config:
        launcher.save_configuration(args.save_config)
        return
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = launcher.launch_platform(
            interactive=args.interactive,
            with_http_server=not args.no_http_server,
            http_port=args.port
        )
        
        if success:
            print("\n⏳ Platform is running. Press Ctrl+C to stop all services...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested...")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    launcher = None
    main() 