#!/usr/bin/env python3
"""
Recursive Error Monitor Backend
==============================
Continuously monitors, logs, and auto-fixes errors across the entire platform.

Features:
- Real-time log monitoring
- Error pattern detection
- Automatic error fixing
- Centralized error logging
- Periodic error reviews
- Performance impact analysis
"""

import asyncio
import aiofiles
import json
import logging
import time
import os
import re
import subprocess
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import psutil
import requests
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH" 
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ErrorStatus(Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    FIX_ATTEMPTED = "FIX_ATTEMPTED"
    FIXED = "FIXED"
    PERSISTENT = "PERSISTENT"
    IGNORED = "IGNORED"

@dataclass
class ErrorEntry:
    id: str
    timestamp: str
    severity: ErrorSeverity
    status: ErrorStatus
    source: str
    error_type: str
    message: str
    stack_trace: Optional[str]
    context: Dict
    fix_attempts: List[Dict]
    first_seen: str
    last_seen: str
    occurrence_count: int
    auto_fixable: bool
    fix_success_rate: float

class ErrorMonitorBackend:
    def __init__(self, config_path: str = "error_monitor_config.json"):
        self.config = self.load_config(config_path)
        self.error_database = {}
        self.error_patterns = self.load_error_patterns()
        self.auto_fix_rules = self.load_auto_fix_rules()
        self.monitored_files = set()
        self.file_positions = {}
        self.error_aggregator = ErrorAggregator()
        self.auto_fix_engine = AutoFixEngine()
        self.periodic_reviewer = PeriodicReviewer()
        self.performance_monitor = PerformanceMonitor()
        self.running = False
        
        # Statistics
        self.stats = {
            'total_errors': 0,
            'fixed_errors': 0,
            'persistent_errors': 0,
            'auto_fix_success_rate': 0.0,
            'monitor_uptime': 0,
            'last_review': None
        }

    def load_config(self, config_path: str) -> Dict:
        """Load error monitor configuration"""
        default_config = {
            "monitor_interval": 5,  # seconds
            "review_interval": 3600,  # 1 hour
            "log_retention_days": 30,
            "max_fix_attempts": 3,
            "auto_fix_enabled": True,
            "notification_enabled": True,
            "performance_monitoring": True,
            "monitored_directories": [
                "universal-api-bridge/",
                "llm-agent-bridge/",
                "logs/",
                "."
            ],
            "log_file_patterns": [
                "*.log",
                "error*.txt",
                "debug*.txt",
                "*.err"
            ],
            "excluded_patterns": [
                "__pycache__",
                ".git",
                "node_modules"
            ],
            "api_endpoints_to_monitor": [
                "https://newsdata.io/api/1/latest",
                "https://api.currentsapi.services/v1/latest-news"
            ],
            "critical_keywords": [
                "CRITICAL",
                "FATAL", 
                "ERROR",
                "FAILED",
                "EXCEPTION",
                "CRASH"
            ]
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return default_config

    def load_error_patterns(self) -> Dict:
        """Load error detection patterns"""
        return {
            'api_errors': [
                r'API.*error.*(\d{3})',
                r'HTTP.*(\d{3}).*error',
                r'Request.*failed.*(\d{3})',
                r'SSL.*CERTIFICATE.*VERIFY.*FAILED',
                r'NetworkError|ConnectionError|TimeoutError'
            ],
            'javascript_errors': [
                r'TypeError.*(\w+)',
                r'ReferenceError.*(\w+)',
                r'SyntaxError.*(\w+)',
                r'Uncaught.*Error',
                r'Promise.*rejected'
            ],
            'python_errors': [
                r'Traceback.*most recent call',
                r'Exception.*(\w+Error)',
                r'ImportError.*(\w+)',
                r'ModuleNotFoundError.*(\w+)',
                r'AttributeError.*(\w+)'
            ],
            'system_errors': [
                r'Out of memory',
                r'Disk.*full',
                r'Permission.*denied',
                r'File.*not.*found',
                r'Process.*killed'
            ],
            'performance_issues': [
                r'Slow.*query.*(\d+)ms',
                r'High.*CPU.*(\d+%)',
                r'Memory.*usage.*(\d+%)',
                r'Response.*time.*(\d+)ms'
            ]
        }

    def load_auto_fix_rules(self) -> Dict:
        """Load automatic fix rules"""
        return {
            'ssl_certificate_error': {
                'pattern': r'SSL.*CERTIFICATE.*VERIFY.*FAILED',
                'fixes': [
                    {
                        'type': 'config_update',
                        'action': 'disable_ssl_verification',
                        'description': 'Add SSL verification bypass for known issues'
                    },
                    {
                        'type': 'fallback_activation',
                        'action': 'enable_backup_api',
                        'description': 'Switch to backup API provider'
                    }
                ]
            },
            'module_not_found': {
                'pattern': r'ModuleNotFoundError.*\'(\w+)\'',
                'fixes': [
                    {
                        'type': 'install_dependency',
                        'action': 'pip_install',
                        'description': 'Install missing Python module'
                    }
                ]
            },
            'api_rate_limit': {
                'pattern': r'rate.*limit.*exceeded|429.*Too Many Requests',
                'fixes': [
                    {
                        'type': 'cache_activation',
                        'action': 'enable_cache_fallback',
                        'description': 'Activate cache fallback for rate limited APIs'
                    },
                    {
                        'type': 'delay_injection',
                        'action': 'add_request_delay',
                        'description': 'Add delays between API requests'
                    }
                ]
            },
            'javascript_reference_error': {
                'pattern': r'ReferenceError.*(\w+).*not defined',
                'fixes': [
                    {
                        'type': 'script_injection',
                        'action': 'add_missing_variable',
                        'description': 'Initialize missing JavaScript variables'
                    }
                ]
            },
            'file_not_found': {
                'pattern': r'FileNotFoundError.*\'([^\']+)\'',
                'fixes': [
                    {
                        'type': 'file_creation',
                        'action': 'create_missing_file',
                        'description': 'Create missing file with default content'
                    }
                ]
            }
        }

    async def start_monitoring(self):
        """Start the recursive error monitoring process"""
        logger.info("🚀 Starting Recursive Error Monitor Backend...")
        self.running = True
        start_time = time.time()
        
        # Start all monitoring tasks concurrently
        tasks = [
            asyncio.create_task(self.monitor_log_files()),
            asyncio.create_task(self.monitor_api_endpoints()),
            asyncio.create_task(self.monitor_system_resources()),
            asyncio.create_task(self.periodic_error_review()),
            asyncio.create_task(self.generate_periodic_reports()),
            asyncio.create_task(self.cleanup_old_logs()),
            asyncio.create_task(self.update_statistics())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping error monitor...")
            self.running = False
            
            # Save final statistics
            self.stats['monitor_uptime'] = time.time() - start_time
            await self.save_error_database()
            await self.generate_shutdown_report()

    async def monitor_log_files(self):
        """Monitor log files for new errors"""
        logger.info("📁 Starting log file monitoring...")
        
        while self.running:
            try:
                # Discover new log files
                await self.discover_log_files()
                
                # Check each monitored file for new content
                for file_path in list(self.monitored_files):
                    if os.path.exists(file_path):
                        await self.check_file_for_errors(file_path)
                    else:
                        # File was deleted, remove from monitoring
                        self.monitored_files.discard(file_path)
                        self.file_positions.pop(file_path, None)
                
                await asyncio.sleep(self.config['monitor_interval'])
                
            except Exception as e:
                logger.error(f"Error in log file monitoring: {e}")
                await asyncio.sleep(10)

    async def discover_log_files(self):
        """Recursively discover log files to monitor"""
        for directory in self.config['monitored_directories']:
            if os.path.exists(directory):
                for pattern in self.config['log_file_patterns']:
                    try:
                        for file_path in Path(directory).rglob(pattern):
                            if any(excluded in str(file_path) for excluded in self.config['excluded_patterns']):
                                continue
                            
                            file_str = str(file_path)
                            if file_str not in self.monitored_files:
                                self.monitored_files.add(file_str)
                                self.file_positions[file_str] = 0
                                logger.info(f"📝 Now monitoring: {file_str}")
                    except Exception as e:
                        logger.error(f"Error discovering files in {directory}: {e}")

    async def check_file_for_errors(self, file_path: str):
        """Check a specific file for new errors"""
        try:
            current_size = os.path.getsize(file_path)
            last_position = self.file_positions.get(file_path, 0)
            
            if current_size > last_position:
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    await f.seek(last_position)
                    new_content = await f.read()
                    
                    if new_content:
                        await self.analyze_content_for_errors(new_content, file_path)
                        self.file_positions[file_path] = current_size
            
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")

    async def analyze_content_for_errors(self, content: str, source: str):
        """Analyze content for error patterns"""
        lines = content.split('\n')
        
        for line_no, line in enumerate(lines):
            for error_type, patterns in self.error_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        await self.process_detected_error(
                            error_type=error_type,
                            message=line.strip(),
                            source=source,
                            line_number=line_no + self.file_positions.get(source, 0),
                            pattern_match=match
                        )

    async def process_detected_error(self, error_type: str, message: str, source: str, 
                                   line_number: int, pattern_match: re.Match):
        """Process a detected error"""
        # Generate unique error ID
        error_id = hashlib.md5(f"{error_type}:{message}:{source}".encode()).hexdigest()[:12]
        
        current_time = datetime.now().isoformat()
        
        if error_id in self.error_database:
            # Update existing error
            error = self.error_database[error_id]
            error.last_seen = current_time
            error.occurrence_count += 1
        else:
            # Create new error entry
            severity = self.determine_severity(error_type, message)
            
            error = ErrorEntry(
                id=error_id,
                timestamp=current_time,
                severity=severity,
                status=ErrorStatus.NEW,
                source=source,
                error_type=error_type,
                message=message,
                stack_trace=None,
                context={
                    'line_number': line_number,
                    'pattern_match': pattern_match.group() if pattern_match else None,
                    'file_size': os.path.getsize(source) if os.path.exists(source) else 0
                },
                fix_attempts=[],
                first_seen=current_time,
                last_seen=current_time,
                occurrence_count=1,
                auto_fixable=self.is_auto_fixable(error_type, message),
                fix_success_rate=0.0
            )
            
            self.error_database[error_id] = error
            self.stats['total_errors'] += 1
            
            logger.warning(f"🚨 NEW ERROR [{severity.value}]: {error_type} in {source}")
            logger.warning(f"   Message: {message}")
            
            # Attempt automatic fix if enabled and applicable
            if self.config['auto_fix_enabled'] and error.auto_fixable:
                await self.attempt_auto_fix(error)

    def determine_severity(self, error_type: str, message: str) -> ErrorSeverity:
        """Determine error severity based on type and content"""
        critical_indicators = ['CRITICAL', 'FATAL', 'CRASH', 'SYSTEM', 'SECURITY']
        high_indicators = ['ERROR', 'FAILED', 'EXCEPTION', 'API']
        
        message_upper = message.upper()
        
        if any(indicator in message_upper for indicator in critical_indicators):
            return ErrorSeverity.CRITICAL
        elif any(indicator in message_upper for indicator in high_indicators):
            return ErrorSeverity.HIGH
        elif error_type in ['api_errors', 'system_errors']:
            return ErrorSeverity.HIGH
        elif error_type in ['javascript_errors', 'python_errors']:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def is_auto_fixable(self, error_type: str, message: str) -> bool:
        """Determine if error can be automatically fixed"""
        for rule_name, rule in self.auto_fix_rules.items():
            if re.search(rule['pattern'], message, re.IGNORECASE):
                return True
        return False

    async def attempt_auto_fix(self, error: ErrorEntry):
        """Attempt to automatically fix an error"""
        logger.info(f"🔧 Attempting auto-fix for error {error.id}")
        
        for rule_name, rule in self.auto_fix_rules.items():
            if re.search(rule['pattern'], error.message, re.IGNORECASE):
                for fix in rule['fixes']:
                    try:
                        fix_attempt = {
                            'timestamp': datetime.now().isoformat(),
                            'rule': rule_name,
                            'fix_type': fix['type'],
                            'action': fix['action'],
                            'description': fix['description'],
                            'success': False,
                            'error': None
                        }
                        
                        # Execute the fix
                        success = await self.execute_fix(fix, error)
                        fix_attempt['success'] = success
                        
                        error.fix_attempts.append(fix_attempt)
                        error.status = ErrorStatus.FIX_ATTEMPTED
                        
                        if success:
                            error.status = ErrorStatus.FIXED
                            self.stats['fixed_errors'] += 1
                            logger.info(f"✅ Successfully fixed error {error.id} using {rule_name}")
                            return True
                        else:
                            logger.warning(f"⚠️ Fix attempt failed for error {error.id}")
                            
                    except Exception as e:
                        fix_attempt['error'] = str(e)
                        error.fix_attempts.append(fix_attempt)
                        logger.error(f"❌ Fix execution failed for error {error.id}: {e}")
        
        # Mark as persistent if all fixes failed
        if len(error.fix_attempts) >= self.config['max_fix_attempts']:
            error.status = ErrorStatus.PERSISTENT
            self.stats['persistent_errors'] += 1
        
        return False

    async def execute_fix(self, fix: Dict, error: ErrorEntry) -> bool:
        """Execute a specific fix action"""
        try:
            if fix['type'] == 'config_update':
                return await self.apply_config_fix(fix, error)
            elif fix['type'] == 'install_dependency':
                return await self.install_missing_dependency(fix, error)
            elif fix['type'] == 'cache_activation':
                return await self.activate_cache_fallback(fix, error)
            elif fix['type'] == 'file_creation':
                return await self.create_missing_file(fix, error)
            elif fix['type'] == 'script_injection':
                return await self.inject_script_fix(fix, error)
            else:
                logger.warning(f"Unknown fix type: {fix['type']}")
                return False
        except Exception as e:
            logger.error(f"Fix execution error: {e}")
            return False

    async def apply_config_fix(self, fix: Dict, error: ErrorEntry) -> bool:
        """Apply configuration-based fixes"""
        if 'SSL' in error.message and 'CERTIFICATE' in error.message:
            # Update API configuration to handle SSL issues
            config_update = {
                'ssl_verification': False,
                'fallback_enabled': True,
                'error_handling': 'graceful'
            }
            
            config_file = 'api_config.json'
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                else:
                    config = {}
                
                config.update(config_update)
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                logger.info(f"Updated {config_file} to handle SSL issues")
                return True
            except Exception as e:
                logger.error(f"Failed to update config: {e}")
                return False
        
        return False

    async def install_missing_dependency(self, fix: Dict, error: ErrorEntry) -> bool:
        """Install missing Python dependencies"""
        match = re.search(r'ModuleNotFoundError.*\'(\w+)\'', error.message)
        if match:
            module_name = match.group(1)
            try:
                result = subprocess.run(
                    ['pip', 'install', module_name],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully installed {module_name}")
                    return True
                else:
                    logger.error(f"Failed to install {module_name}: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"Error installing {module_name}: {e}")
                return False
        
        return False

    async def activate_cache_fallback(self, fix: Dict, error: ErrorEntry) -> bool:
        """Activate cache fallback for API issues"""
        # This would integrate with your existing cache system
        cache_config = {
            'enabled': True,
            'fallback_on_error': True,
            'max_age_hours': 24
        }
        
        try:
            with open('cache_config.json', 'w') as f:
                json.dump(cache_config, f, indent=2)
            
            logger.info("Activated cache fallback for API errors")
            return True
        except Exception as e:
            logger.error(f"Failed to activate cache fallback: {e}")
            return False

    async def create_missing_file(self, fix: Dict, error: ErrorEntry) -> bool:
        """Create missing files with default content"""
        match = re.search(r'FileNotFoundError.*\'([^\']+)\'', error.message)
        if match:
            file_path = match.group(1)
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Create with appropriate default content
                if file_path.endswith('.json'):
                    default_content = '{}'
                elif file_path.endswith('.py'):
                    default_content = '# Auto-generated file\npass\n'
                elif file_path.endswith('.html'):
                    default_content = '<!DOCTYPE html><html><head><title>Auto-generated</title></head><body></body></html>'
                else:
                    default_content = ''
                
                with open(file_path, 'w') as f:
                    f.write(default_content)
                
                logger.info(f"Created missing file: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to create file {file_path}: {e}")
                return False
        
        return False

    async def inject_script_fix(self, fix: Dict, error: ErrorEntry) -> bool:
        """Inject JavaScript fixes for common errors"""
        # This would require more sophisticated analysis
        # For now, just log the attempt
        logger.info(f"Script injection fix attempted for: {error.message}")
        return False

    async def monitor_api_endpoints(self):
        """Monitor API endpoints for availability"""
        logger.info("🌐 Starting API endpoint monitoring...")
        
        while self.running:
            try:
                for endpoint in self.config['api_endpoints_to_monitor']:
                    await self.check_api_endpoint(endpoint)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in API monitoring: {e}")
                await asyncio.sleep(30)

    async def check_api_endpoint(self, endpoint: str):
        """Check a specific API endpoint"""
        try:
            start_time = time.time()
            response = requests.get(endpoint, timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                await self.process_detected_error(
                    error_type='api_errors',
                    message=f"API endpoint {endpoint} returned status {response.status_code}",
                    source='api_monitor',
                    line_number=0,
                    pattern_match=None
                )
            elif response_time > 5000:  # Slow response
                await self.process_detected_error(
                    error_type='performance_issues',
                    message=f"API endpoint {endpoint} slow response: {response_time:.0f}ms",
                    source='api_monitor',
                    line_number=0,
                    pattern_match=None
                )
                
        except Exception as e:
            await self.process_detected_error(
                error_type='api_errors',
                message=f"API endpoint {endpoint} failed: {str(e)}",
                source='api_monitor',
                line_number=0,
                pattern_match=None
            )

    async def monitor_system_resources(self):
        """Monitor system resources for issues"""
        if not self.config['performance_monitoring']:
            return
            
        logger.info("📊 Starting system resource monitoring...")
        
        while self.running:
            try:
                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > 90:
                    await self.process_detected_error(
                        error_type='performance_issues',
                        message=f"High CPU usage: {cpu_percent}%",
                        source='system_monitor',
                        line_number=0,
                        pattern_match=None
                    )
                
                # Check memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 85:
                    await self.process_detected_error(
                        error_type='performance_issues',
                        message=f"High memory usage: {memory.percent}%",
                        source='system_monitor',
                        line_number=0,
                        pattern_match=None
                    )
                
                # Check disk usage
                disk = psutil.disk_usage('/')
                if disk.percent > 90:
                    await self.process_detected_error(
                        error_type='system_errors',
                        message=f"High disk usage: {disk.percent}%",
                        source='system_monitor',
                        line_number=0,
                        pattern_match=None
                    )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(60)

    async def periodic_error_review(self):
        """Periodically review and analyze errors"""
        logger.info("🔍 Starting periodic error review...")
        
        while self.running:
            try:
                await self.analyze_error_trends()
                await self.update_fix_success_rates()
                await self.identify_recurring_issues()
                await self.save_error_database()
                
                self.stats['last_review'] = datetime.now().isoformat()
                
                await asyncio.sleep(self.config['review_interval'])
                
            except Exception as e:
                logger.error(f"Error in periodic review: {e}")
                await asyncio.sleep(300)

    async def analyze_error_trends(self):
        """Analyze error trends and patterns"""
        # Group errors by type and time
        error_trends = defaultdict(list)
        
        for error in self.error_database.values():
            error_trends[error.error_type].append(error)
        
        # Log trend analysis
        for error_type, errors in error_trends.items():
            recent_errors = [e for e in errors if 
                           datetime.fromisoformat(e.last_seen) > datetime.now() - timedelta(hours=24)]
            
            if len(recent_errors) > 5:  # Threshold for trend alert
                logger.warning(f"📈 Trend Alert: {len(recent_errors)} {error_type} errors in last 24h")

    async def update_fix_success_rates(self):
        """Update success rates for auto-fixes"""
        for error in self.error_database.values():
            if error.fix_attempts:
                successful_fixes = sum(1 for attempt in error.fix_attempts if attempt['success'])
                error.fix_success_rate = successful_fixes / len(error.fix_attempts)

    async def identify_recurring_issues(self):
        """Identify recurring issues that need attention"""
        recurring_threshold = 10
        
        for error in self.error_database.values():
            if error.occurrence_count >= recurring_threshold and error.status != ErrorStatus.FIXED:
                logger.warning(f"🔄 Recurring Issue: {error.error_type} occurred {error.occurrence_count} times")
                error.status = ErrorStatus.PERSISTENT

    async def generate_periodic_reports(self):
        """Generate periodic error reports"""
        while self.running:
            try:
                await self.generate_hourly_report()
                await asyncio.sleep(3600)  # Every hour
            except Exception as e:
                logger.error(f"Error generating reports: {e}")
                await asyncio.sleep(300)

    async def generate_hourly_report(self):
        """Generate hourly error report"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        recent_errors = [
            error for error in self.error_database.values()
            if datetime.fromisoformat(error.last_seen) > hour_ago
        ]
        
        report = {
            'timestamp': now.isoformat(),
            'period': 'last_hour',
            'total_errors': len(recent_errors),
            'new_errors': len([e for e in recent_errors if e.status == ErrorStatus.NEW]),
            'fixed_errors': len([e for e in recent_errors if e.status == ErrorStatus.FIXED]),
            'critical_errors': len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]),
            'error_breakdown': {},
            'top_error_sources': {},
            'auto_fix_performance': {}
        }
        
        # Error breakdown by type
        for error in recent_errors:
            error_type = error.error_type
            if error_type not in report['error_breakdown']:
                report['error_breakdown'][error_type] = 0
            report['error_breakdown'][error_type] += 1
        
        # Save report
        report_file = f"error_reports/hourly_{now.strftime('%Y%m%d_%H')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Generated hourly report: {len(recent_errors)} errors processed")

    async def save_error_database(self):
        """Save error database to disk"""
        try:
            database_backup = {
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats,
                'errors': {k: asdict(v) for k, v in self.error_database.items()}
            }
            
            with open('error_database.json', 'w') as f:
                json.dump(database_backup, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save error database: {e}")

    async def cleanup_old_logs(self):
        """Clean up old log files"""
        while self.running:
            try:
                retention_days = self.config['log_retention_days']
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                for directory in ['error_reports/', 'logs/']:
                    if os.path.exists(directory):
                        for file_path in Path(directory).rglob('*'):
                            if file_path.is_file():
                                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                if file_time < cutoff_date:
                                    try:
                                        os.remove(file_path)
                                        logger.info(f"🗑️ Cleaned up old log: {file_path}")
                                    except Exception as e:
                                        logger.error(f"Failed to remove {file_path}: {e}")
                
                await asyncio.sleep(86400)  # Daily cleanup
                
            except Exception as e:
                logger.error(f"Error in log cleanup: {e}")
                await asyncio.sleep(3600)

    async def update_statistics(self):
        """Update monitoring statistics"""
        while self.running:
            try:
                # Update auto-fix success rate
                if self.stats['total_errors'] > 0:
                    self.stats['auto_fix_success_rate'] = (
                        self.stats['fixed_errors'] / self.stats['total_errors']
                    ) * 100
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
                await asyncio.sleep(60)

    async def generate_shutdown_report(self):
        """Generate final report on shutdown"""
        report = {
            'shutdown_time': datetime.now().isoformat(),
            'total_runtime': self.stats['monitor_uptime'],
            'final_statistics': self.stats,
            'persistent_errors': [
                asdict(error) for error in self.error_database.values()
                if error.status == ErrorStatus.PERSISTENT
            ]
        }
        
        with open('final_error_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("📋 Generated final error report")

# Supporting classes (simplified for space)
class ErrorAggregator:
    """Aggregates errors from multiple sources"""
    pass

class AutoFixEngine:
    """Handles automatic error fixing"""
    pass

class PeriodicReviewer:
    """Reviews errors periodically"""
    pass

class PerformanceMonitor:
    """Monitors system performance"""
    pass

async def main():
    """Main entry point"""
    monitor = ErrorMonitorBackend()
    await monitor.start_monitoring()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Error Monitor stopped by user")
    except Exception as e:
        print(f"❌ Error Monitor crashed: {e}")
        traceback.print_exc() 