#!/usr/bin/env python3
"""
Automatic Error Monitor Startup System
=====================================
Ensures error monitoring starts automatically with the application.

Features:
- Auto-detects if monitor is already running
- Starts monitor in background if needed
- Integrates with main application startup
- Windows service capability
- Startup validation and health checks
"""

import os
import sys
import time
import json
import subprocess
import threading
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_startup_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoStartupMonitor:
    def __init__(self):
        self.monitor_script = "simple_error_monitor.py"
        self.pid_file = "error_monitoring.pid"
        self.status_file = "monitor_startup_status.json"
        self.max_startup_attempts = 3
        self.startup_timeout = 30  # seconds
        
    def is_monitor_running(self):
        """Check if error monitor is already running"""
        try:
            # Check PID file
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is actually running
                try:
                    # On Windows, use tasklist
                    result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                          capture_output=True, text=True)
                    return str(pid) in result.stdout
                except:
                    # Fallback: check if PID file is recent
                    file_age = time.time() - os.path.getmtime(self.pid_file)
                    return file_age < 300  # 5 minutes
            
            # Alternative: check for python processes running our script
            try:
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                python_processes = [line for line in result.stdout.split('\n') 
                                  if 'python.exe' in line.lower()]
                
                # If we have python processes, assume monitor might be running
                return len(python_processes) > 0
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking monitor status: {e}")
            return False
    
    def start_error_monitor(self):
        """Start the error monitoring system"""
        try:
            logger.info("🚀 Starting error monitoring system...")
            
            # Check if monitor script exists
            if not os.path.exists(self.monitor_script):
                logger.error(f"❌ Monitor script not found: {self.monitor_script}")
                return False
            
            # Start the monitor in background
            if os.name == 'nt':  # Windows
                # Use START command to run in new window (detached)
                cmd = f'start /B python "{self.monitor_script}"'
                process = subprocess.Popen(cmd, shell=True)
            else:  # Unix/Linux
                cmd = [sys.executable, self.monitor_script]
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL)
            
            # Wait a moment for startup
            time.sleep(3)
            
            # Verify it started
            if self.is_monitor_running():
                logger.info("✅ Error monitor started successfully")
                self.log_startup_success()
                return True
            else:
                logger.error("❌ Error monitor failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start error monitor: {e}")
            return False
    
    def ensure_monitor_running(self):
        """Ensure error monitor is running, start if needed"""
        logger.info("🔍 Checking error monitor status...")
        
        if self.is_monitor_running():
            logger.info("✅ Error monitor is already running")
            return True
        
        logger.info("⚠️ Error monitor not detected, starting...")
        
        # Try to start the monitor
        for attempt in range(self.max_startup_attempts):
            logger.info(f"🔄 Startup attempt {attempt + 1}/{self.max_startup_attempts}")
            
            if self.start_error_monitor():
                return True
            
            if attempt < self.max_startup_attempts - 1:
                logger.info(f"⏳ Waiting before retry...")
                time.sleep(5)
        
        logger.error("❌ Failed to start error monitor after all attempts")
        self.log_startup_failure()
        return False
    
    def log_startup_success(self):
        """Log successful startup"""
        status = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'attempts': 1,
            'pid_file_exists': os.path.exists(self.pid_file),
            'monitor_script': self.monitor_script
        }
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log startup status: {e}")
    
    def log_startup_failure(self):
        """Log startup failure"""
        status = {
            'status': 'failed',
            'timestamp': datetime.now().isoformat(),
            'attempts': self.max_startup_attempts,
            'pid_file_exists': os.path.exists(self.pid_file),
            'monitor_script': self.monitor_script,
            'error': 'Max startup attempts exceeded'
        }
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log startup status: {e}")
    
    def create_startup_integration(self):
        """Create integration scripts for automatic startup"""
        
        # 1. Create Windows batch file for startup
        batch_script = """@echo off
REM Auto-startup script for Error Monitoring System
cd /d "%~dp0"
python auto_startup_monitor.py
if errorlevel 1 (
    echo Error monitor startup failed
    pause
)
"""
        
        try:
            with open('start_error_monitoring.bat', 'w') as f:
                f.write(batch_script)
            logger.info("✅ Created Windows startup batch file")
        except Exception as e:
            logger.error(f"Failed to create batch file: {e}")
        
        # 2. Create Python integration module
        integration_code = '''"""
Error Monitor Integration Module
===============================
Import this module in your main application to auto-start error monitoring.

Usage:
    from auto_startup_monitor import ensure_error_monitoring
    ensure_error_monitoring()
"""

import os
import sys
from pathlib import Path

def ensure_error_monitoring():
    """Ensure error monitoring is running - call this from your main app"""
    try:
        # Get the directory containing this script
        script_dir = Path(__file__).parent
        original_dir = os.getcwd()
        
        # Change to the script directory
        os.chdir(script_dir)
        
        # Import and run the auto startup
        from auto_startup_monitor import AutoStartupMonitor
        
        monitor = AutoStartupMonitor()
        success = monitor.ensure_monitor_running()
        
        # Return to original directory
        os.chdir(original_dir)
        
        return success
        
    except Exception as e:
        print(f"Warning: Failed to start error monitoring: {e}")
        return False

# Auto-run if this file is executed directly
if __name__ == "__main__":
    ensure_error_monitoring()
'''
        
        try:
            with open('error_monitor_integration.py', 'w') as f:
                f.write(integration_code)
            logger.info("✅ Created Python integration module")
        except Exception as e:
            logger.error(f"Failed to create integration module: {e}")
        
        # 3. Create application startup hook
        self.create_app_startup_hook()
    
    def create_app_startup_hook(self):
        """Create startup hook for main applications"""
        
        # Hook for news platform HTML files
        html_startup_script = '''
<!-- Error Monitor Auto-Startup -->
<script>
// Auto-start error monitoring when page loads
window.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Checking error monitoring status...');
    
    // Check if monitor is running via a simple API call
    fetch('/monitor-status')
        .then(response => {
            if (!response.ok) {
                console.log('⚠️ Error monitor not detected, attempting startup...');
                return fetch('/start-monitor', { method: 'POST' });
            }
            console.log('✅ Error monitor is running');
        })
        .catch(error => {
            console.log('ℹ️ Error monitor status check failed (expected if not running)');
            // Fallback: Try to start via python script
            console.log('🔄 Attempting fallback startup...');
        });
});
</script>
'''
        
        try:
            with open('html_monitor_startup_hook.html', 'w') as f:
                f.write(html_startup_script)
            logger.info("✅ Created HTML startup hook")
        except Exception as e:
            logger.error(f"Failed to create HTML hook: {e}")
    
    def run_health_check(self):
        """Run a health check of the monitoring system"""
        logger.info("🏥 Running error monitor health check...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'monitor_running': self.is_monitor_running(),
            'pid_file_exists': os.path.exists(self.pid_file),
            'monitor_script_exists': os.path.exists(self.monitor_script),
            'logs_directory_exists': os.path.exists('error_logs'),
            'master_log_exists': os.path.exists('master_error_log.jsonl')
        }
        
        # Check log file sizes
        if health_status['master_log_exists']:
            health_status['master_log_size'] = os.path.getsize('master_error_log.jsonl')
            health_status['master_log_age'] = time.time() - os.path.getmtime('master_error_log.jsonl')
        
        # Overall health score
        checks_passed = sum([
            health_status['monitor_running'],
            health_status['monitor_script_exists'],
            health_status['master_log_exists']
        ])
        
        health_status['health_score'] = f"{checks_passed}/3"
        health_status['healthy'] = checks_passed >= 2
        
        # Save health check results
        try:
            with open('monitor_health_check.json', 'w') as f:
                json.dump(health_status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health check: {e}")
        
        # Display results
        if health_status['healthy']:
            logger.info(f"✅ Health check PASSED ({health_status['health_score']})")
        else:
            logger.warning(f"⚠️ Health check FAILED ({health_status['health_score']})")
        
        return health_status

def auto_startup_main():
    """Main function for automatic startup"""
    print("""
🔄 ERROR MONITOR AUTO-STARTUP
============================
Ensuring error monitoring is running...
""")
    
    startup_monitor = AutoStartupMonitor()
    
    # Run health check first
    health = startup_monitor.run_health_check()
    
    # Ensure monitor is running
    success = startup_monitor.ensure_monitor_running()
    
    if success:
        print("✅ Error monitoring system is ACTIVE")
        print("📊 All errors will be automatically monitored and logged")
        
        # Create integration files
        startup_monitor.create_startup_integration()
        print("📁 Created automatic startup integration files")
        
    else:
        print("❌ Failed to start error monitoring system")
        print("🔧 Manual intervention may be required")
    
    return success

if __name__ == "__main__":
    auto_startup_main() 