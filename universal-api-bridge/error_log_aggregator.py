#!/usr/bin/env python3
"""
Error Log Aggregator
===================
Aggregates all errors from various sources into a single master error log.

Features:
- Collects from multiple log sources
- Standardizes error format
- Provides real-time aggregation
- Creates searchable error database
- Generates summary reports
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import re
import hashlib
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AggregatedError:
    """Standardized error entry for the master log"""
    id: str
    timestamp: str
    severity: str
    source_type: str
    source_file: str
    error_type: str
    message: str
    stack_trace: Optional[str]
    context: Dict
    fix_applied: bool
    fix_success: bool
    occurrence_count: int
    first_occurrence: str
    last_occurrence: str
    tags: List[str]

class ErrorLogAggregator:
    def __init__(self, config_file: str = "error_monitor_config.json"):
        self.config = self.load_config(config_file)
        self.master_log_file = "master_error_log.jsonl"
        self.error_database = {}
        self.source_monitors = {}
        self.running = False
        
        # Statistics
        self.stats = {
            'total_errors_aggregated': 0,
            'errors_by_severity': defaultdict(int),
            'errors_by_source': defaultdict(int),
            'errors_by_type': defaultdict(int),
            'start_time': None,
            'last_aggregation': None
        }

    def load_config(self, config_file: str) -> Dict:
        """Load configuration for error aggregation"""
        default_config = {
            "master_log_rotation": True,
            "max_log_size_mb": 50,
            "aggregation_interval": 10,
            "error_deduplication": True,
            "include_stack_traces": True,
            "compress_old_logs": True,
            "real_time_monitoring": True
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
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

    async def start_aggregation(self):
        """Start the error aggregation process"""
        logger.info("🔄 Starting Error Log Aggregation...")
        self.running = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        # Initialize master log file
        await self.initialize_master_log()
        
        # Start aggregation tasks
        tasks = [
            asyncio.create_task(self.monitor_browser_console_logs()),
            asyncio.create_task(self.monitor_python_logs()),
            asyncio.create_task(self.monitor_system_logs()),
            asyncio.create_task(self.monitor_api_error_logs()),
            asyncio.create_task(self.monitor_application_logs()),
            asyncio.create_task(self.periodic_summary_generation()),
            asyncio.create_task(self.log_rotation_manager()),
            asyncio.create_task(self.real_time_error_processor())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping error aggregation...")
            self.running = False
            await self.generate_final_summary()

    async def initialize_master_log(self):
        """Initialize the master error log file"""
        # Create logs directory if it doesn't exist
        os.makedirs("error_logs", exist_ok=True)
        
        # Write header if file doesn't exist
        if not os.path.exists(self.master_log_file):
            header = {
                "log_type": "master_error_log",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "format": "jsonl",
                "description": "Aggregated error log from all platform sources"
            }
            
            await self.write_to_master_log(header, is_header=True)
            logger.info(f"📝 Initialized master error log: {self.master_log_file}")

    async def write_to_master_log(self, data: Dict, is_header: bool = False):
        """Write data to the master error log"""
        try:
            with open(self.master_log_file, 'a', encoding='utf-8') as f:
                if is_header:
                    f.write(f"# {json.dumps(data)}\n")
                else:
                    f.write(f"{json.dumps(data, default=str)}\n")
        except Exception as e:
            logger.error(f"Failed to write to master log: {e}")

    async def monitor_browser_console_logs(self):
        """Monitor browser console logs for JavaScript errors"""
        logger.info("🌐 Monitoring browser console logs...")
        
        # This would typically integrate with browser automation tools
        # For now, we'll monitor for files that might contain console errors
        console_log_patterns = [
            "*console*.log",
            "*browser*.log",
            "*javascript*.log",
            "*chrome*.log",
            "*firefox*.log"
        ]
        
        while self.running:
            try:
                for pattern in console_log_patterns:
                    for log_file in Path(".").rglob(pattern):
                        await self.process_browser_log_file(str(log_file))
                
                await asyncio.sleep(self.config['aggregation_interval'])
            except Exception as e:
                logger.error(f"Error monitoring browser logs: {e}")
                await asyncio.sleep(30)

    async def process_browser_log_file(self, file_path: str):
        """Process a browser log file for errors"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # JavaScript error patterns
                js_error_patterns = [
                    r'TypeError.*at.*line (\d+)',
                    r'ReferenceError.*(\w+) is not defined',
                    r'SyntaxError.*Unexpected token',
                    r'Uncaught.*Error.*at.*(\w+\.js):(\d+)',
                    r'Promise.*rejected.*(\w+)',
                    r'Network error.*failed to fetch',
                    r'CORS.*blocked.*request'
                ]
                
                for pattern in js_error_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        await self.aggregate_error(
                            source_type="browser_console",
                            source_file=file_path,
                            error_type="javascript_error",
                            message=match.group(0),
                            severity="HIGH",
                            context={"pattern": pattern, "line": match.start()}
                        )
        except Exception as e:
            logger.error(f"Error processing browser log {file_path}: {e}")

    async def monitor_python_logs(self):
        """Monitor Python application logs"""
        logger.info("🐍 Monitoring Python logs...")
        
        python_log_patterns = [
            "*.log",
            "*error*.txt",
            "*exception*.log",
            "traceback*.log"
        ]
        
        while self.running:
            try:
                for pattern in python_log_patterns:
                    for log_file in Path(".").rglob(pattern):
                        await self.process_python_log_file(str(log_file))
                
                await asyncio.sleep(self.config['aggregation_interval'])
            except Exception as e:
                logger.error(f"Error monitoring Python logs: {e}")
                await asyncio.sleep(30)

    async def process_python_log_file(self, file_path: str):
        """Process a Python log file for errors"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Python error patterns
                python_error_patterns = [
                    r'Traceback \(most recent call last\):(.*?)(?=\n\S|\Z)',
                    r'(.*Error): (.*)',
                    r'CRITICAL.*(\w+): (.*)',
                    r'ERROR.*(\w+): (.*)',
                    r'FATAL.*(\w+): (.*)'
                ]
                
                for pattern in python_error_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    for match in matches:
                        # Extract stack trace if it's a traceback
                        stack_trace = None
                        if "Traceback" in match.group(0):
                            stack_trace = match.group(0)
                        
                        await self.aggregate_error(
                            source_type="python_application",
                            source_file=file_path,
                            error_type="python_error",
                            message=match.group(0).split('\n')[0],  # First line
                            severity=self.determine_python_severity(match.group(0)),
                            context={"pattern": pattern},
                            stack_trace=stack_trace
                        )
        except Exception as e:
            logger.error(f"Error processing Python log {file_path}: {e}")

    def determine_python_severity(self, error_text: str) -> str:
        """Determine severity of Python errors"""
        error_upper = error_text.upper()
        
        if any(word in error_upper for word in ['CRITICAL', 'FATAL', 'SYSTEM']):
            return "CRITICAL"
        elif any(word in error_upper for word in ['ERROR', 'EXCEPTION', 'FAILED']):
            return "HIGH"
        elif any(word in error_upper for word in ['WARNING', 'WARN']):
            return "MEDIUM"
        else:
            return "LOW"

    async def monitor_system_logs(self):
        """Monitor system-level logs"""
        logger.info("🖥️ Monitoring system logs...")
        
        system_log_paths = [
            "/var/log/syslog",
            "/var/log/messages", 
            "/var/log/kern.log",
            "C:\\Windows\\System32\\winevt\\Logs\\System.evtx",  # Windows
            "C:\\Windows\\System32\\winevt\\Logs\\Application.evtx"  # Windows
        ]
        
        while self.running:
            try:
                for log_path in system_log_paths:
                    if os.path.exists(log_path):
                        await self.process_system_log_file(log_path)
                
                await asyncio.sleep(60)  # Check system logs less frequently
            except Exception as e:
                logger.error(f"Error monitoring system logs: {e}")
                await asyncio.sleep(60)

    async def process_system_log_file(self, file_path: str):
        """Process system log files (simplified for common text logs)"""
        try:
            if file_path.endswith('.evtx'):
                # Windows Event Log - would need special handling
                return
            
            if os.path.exists(file_path):
                # Only read last 1000 lines to avoid processing entire system logs
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                
                content = '\n'.join(recent_lines)
                
                # System error patterns
                system_error_patterns = [
                    r'kernel.*panic',
                    r'out of memory',
                    r'disk.*full',
                    r'failed.*mount',
                    r'permission.*denied',
                    r'service.*failed.*start'
                ]
                
                for pattern in system_error_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        await self.aggregate_error(
                            source_type="system",
                            source_file=file_path,
                            error_type="system_error",
                            message=match.group(0),
                            severity="CRITICAL",
                            context={"pattern": pattern}
                        )
        except Exception as e:
            logger.error(f"Error processing system log {file_path}: {e}")

    async def monitor_api_error_logs(self):
        """Monitor API-specific error logs"""
        logger.info("🌐 Monitoring API error logs...")
        
        api_log_patterns = [
            "*api*.log",
            "*request*.log",
            "*response*.log",
            "*http*.log"
        ]
        
        while self.running:
            try:
                for pattern in api_log_patterns:
                    for log_file in Path(".").rglob(pattern):
                        await self.process_api_log_file(str(log_file))
                
                await asyncio.sleep(self.config['aggregation_interval'])
            except Exception as e:
                logger.error(f"Error monitoring API logs: {e}")
                await asyncio.sleep(30)

    async def process_api_log_file(self, file_path: str):
        """Process API log files"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # API error patterns
                api_error_patterns = [
                    r'HTTP/\d\.\d" (4\d\d|5\d\d)',  # 4xx/5xx status codes
                    r'SSL.*certificate.*verify.*failed',
                    r'Connection.*timeout',
                    r'Rate.*limit.*exceeded',
                    r'API.*key.*invalid',
                    r'Authentication.*failed',
                    r'Request.*too.*large'
                ]
                
                for pattern in api_error_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        severity = "HIGH"
                        if "5" in match.group(0):  # 5xx errors are more severe
                            severity = "CRITICAL"
                        elif "4" in match.group(0):  # 4xx errors
                            severity = "MEDIUM"
                        
                        await self.aggregate_error(
                            source_type="api",
                            source_file=file_path,
                            error_type="api_error",
                            message=match.group(0),
                            severity=severity,
                            context={"pattern": pattern}
                        )
        except Exception as e:
            logger.error(f"Error processing API log {file_path}: {e}")

    async def monitor_application_logs(self):
        """Monitor application-specific logs"""
        logger.info("📱 Monitoring application logs...")
        
        app_log_patterns = [
            "*app*.log",
            "*application*.log",
            "*server*.log",
            "*debug*.log"
        ]
        
        while self.running:
            try:
                for pattern in app_log_patterns:
                    for log_file in Path(".").rglob(pattern):
                        await self.process_application_log_file(str(log_file))
                
                await asyncio.sleep(self.config['aggregation_interval'])
            except Exception as e:
                logger.error(f"Error monitoring application logs: {e}")
                await asyncio.sleep(30)

    async def process_application_log_file(self, file_path: str):
        """Process application log files"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Application error patterns
                app_error_patterns = [
                    r'ERROR.*(\w+).*: (.*)',
                    r'FATAL.*(\w+).*: (.*)',
                    r'Exception.*(\w+): (.*)',
                    r'Failed.*to.*(\w+): (.*)',
                    r'Unable.*to.*(\w+): (.*)'
                ]
                
                for pattern in app_error_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        await self.aggregate_error(
                            source_type="application",
                            source_file=file_path,
                            error_type="application_error",
                            message=match.group(0),
                            severity=self.determine_app_severity(match.group(0)),
                            context={"pattern": pattern}
                        )
        except Exception as e:
            logger.error(f"Error processing application log {file_path}: {e}")

    def determine_app_severity(self, error_text: str) -> str:
        """Determine severity of application errors"""
        error_upper = error_text.upper()
        
        if any(word in error_upper for word in ['FATAL', 'CRITICAL']):
            return "CRITICAL"
        elif any(word in error_upper for word in ['ERROR', 'EXCEPTION']):
            return "HIGH"
        elif any(word in error_upper for word in ['FAILED', 'UNABLE']):
            return "MEDIUM"
        else:
            return "LOW"

    async def aggregate_error(self, source_type: str, source_file: str, error_type: str, 
                            message: str, severity: str, context: Dict, stack_trace: Optional[str] = None):
        """Aggregate an error into the master log"""
        try:
            # Generate unique error ID
            error_content = f"{source_type}:{error_type}:{message}"
            error_id = hashlib.md5(error_content.encode()).hexdigest()[:12]
            
            current_time = datetime.now().isoformat()
            
            # Check if error already exists
            if error_id in self.error_database:
                # Update existing error
                existing_error = self.error_database[error_id]
                existing_error.occurrence_count += 1
                existing_error.last_occurrence = current_time
                
                # Update master log with occurrence
                await self.write_to_master_log({
                    "type": "error_occurrence",
                    "error_id": error_id,
                    "timestamp": current_time,
                    "occurrence_count": existing_error.occurrence_count
                })
            else:
                # Create new aggregated error
                aggregated_error = AggregatedError(
                    id=error_id,
                    timestamp=current_time,
                    severity=severity,
                    source_type=source_type,
                    source_file=source_file,
                    error_type=error_type,
                    message=message[:500],  # Limit message length
                    stack_trace=stack_trace[:1000] if stack_trace else None,  # Limit stack trace
                    context=context,
                    fix_applied=False,
                    fix_success=False,
                    occurrence_count=1,
                    first_occurrence=current_time,
                    last_occurrence=current_time,
                    tags=self.generate_error_tags(error_type, message)
                )
                
                self.error_database[error_id] = aggregated_error
                
                # Write to master log
                await self.write_to_master_log({
                    "type": "new_error",
                    **asdict(aggregated_error)
                })
                
                # Update statistics
                self.stats['total_errors_aggregated'] += 1
                self.stats['errors_by_severity'][severity] += 1
                self.stats['errors_by_source'][source_type] += 1
                self.stats['errors_by_type'][error_type] += 1
                self.stats['last_aggregation'] = current_time
                
                logger.info(f"📝 Aggregated new {severity} error: {error_type} from {source_type}")
        
        except Exception as e:
            logger.error(f"Failed to aggregate error: {e}")

    def generate_error_tags(self, error_type: str, message: str) -> List[str]:
        """Generate tags for error categorization"""
        tags = [error_type]
        
        message_lower = message.lower()
        
        # Add contextual tags
        if 'ssl' in message_lower or 'certificate' in message_lower:
            tags.append('ssl')
        if 'network' in message_lower or 'connection' in message_lower:
            tags.append('network')
        if 'memory' in message_lower:
            tags.append('memory')
        if 'disk' in message_lower or 'storage' in message_lower:
            tags.append('storage')
        if 'api' in message_lower:
            tags.append('api')
        if 'timeout' in message_lower:
            tags.append('timeout')
        if 'permission' in message_lower or 'access' in message_lower:
            tags.append('permission')
        
        return tags

    async def periodic_summary_generation(self):
        """Generate periodic summary reports"""
        while self.running:
            try:
                await self.generate_summary_report()
                await asyncio.sleep(3600)  # Generate every hour
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                await asyncio.sleep(300)

    async def generate_summary_report(self):
        """Generate an aggregated error summary report"""
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        
        # Filter recent errors
        recent_errors = [
            error for error in self.error_database.values()
            if datetime.fromisoformat(error.last_occurrence) > hour_ago
        ]
        
        summary = {
            "report_timestamp": current_time.isoformat(),
            "period": "last_hour",
            "total_unique_errors": len(self.error_database),
            "recent_errors": len(recent_errors),
            "aggregation_statistics": dict(self.stats),
            "error_breakdown": {
                "by_severity": dict(self.stats['errors_by_severity']),
                "by_source": dict(self.stats['errors_by_source']),
                "by_type": dict(self.stats['errors_by_type'])
            },
            "top_errors": [
                {
                    "id": error.id,
                    "message": error.message[:100],
                    "occurrence_count": error.occurrence_count,
                    "severity": error.severity,
                    "source_type": error.source_type
                }
                for error in sorted(recent_errors, key=lambda x: x.occurrence_count, reverse=True)[:10]
            ]
        }
        
        # Save summary report
        summary_file = f"error_summaries/summary_{current_time.strftime('%Y%m%d_%H')}.json"
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Also write to master log
        await self.write_to_master_log({
            "type": "hourly_summary",
            **summary
        })
        
        logger.info(f"📊 Generated hourly summary: {len(recent_errors)} recent errors")

    async def log_rotation_manager(self):
        """Manage log rotation to prevent files from getting too large"""
        while self.running:
            try:
                if os.path.exists(self.master_log_file):
                    file_size_mb = os.path.getsize(self.master_log_file) / (1024 * 1024)
                    
                    if file_size_mb > self.config['max_log_size_mb']:
                        # Rotate the log
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        rotated_file = f"error_logs/master_error_log_{timestamp}.jsonl"
                        
                        os.makedirs("error_logs", exist_ok=True)
                        os.rename(self.master_log_file, rotated_file)
                        
                        # Compress if enabled
                        if self.config['compress_old_logs']:
                            import gzip
                            with open(rotated_file, 'rb') as f_in:
                                with gzip.open(f"{rotated_file}.gz", 'wb') as f_out:
                                    f_out.writelines(f_in)
                            os.remove(rotated_file)
                        
                        # Reinitialize master log
                        await self.initialize_master_log()
                        
                        logger.info(f"🔄 Rotated master log file: {file_size_mb:.1f}MB")
                
                await asyncio.sleep(1800)  # Check every 30 minutes
            except Exception as e:
                logger.error(f"Error in log rotation: {e}")
                await asyncio.sleep(300)

    async def real_time_error_processor(self):
        """Process errors in real-time for immediate alerts"""
        while self.running:
            try:
                # Check for critical errors that need immediate attention
                critical_errors = [
                    error for error in self.error_database.values()
                    if error.severity == "CRITICAL" and not error.fix_applied
                ]
                
                for error in critical_errors:
                    logger.critical(f"🚨 CRITICAL ERROR DETECTED: {error.message[:100]}")
                    
                    # Here you could send notifications, trigger alerts, etc.
                    await self.send_critical_alert(error)
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in real-time processing: {e}")
                await asyncio.sleep(60)

    async def send_critical_alert(self, error: AggregatedError):
        """Send alerts for critical errors"""
        alert = {
            "type": "critical_error_alert",
            "timestamp": datetime.now().isoformat(),
            "error_id": error.id,
            "message": error.message,
            "source": error.source_file,
            "occurrence_count": error.occurrence_count
        }
        
        # Write alert to master log
        await self.write_to_master_log(alert)
        
        # Here you could integrate with notification services:
        # - Email notifications
        # - Slack/Discord webhooks
        # - SMS alerts
        # - PagerDuty/Opsgenie

    async def generate_final_summary(self):
        """Generate final summary when aggregation stops"""
        final_summary = {
            "aggregation_stopped": datetime.now().isoformat(),
            "total_runtime": (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds(),
            "final_statistics": dict(self.stats),
            "total_unique_errors": len(self.error_database),
            "persistent_errors": [
                asdict(error) for error in self.error_database.values()
                if error.occurrence_count > 5 and not error.fix_applied
            ]
        }
        
        with open("final_aggregation_summary.json", 'w') as f:
            json.dump(final_summary, f, indent=2, default=str)
        
        await self.write_to_master_log({
            "type": "aggregation_shutdown",
            **final_summary
        })
        
        logger.info("📋 Generated final aggregation summary")

async def main():
    """Main entry point for error log aggregator"""
    aggregator = ErrorLogAggregator()
    await aggregator.start_aggregation()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Error Log Aggregator stopped by user")
    except Exception as e:
        print(f"❌ Error Log Aggregator crashed: {e}")
        import traceback
        traceback.print_exc() 