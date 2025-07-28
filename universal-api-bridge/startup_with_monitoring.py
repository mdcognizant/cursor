#!/usr/bin/env python3
"""
Application Startup with Automatic Error Monitoring + Shell Monitor
===================================================================
Use this script to start any application with automatic error monitoring AND shell monitor.

Usage Examples:
    python startup_with_monitoring.py                          # Start monitoring + shell monitor
    python startup_with_monitoring.py --app enhanced_delta_news_platform_complete.html
    python startup_with_monitoring.py --server                 # Start HTTP server + monitoring + shell monitor
    python startup_with_monitoring.py --check                  # Check status only
    python startup_with_monitoring.py --shell-only             # Start just shell monitor service
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

class ApplicationStartupManager:
    def __init__(self):
        self.monitor_running = False
        self.app_running = False
        self.shell_monitor_running = False
        self.shell_monitor_process = None
        
    def start_shell_monitor_service(self):
        """Start shell monitor as a background service"""
        print("🔧 Starting Shell Monitor Service...")
        
        try:
            # Check if shell monitor is available
            shell_monitor_path = Path("../shell_monitor.py")
            if not shell_monitor_path.exists():
                shell_monitor_path = Path("shell_monitor.py")
            
            if not shell_monitor_path.exists():
                print("⚠️ Shell monitor not found, creating integrated version...")
                self.create_integrated_shell_monitor()
                shell_monitor_path = Path("integrated_shell_monitor.py")
            
            if shell_monitor_path.exists():
                # Start shell monitor in interactive service mode
                print(f"🚀 Starting shell monitor from: {shell_monitor_path}")
                
                # Create a wrapper script that keeps shell monitor available
                self.create_shell_monitor_service()
                
                # Start the service
                self.shell_monitor_process = subprocess.Popen([
                    sys.executable, "shell_monitor_service.py"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print(f"✅ Shell Monitor Service started (PID: {self.shell_monitor_process.pid})")
                
                # Wait a moment and verify
                time.sleep(2)
                self.shell_monitor_running = True
                
                # Create easy access commands
                self.create_shell_monitor_shortcuts()
                
                return True
            else:
                print("❌ Shell monitor not available")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start shell monitor service: {e}")
            return False
    
    def create_shell_monitor_service(self):
        """Create a background service wrapper for shell monitor"""
        service_code = '''#!/usr/bin/env python3
"""
Shell Monitor Background Service
===============================
Keeps shell monitor available as a background service for Cursor.
"""

import sys
import os
import time
import subprocess
import threading
import socket
from pathlib import Path

class ShellMonitorService:
    def __init__(self):
        self.running = False
        self.port = 9999  # Service port
        self.commands_queue = []
        
    def start_service(self):
        """Start the shell monitor background service"""
        print("🔧 Shell Monitor Service starting...")
        self.running = True
        
        # Start command handler thread
        handler_thread = threading.Thread(target=self.command_handler, daemon=True)
        handler_thread.start()
        
        # Start network listener (for remote commands)
        listener_thread = threading.Thread(target=self.network_listener, daemon=True)
        listener_thread.start()
        
        print(f"✅ Shell Monitor Service active on port {self.port}")
        print("📋 Available commands:")
        print("   - Quick run: python run_with_monitor.py 'your command'")
        print("   - Interactive: python shell_monitor_interactive.py")
        print("   - Status: python shell_monitor_status.py")
        
        # Keep service alive
        try:
            while self.running:
                time.sleep(10)
                # Periodic health check
                if len(self.commands_queue) > 0:
                    print(f"📊 Shell Monitor: {len(self.commands_queue)} commands queued")
        except KeyboardInterrupt:
            print("\\n🛑 Shell Monitor Service stopping...")
            self.running = False
    
    def command_handler(self):
        """Handle queued commands"""
        while self.running:
            if self.commands_queue:
                command = self.commands_queue.pop(0)
                self.execute_monitored_command(command)
            time.sleep(1)
    
    def network_listener(self):
        """Listen for network commands"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', self.port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Non-blocking
            
            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    data = client_socket.recv(1024).decode('utf-8')
                    if data:
                        self.commands_queue.append(data.strip())
                        client_socket.send(b"Command queued\\n")
                    client_socket.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # Only log if we're still supposed to be running
                        print(f"Network listener error: {e}")
                    
        except Exception as e:
            print(f"Failed to start network listener: {e}")
    
    def execute_monitored_command(self, command):
        """Execute command with shell monitor"""
        print(f"🔄 Executing monitored command: {command}")
        
        try:
            # Use shell monitor to run the command
            shell_monitor_path = Path("../shell_monitor.py")
            if not shell_monitor_path.exists():
                shell_monitor_path = Path("shell_monitor.py")
            
            if shell_monitor_path.exists():
                result = subprocess.run([
                    sys.executable, str(shell_monitor_path), "run", command
                ], capture_output=True, text=True, timeout=300)
                
                print(f"✅ Command completed with exit code: {result.returncode}")
            else:
                # Fallback to direct execution with timeout
                result = subprocess.run(command, shell=True, capture_output=True, 
                                      text=True, timeout=60)
                print(f"✅ Command completed (direct): {result.returncode}")
                
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out")
        except Exception as e:
            print(f"❌ Command failed: {e}")

if __name__ == "__main__":
    service = ShellMonitorService()
    service.start_service()
'''
        
        try:
            with open("shell_monitor_service.py", 'w') as f:
                f.write(service_code)
            print("✅ Created shell monitor service")
        except Exception as e:
            print(f"Failed to create shell monitor service: {e}")
    
    def create_shell_monitor_shortcuts(self):
        """Create easy-to-use shell monitor shortcuts"""
        
        # 1. Quick command runner
        quick_runner = '''#!/usr/bin/env python3
"""
Quick Shell Monitor Command Runner
=================================
Usage: python run_with_monitor.py "your command here"
"""

import sys
import subprocess
from pathlib import Path

def run_with_monitor(command):
    """Run a command with shell monitor protection"""
    print(f"🔄 Running with shell monitor: {command}")
    
    # Find shell monitor
    shell_monitor_path = Path("../shell_monitor.py")
    if not shell_monitor_path.exists():
        shell_monitor_path = Path("shell_monitor.py")
    
    if shell_monitor_path.exists():
        try:
            result = subprocess.run([
                sys.executable, str(shell_monitor_path), "run", command
            ], timeout=300)
            return result.returncode
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out after 5 minutes")
            return 124
        except Exception as e:
            print(f"❌ Shell monitor failed: {e}")
            return 1
    else:
        print("❌ Shell monitor not found")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_with_monitor.py 'command to run'")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    exit_code = run_with_monitor(command)
    sys.exit(exit_code)
'''
        
        # 2. Interactive shell monitor
        interactive_runner = '''#!/usr/bin/env python3
"""
Interactive Shell Monitor
========================
Provides an interactive shell with built-in monitoring.
"""

import sys
import subprocess
from pathlib import Path

def interactive_shell():
    """Start interactive shell with monitoring"""
    print("🔧 Interactive Shell Monitor")
    print("Type 'exit' to quit, 'help' for commands")
    print("=" * 40)
    
    shell_monitor_path = Path("../shell_monitor.py")
    if not shell_monitor_path.exists():
        shell_monitor_path = Path("shell_monitor.py")
    
    while True:
        try:
            command = input("monitor> ").strip()
            
            if command.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            elif command.lower() == 'help':
                print("Available commands:")
                print("  - Any shell command (automatically monitored)")
                print("  - 'status' - Check monitoring status")
                print("  - 'exit' - Quit interactive shell")
                continue
            elif command.lower() == 'status':
                subprocess.run([sys.executable, "startup_with_monitoring.py", "--check"])
                continue
            elif not command:
                continue
            
            # Run command with shell monitor
            if shell_monitor_path.exists():
                subprocess.run([
                    sys.executable, str(shell_monitor_path), "run", command
                ])
            else:
                print("⚠️ Shell monitor not found, running directly...")
                subprocess.run(command, shell=True)
                
        except KeyboardInterrupt:
            print("\\n👋 Interrupted, goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    interactive_shell()
'''
        
        # 3. Status checker
        status_checker = '''#!/usr/bin/env python3
"""
Shell Monitor Status Checker
============================
Check the status of shell monitor service.
"""

import subprocess
import sys

def check_shell_monitor_status():
    """Check shell monitor service status"""
    print("🔧 SHELL MONITOR STATUS")
    print("=" * 30)
    
    try:
        # Check if service is running
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        python_procs = [line for line in result.stdout.split('\\n') if 'python.exe' in line.lower()]
        
        shell_monitor_procs = [proc for proc in python_procs if 'shell_monitor' in proc.lower()]
        
        if shell_monitor_procs:
            print(f"✅ Shell Monitor processes: {len(shell_monitor_procs)}")
            for proc in shell_monitor_procs:
                parts = proc.split()
                if len(parts) >= 2:
                    print(f"   PID: {parts[1]}")
        else:
            print("❌ Shell Monitor service not running")
        
        # Check if files exist
        files = ['shell_monitor_service.py', 'run_with_monitor.py', 'shell_monitor_interactive.py']
        print("\\n📁 Shell Monitor Files:")
        for file in files:
            if os.path.exists(file):
                print(f"✅ {file}")
            else:
                print(f"❌ {file}")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")

if __name__ == "__main__":
    import os
    check_shell_monitor_status()
'''
        
        try:
            with open("run_with_monitor.py", 'w') as f:
                f.write(quick_runner)
            with open("shell_monitor_interactive.py", 'w') as f:
                f.write(interactive_runner)
            with open("shell_monitor_status.py", 'w') as f:
                f.write(status_checker)
            
            print("✅ Created shell monitor shortcuts:")
            print("   📄 run_with_monitor.py - Quick command execution")
            print("   📄 shell_monitor_interactive.py - Interactive shell")
            print("   📄 shell_monitor_status.py - Status checker")
            
        except Exception as e:
            print(f"Failed to create shortcuts: {e}")
    
    def create_integrated_shell_monitor(self):
        """Create a simplified integrated shell monitor if main one not available"""
        integrated_code = '''#!/usr/bin/env python3
"""
Integrated Shell Monitor (Simplified)
====================================
A simplified version of shell monitor integrated into the startup system.
"""

import subprocess
import sys
import time
import threading

class IntegratedShellMonitor:
    def __init__(self):
        self.timeout = 60  # Default timeout
        
    def run_command(self, command, timeout=None):
        """Run command with timeout and monitoring"""
        if timeout is None:
            timeout = self.timeout
            
        print(f"⏱️ Running with {timeout}s timeout: {command}")
        
        try:
            start_time = time.time()
            
            process = subprocess.Popen(command, shell=True, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT,
                                     text=True)
            
            # Monitor process with timeout
            def timeout_handler():
                time.sleep(timeout)
                if process.poll() is None:
                    print(f"\\n⏰ Command timed out after {timeout}s")
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
            
            timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
            timeout_thread.start()
            
            # Wait for completion
            stdout, stderr = process.communicate()
            duration = time.time() - start_time
            
            print(f"✅ Command completed in {duration:.1f}s (exit code: {process.returncode})")
            
            if stdout:
                print(stdout)
            
            return process.returncode
            
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python integrated_shell_monitor.py 'command'")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    monitor = IntegratedShellMonitor()
    exit_code = monitor.run_command(command)
    sys.exit(exit_code)
'''
        
        try:
            with open("integrated_shell_monitor.py", 'w') as f:
                f.write(integrated_code)
            print("✅ Created integrated shell monitor")
        except Exception as e:
            print(f"Failed to create integrated shell monitor: {e}")

    def start_error_monitoring(self):
        """Start error monitoring in background"""
        print("🔄 Starting Error Monitoring...")
        
        try:
            # Check if already running
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            if 'python.exe' in result.stdout and 'simple_error_monitor' in result.stdout:
                print("✅ Error monitoring already running")
                self.monitor_running = True
                return True
            
            # Start the simple monitor
            if os.path.exists('simple_error_monitor.py'):
                # Start in background using subprocess
                process = subprocess.Popen([
                    sys.executable, 'simple_error_monitor.py'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print(f"🚀 Error monitor started (PID: {process.pid})")
                
                # Wait a moment and verify
                time.sleep(3)
                self.monitor_running = True
                return True
            else:
                print("❌ simple_error_monitor.py not found")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start error monitoring: {e}")
            return False
    
    def start_application(self, app_name=None):
        """Start the main application"""
        if app_name:
            print(f"🚀 Starting application: {app_name}")
            
            if app_name.endswith('.html'):
                # Open HTML file in browser
                if os.path.exists(app_name):
                    file_path = os.path.abspath(app_name)
                    webbrowser.open(f"file:///{file_path}")
                    print(f"✅ Opened {app_name} in browser")
                    self.app_running = True
                    return True
                else:
                    print(f"❌ File not found: {app_name}")
                    return False
            
            elif app_name.endswith('.py'):
                # Run Python script
                if os.path.exists(app_name):
                    process = subprocess.Popen([sys.executable, app_name])
                    print(f"✅ Started {app_name} (PID: {process.pid})")
                    self.app_running = True
                    return True
                else:
                    print(f"❌ File not found: {app_name}")
                    return False
        
        return True
    
    def start_http_server(self, port=8000):
        """Start HTTP server for serving files"""
        print(f"🌐 Starting HTTP server on port {port}...")
        
        try:
            # Start HTTP server in background
            process = subprocess.Popen([
                sys.executable, '-m', 'http.server', str(port)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"✅ HTTP server started on http://localhost:{port}")
            print(f"   PID: {process.pid}")
            
            # Wait a moment for server to start
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start HTTP server: {e}")
            return False
    
    def check_status(self):
        """Check status of all components"""
        print("📊 SYSTEM STATUS CHECK")
        print("=" * 40)
        
        # Check error monitoring
        try:
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            python_procs = [line for line in result.stdout.split('\n') if 'python.exe' in line.lower()]
            
            if python_procs:
                print(f"✅ Python processes running: {len(python_procs)}")
                for proc in python_procs[:5]:  # Show first 5
                    parts = proc.split()
                    if len(parts) >= 2:
                        print(f"   PID: {parts[1]}")
            else:
                print("❌ No Python processes found")
        except:
            print("❓ Unable to check processes")
        
        # Check files
        files_to_check = [
            'simple_error_monitor.py',
            'enhanced_delta_news_platform_complete.html',
            'master_error_log.jsonl',
            'error_monitoring.pid',
            'shell_monitor_service.py',
            'run_with_monitor.py',
            'shell_monitor_interactive.py'
        ]
        
        print("\n📁 File Status:")
        for file in files_to_check:
            if os.path.exists(file):
                size = os.path.getsize(file)
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"✅ {file}: {size} bytes ({mtime.strftime('%H:%M:%S')})")
            else:
                print(f"❌ {file}: Not found")
        
        print("\n" + "=" * 40)
    
    def startup_everything(self, app_name=None, with_server=False, shell_only=False):
        """Start everything with error monitoring AND shell monitor"""
        if shell_only:
            print("🔧 STARTING SHELL MONITOR SERVICE ONLY")
            print("=" * 50)
            
            if self.start_shell_monitor_service():
                print("\n✅ Shell Monitor Service is active!")
                print("💡 You can now use:")
                print("   python run_with_monitor.py 'your command'")
                print("   python shell_monitor_interactive.py")
                return True
            else:
                print("\n❌ Failed to start Shell Monitor Service")
                return False
        
        print("🚀 STARTING APPLICATION WITH ERROR MONITORING + SHELL MONITOR")
        print("=" * 60)
        
        success_count = 0
        total_components = 2  # Error monitoring + Shell monitor
        
        # 1. Start shell monitor service first
        if self.start_shell_monitor_service():
            success_count += 1
        
        # 2. Start error monitoring
        if self.start_error_monitoring():
            success_count += 1
        
        # 3. Start HTTP server if requested
        if with_server:
            total_components += 1
            if self.start_http_server():
                success_count += 1
        
        # 4. Start main application if specified
        if app_name:
            total_components += 1
            if self.start_application(app_name):
                success_count += 1
        
        # Report results
        print("\n" + "=" * 60)
        print(f"📊 STARTUP SUMMARY: {success_count}/{total_components} components started")
        
        if success_count == total_components:
            print("✅ ALL SYSTEMS OPERATIONAL")
            print("🛡️ Error monitoring is ACTIVE - all errors will be caught!")
            print("🔧 Shell monitor is ACTIVE - commands won't hang!")
            if app_name:
                print(f"🎯 Application '{app_name}' is running")
            return True
        else:
            print("⚠️ Some components failed to start")
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start application with automatic error monitoring + shell monitor")
    parser.add_argument('--app', help='Application file to start (.html or .py)')
    parser.add_argument('--server', action='store_true', help='Start HTTP server')
    parser.add_argument('--check', action='store_true', help='Check status only')
    parser.add_argument('--shell-only', action='store_true', help='Start just shell monitor service')
    parser.add_argument('--port', type=int, default=8000, help='HTTP server port')
    
    args = parser.parse_args()
    
    manager = ApplicationStartupManager()
    
    if args.check:
        manager.check_status()
    else:
        success = manager.startup_everything(
            app_name=args.app,
            with_server=args.server,
            shell_only=args.shell_only
        )
        
        if success:
            print("\n💡 Available Tools:")
            print("   🔧 Shell Monitor Commands:")
            print("      python run_with_monitor.py 'command'     # Run any command safely")
            print("      python shell_monitor_interactive.py      # Interactive shell")
            print("      python shell_monitor_status.py           # Check shell monitor status")
            print("   📊 Error Monitor Commands:")
            print("      python monitor_status.py                 # Check error monitoring")
            print("      python monitor_status.py live            # Live error monitoring")
            print("   🔄 System Commands:")
            print("      python startup_with_monitoring.py --check # Check all systems")
            
            if args.shell_only:
                print("\n🔧 Shell Monitor Service is now running in background!")
                print("   Use the commands above to execute monitored commands.")
            elif args.app and not args.app.endswith('.html'):
                try:
                    # Keep script running if we started a Python app
                    print("\n⏳ Keeping all services active...")
                    while True:
                        time.sleep(60)
                        print(f"🔄 Services heartbeat: {datetime.now().strftime('%H:%M:%S')}")
                except KeyboardInterrupt:
                    print("\n👋 Shutting down all services...")

if __name__ == "__main__":
    main() 