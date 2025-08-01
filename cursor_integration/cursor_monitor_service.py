#!/usr/bin/env python3
"""
Cursor Shell Monitor Background Service
Monitors Cursor command executions and provides diagnostics.
"""

import time
import sys
import json
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shell_monitor.monitor import ShellMonitor
from src.shell_monitor.diagnostics import ShellDiagnostics

class CursorMonitorService:
    """Background service for monitoring Cursor commands."""
    
    def __init__(self):
        self.running = False
        self.config_file = Path.home() / ".cursor_monitor_config.json"
        self.log_file = Path.home() / ".cursor_monitor_service.log"
        
    def start(self):
        """Start the monitoring service."""
        self.running = True
        print("🚀 Cursor Monitor Service started")
        
        try:
            while self.running:
                time.sleep(30)  # Check every 30 seconds
                self._check_system_health()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the monitoring service."""
        self.running = False
        print("🛑 Cursor Monitor Service stopped")
    
    def _check_system_health(self):
        """Perform periodic system health checks."""
        try:
            # Run quick diagnostics
            diagnostics = ShellDiagnostics(verbose=False)
            results = diagnostics.run_full_diagnostic()
            
            # Log any warnings or failures
            issues = [r for r in results if r.status in ['warning', 'fail']]
            if issues:
                self._log_issues(issues)
                
        except Exception as e:
            self._log_error(f"Health check failed: {e}")
    
    def _log_issues(self, issues):
        """Log system issues."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] Issues detected:\n")
            for issue in issues:
                f.write(f"  - {issue.name}: {issue.message}\n")
            f.write("\n")
    
    def _log_error(self, error_msg):
        """Log errors."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] ERROR: {error_msg}\n")

if __name__ == "__main__":
    service = CursorMonitorService()
    try:
        service.start()
    except Exception as e:
        print(f"❌ Service failed: {e}")
        sys.exit(1)
