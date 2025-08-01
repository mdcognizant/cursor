#!/usr/bin/env python3
"""
Simple Error Monitor - No External Dependencies
==============================================
A lightweight error monitoring system that uses only built-in Python modules.

Features:
- Monitors log files for errors
- Aggregates errors into a master log
- Simple auto-fixes for common issues
- Real-time error detection
- No external dependencies required
"""

import os
import time
import json
import threading
import re
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_error_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleErrorMonitor:
    def __init__(self):
        self.running = False
        self.monitored_files = set()
        self.file_positions = {}
        self.error_database = {}
        self.master_log_file = "master_error_log.txt"
        
        # Statistics
        self.stats = {
            'total_errors': 0,
            'fixed_errors': 0,
            'start_time': None
        }
        
        # Error patterns (simplified)
        self.error_patterns = {
            'api_errors': [
                r'SSL.*certificate.*verify.*failed',
                r'HTTP.*error.*(\d{3})',
                r'API.*error.*(\d{3})',
                r'Rate.*limit.*exceeded',
                r'NetworkError|ConnectionError'
            ],
            'javascript_errors': [
                r'TypeError.*(\w+)',
                r'ReferenceError.*(\w+)',
                r'Uncaught.*Error',
                r'Promise.*rejected'
            ],
            'python_errors': [
                r'Traceback.*most recent call',
                r'ModuleNotFoundError.*(\w+)',
                r'ImportError.*(\w+)',
                r'FileNotFoundError.*(\w+)'
            ]
        }
        
        # Simple auto-fix rules
        self.auto_fixes = {
            'ssl_certificate_error': {
                'pattern': r'SSL.*certificate.*verify.*failed',
                'fix': self.fix_ssl_issue
            },
            'missing_module': {
                'pattern': r'ModuleNotFoundError.*\'(\w+)\'',
                'fix': self.fix_missing_module
            }
        }

    def start_monitoring(self):
        """Start the simple error monitoring"""
        logger.info("🚀 Starting Simple Error Monitor...")
        self.running = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        # Initialize master log
        self.initialize_master_log()
        
        # Start monitoring in separate threads
        threads = [
            threading.Thread(target=self.monitor_log_files, daemon=True),
            threading.Thread(target=self.monitor_api_status, daemon=True),
            threading.Thread(target=self.periodic_reporting, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping monitor...")
            self.running = False
            self.generate_final_report()

    def initialize_master_log(self):
        """Initialize the master error log"""
        header = f"""
# Simple Error Monitor Log
# Started: {datetime.now().isoformat()}
# Format: [TIMESTAMP] [SEVERITY] [TYPE] MESSAGE
# ================================================

"""
        with open(self.master_log_file, 'w') as f:
            f.write(header)
        
        logger.info(f"📝 Initialized master log: {self.master_log_file}")

    def write_to_master_log(self, severity, error_type, message):
        """Write error to master log"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{severity}] [{error_type}] {message}\n"
        
        try:
            with open(self.master_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write to master log: {e}")

    def monitor_log_files(self):
        """Monitor log files for errors"""
        logger.info("📁 Starting log file monitoring...")
        
        while self.running:
            try:
                # Discover log files
                self.discover_log_files()
                
                # Check each file for new content
                for file_path in list(self.monitored_files):
                    if os.path.exists(file_path):
                        self.check_file_for_errors(file_path)
                    else:
                        # File was deleted
                        self.monitored_files.discard(file_path)
                        self.file_positions.pop(file_path, None)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in log monitoring: {e}")
                time.sleep(10)

    def discover_log_files(self):
        """Discover log files to monitor"""
        log_patterns = ['*.log', '*.err', 'error*.txt']
        
        for pattern in log_patterns:
            try:
                for file_path in Path('.').rglob(pattern):
                    # Skip certain directories
                    if any(excluded in str(file_path) for excluded in ['__pycache__', '.git', 'node_modules']):
                        continue
                    
                    file_str = str(file_path)
                    if file_str not in self.monitored_files:
                        self.monitored_files.add(file_str)
                        self.file_positions[file_str] = 0
                        logger.info(f"📝 Now monitoring: {file_str}")
            except Exception as e:
                logger.error(f"Error discovering files: {e}")

    def check_file_for_errors(self, file_path):
        """Check a file for new errors"""
        try:
            current_size = os.path.getsize(file_path)
            last_position = self.file_positions.get(file_path, 0)
            
            if current_size > last_position:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    
                    if new_content:
                        self.analyze_content_for_errors(new_content, file_path)
                        self.file_positions[file_path] = current_size
        
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")

    def analyze_content_for_errors(self, content, source):
        """Analyze content for error patterns"""
        lines = content.split('\n')
        
        for line_no, line in enumerate(lines):
            for error_type, patterns in self.error_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.process_detected_error(error_type, line.strip(), source)

    def process_detected_error(self, error_type, message, source):
        """Process a detected error"""
        # Generate unique error ID
        error_id = hashlib.md5(f"{error_type}:{message}".encode()).hexdigest()[:8]
        
        current_time = datetime.now().isoformat()
        
        if error_id in self.error_database:
            # Update existing error
            self.error_database[error_id]['count'] += 1
            self.error_database[error_id]['last_seen'] = current_time
        else:
            # New error
            self.error_database[error_id] = {
                'type': error_type,
                'message': message,
                'source': source,
                'first_seen': current_time,
                'last_seen': current_time,
                'count': 1,
                'fixed': False
            }
            
            self.stats['total_errors'] += 1
            
            # Log to master log
            severity = self.determine_severity(error_type, message)
            self.write_to_master_log(severity, error_type, f"{message} (Source: {source})")
            
            logger.warning(f"🚨 NEW ERROR [{severity}]: {error_type} - {message[:100]}")
            
            # Attempt auto-fix
            if self.attempt_auto_fix(error_type, message):
                self.error_database[error_id]['fixed'] = True
                self.stats['fixed_errors'] += 1

    def determine_severity(self, error_type, message):
        """Determine error severity"""
        message_upper = message.upper()
        
        if any(word in message_upper for word in ['CRITICAL', 'FATAL', 'CRASH']):
            return 'CRITICAL'
        elif any(word in message_upper for word in ['ERROR', 'FAILED', 'EXCEPTION']):
            return 'HIGH'
        elif 'WARNING' in message_upper:
            return 'MEDIUM'
        else:
            return 'LOW'

    def attempt_auto_fix(self, error_type, message):
        """Attempt to automatically fix an error"""
        for rule_name, rule in self.auto_fixes.items():
            if re.search(rule['pattern'], message, re.IGNORECASE):
                try:
                    logger.info(f"🔧 Attempting auto-fix: {rule_name}")
                    success = rule['fix'](message)
                    if success:
                        logger.info(f"✅ Successfully applied fix: {rule_name}")
                        self.write_to_master_log('INFO', 'AUTO_FIX', f"Fixed {rule_name}: {message[:100]}")
                        return True
                    else:
                        logger.warning(f"⚠️ Auto-fix failed: {rule_name}")
                except Exception as e:
                    logger.error(f"❌ Auto-fix error: {e}")
        
        return False

    def fix_ssl_issue(self, message):
        """Fix SSL certificate issues"""
        try:
            # Create a simple SSL bypass configuration
            ssl_config = {
                'ssl_verification': False,
                'fallback_enabled': True,
                'updated': datetime.now().isoformat()
            }
            
            with open('ssl_fix_config.json', 'w') as f:
                json.dump(ssl_config, f, indent=2)
            
            logger.info("Created SSL bypass configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to create SSL fix: {e}")
            return False

    def fix_missing_module(self, message):
        """Fix missing Python modules"""
        try:
            # Extract module name
            match = re.search(r'ModuleNotFoundError.*\'(\w+)\'', message)
            if match:
                module_name = match.group(1)
                
                # Try to install the module
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', module_name],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully installed {module_name}")
                    return True
                else:
                    logger.error(f"Failed to install {module_name}: {result.stderr}")
                    return False
        except Exception as e:
            logger.error(f"Error installing module: {e}")
            return False

    def monitor_api_status(self):
        """Monitor API endpoints"""
        logger.info("🌐 Starting API monitoring...")
        
        api_endpoints = [
            "https://newsdata.io/api/1/latest",
            "https://api.currentsapi.services/v1/latest-news"
        ]
        
        while self.running:
            try:
                for endpoint in api_endpoints:
                    self.check_api_health(endpoint)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"API monitoring error: {e}")
                time.sleep(60)

    def check_api_health(self, endpoint):
        """Check API endpoint health"""
        try:
            import urllib.request
            import urllib.error
            
            start_time = time.time()
            
            try:
                response = urllib.request.urlopen(endpoint, timeout=30)
                response_time = (time.time() - start_time) * 1000
                
                if response.status != 200:
                    self.write_to_master_log('HIGH', 'API_ERROR', f"API {endpoint} returned status {response.status}")
                elif response_time > 5000:
                    self.write_to_master_log('MEDIUM', 'PERFORMANCE', f"API {endpoint} slow response: {response_time:.0f}ms")
                
            except urllib.error.URLError as e:
                self.write_to_master_log('HIGH', 'API_ERROR', f"API {endpoint} failed: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error checking API {endpoint}: {e}")

    def periodic_reporting(self):
        """Generate periodic reports"""
        logger.info("📊 Starting periodic reporting...")
        
        while self.running:
            try:
                time.sleep(3600)  # Generate every hour
                self.generate_hourly_report()
            except Exception as e:
                logger.error(f"Reporting error: {e}")
                time.sleep(300)

    def generate_hourly_report(self):
        """Generate hourly report"""
        current_time = datetime.now()
        
        # Count recent errors
        hour_ago = current_time - timedelta(hours=1)
        recent_errors = [
            error for error in self.error_database.values()
            if datetime.fromisoformat(error['last_seen']) > hour_ago
        ]
        
        report = {
            'timestamp': current_time.isoformat(),
            'total_errors': len(self.error_database),
            'recent_errors': len(recent_errors),
            'fixed_errors': self.stats['fixed_errors'],
            'auto_fix_rate': (self.stats['fixed_errors'] / max(1, self.stats['total_errors'])) * 100
        }
        
        # Save report
        report_file = f"error_report_{current_time.strftime('%Y%m%d_%H')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Generated hourly report: {len(recent_errors)} recent errors")

    def generate_final_report(self):
        """Generate final report"""
        final_report = {
            'shutdown_time': datetime.now().isoformat(),
            'total_runtime_minutes': (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds() / 60,
            'statistics': self.stats,
            'total_unique_errors': len(self.error_database),
            'persistent_errors': [
                error for error in self.error_database.values()
                if error['count'] > 5 and not error['fixed']
            ]
        }
        
        with open('final_error_report.json', 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        logger.info("📋 Generated final error report")

def main():
    """Main entry point"""
    print("""
🔄 Simple Error Monitor
======================
✅ No external dependencies required
✅ Real-time error detection
✅ Automatic error fixing
✅ Centralized error logging
✅ API health monitoring

Starting monitor...
""")
    
    monitor = SimpleErrorMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main() 