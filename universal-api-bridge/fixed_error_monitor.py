#!/usr/bin/env python3
"""
Fixed Error Monitor - Robust Version
====================================
A robust error monitoring system that handles all exceptions gracefully.
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
        logging.FileHandler('fixed_error_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedErrorMonitor:
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
            'start_time': None,
            'last_report': None
        }
        
        # Error patterns to detect
        self.error_patterns = {
            'critical': [r'critical', r'fatal', r'emergency'],
            'error': [r'error', r'exception', r'failed', r'failure'],
            'warning': [r'warning', r'warn'],
            'api_error': [r'connection refused', r'timeout', r'404', r'500', r'503'],
            'ssl_error': [r'ssl', r'certificate', r'handshake']
        }

    def start_monitoring(self):
        """Start the robust error monitoring"""
        logger.info("🚀 Starting Fixed Error Monitor...")
        self.running = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        try:
            # Initialize master log
            self.initialize_master_log()
            
            # Start monitoring in separate threads with exception handling
            threads = [
                threading.Thread(target=self.safe_monitor_log_files, daemon=True),
                threading.Thread(target=self.safe_monitor_api_status, daemon=True),
                threading.Thread(target=self.safe_periodic_reporting, daemon=True)
            ]
            
            for thread in threads:
                thread.start()
                logger.info(f"✅ Started thread: {thread.name}")
            
            logger.info("✅ All monitoring threads started successfully")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping monitor...")
            self.running = False
            self.generate_final_report()
        except Exception as e:
            logger.error(f"❌ Critical error in main monitoring: {e}")
            self.running = False

    def safe_monitor_log_files(self):
        """Safely monitor log files with exception handling"""
        try:
            logger.info("📝 Starting log file monitoring...")
            
            while self.running:
                try:
                    self.discover_log_files()
                    
                    for file_path in list(self.monitored_files):
                        try:
                            if os.path.exists(file_path):
                                self.check_file_for_errors(file_path)
                        except Exception as e:
                            logger.error(f"Error checking file {file_path}: {e}")
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error in log monitoring cycle: {e}")
                    time.sleep(10)
                    
        except Exception as e:
            logger.error(f"Fatal error in log file monitoring: {e}")

    def safe_monitor_api_status(self):
        """Safely monitor API status with exception handling"""
        try:
            logger.info("🌐 Starting API monitoring...")
            
            api_endpoints = [
                "http://localhost:8889/health",
                "http://localhost:8888/health",
                "http://localhost:8000"
            ]
            
            while self.running:
                try:
                    for endpoint in api_endpoints:
                        try:
                            self.check_local_api_health(endpoint)
                        except Exception as e:
                            logger.error(f"Error checking API {endpoint}: {e}")
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error in API monitoring cycle: {e}")
                    time.sleep(30)
                    
        except Exception as e:
            logger.error(f"Fatal error in API monitoring: {e}")

    def safe_periodic_reporting(self):
        """Safely generate periodic reports with exception handling"""
        try:
            logger.info("📊 Starting periodic reporting...")
            
            while self.running:
                try:
                    # Generate report every hour
                    time.sleep(3600)
                    
                    if self.running:
                        self.generate_hourly_report()
                    
                except Exception as e:
                    logger.error(f"Error in periodic reporting: {e}")
                    time.sleep(300)  # Wait 5 minutes before retry
                    
        except Exception as e:
            logger.error(f"Fatal error in periodic reporting: {e}")

    def initialize_master_log(self):
        """Initialize the master error log"""
        try:
            header = f"""
# Fixed Error Monitor Log
# Started: {datetime.now().isoformat()}
# Format: [TIMESTAMP] [SEVERITY] [TYPE] MESSAGE
# ================================================

"""
            with open(self.master_log_file, 'w') as f:
                f.write(header)
            
            logger.info(f"📝 Initialized master log: {self.master_log_file}")
            
        except Exception as e:
            logger.error(f"Failed to initialize master log: {e}")

    def write_to_master_log(self, severity, error_type, message):
        """Write error to master log"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] [{severity}] [{error_type}] {message}\n"
            
            with open(self.master_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"Failed to write to master log: {e}")

    def discover_log_files(self):
        """Discover log files to monitor"""
        try:
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
                    logger.error(f"Error discovering files with pattern {pattern}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in file discovery: {e}")

    def check_file_for_errors(self, file_path):
        """Check a file for new errors"""
        try:
            if not os.path.exists(file_path):
                return
                
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
        try:
            lines = content.split('\n')
            
            for line_no, line in enumerate(lines):
                if line.strip():  # Skip empty lines
                    for error_type, patterns in self.error_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                self.process_detected_error(error_type, line.strip(), source)
                                break
                                
        except Exception as e:
            logger.error(f"Error analyzing content from {source}: {e}")

    def process_detected_error(self, error_type, message, source):
        """Process a detected error"""
        try:
            # Generate unique error ID
            error_id = hashlib.md5(f"{error_type}:{message}".encode()).hexdigest()[:8]
            
            current_time = datetime.now().isoformat()
            
            if error_id in self.error_database:
                self.error_database[error_id]['count'] += 1
                self.error_database[error_id]['last_seen'] = current_time
            else:
                self.error_database[error_id] = {
                    'type': error_type,
                    'message': message,
                    'source': source,
                    'first_seen': current_time,
                    'last_seen': current_time,
                    'count': 1,
                    'fixed': False
                }
                
                # Write to master log
                self.write_to_master_log(error_type.upper(), 'DETECTED', f"{source}: {message}")
                
            self.stats['total_errors'] += 1
            
        except Exception as e:
            logger.error(f"Error processing detected error: {e}")

    def check_local_api_health(self, endpoint):
        """Check local API endpoint health"""
        try:
            import urllib.request
            import urllib.error
            
            start_time = time.time()
            
            try:
                request = urllib.request.Request(endpoint)
                request.add_header('User-Agent', 'FixedErrorMonitor/1.0')
                
                response = urllib.request.urlopen(request, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                if response.status != 200:
                    self.write_to_master_log('HIGH', 'API_ERROR', f"API {endpoint} returned status {response.status}")
                elif response_time > 2000:
                    self.write_to_master_log('MEDIUM', 'PERFORMANCE', f"API {endpoint} slow response: {response_time:.0f}ms")
                else:
                    logger.debug(f"✅ API {endpoint} healthy ({response_time:.0f}ms)")
                    
            except urllib.error.HTTPError as e:
                self.write_to_master_log('HIGH', 'API_ERROR', f"API {endpoint} HTTP error: {e.code}")
            except urllib.error.URLError as e:
                # This is expected for some endpoints, just log as debug
                logger.debug(f"API {endpoint} connection error: {e}")
            except Exception as e:
                logger.debug(f"API {endpoint} check error: {e}")
                
        except Exception as e:
            logger.error(f"Error in API health check: {e}")

    def generate_hourly_report(self):
        """Generate hourly error report"""
        try:
            current_time = datetime.now()
            
            # Count recent errors (last hour)
            hour_ago = current_time - timedelta(hours=1)
            recent_errors = [
                error for error in self.error_database.values()
                if datetime.fromisoformat(error['last_seen']) > hour_ago
            ]
            
            report = {
                'timestamp': current_time.isoformat(),
                'period': 'hourly',
                'recent_errors': len(recent_errors),
                'total_errors': self.stats['total_errors'],
                'unique_errors': len(self.error_database),
                'monitored_files': len(self.monitored_files)
            }
            
            report_file = f"error_report_{current_time.strftime('%Y%m%d_%H')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📊 Generated hourly report: {len(recent_errors)} recent errors")
            
        except Exception as e:
            logger.error(f"Error generating hourly report: {e}")

    def generate_final_report(self):
        """Generate final report"""
        try:
            final_report = {
                'shutdown_time': datetime.now().isoformat(),
                'start_time': self.stats['start_time'],
                'statistics': self.stats,
                'total_unique_errors': len(self.error_database),
                'monitored_files': len(self.monitored_files)
            }
            
            with open('final_error_report.json', 'w') as f:
                json.dump(final_report, f, indent=2, default=str)
            
            logger.info("📋 Generated final error report")
            
        except Exception as e:
            logger.error(f"Error generating final report: {e}")

def main():
    """Main entry point"""
    print("""
🔄 Fixed Error Monitor
======================
✅ Robust exception handling
✅ Real-time error detection
✅ Safe threading implementation
✅ Centralized error logging
✅ Local API health monitoring

Starting monitor...
""")
    
    try:
        monitor = FixedErrorMonitor()
        monitor.start_monitoring()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        print(f"❌ Monitor failed to start: {e}")

if __name__ == "__main__":
    main() 