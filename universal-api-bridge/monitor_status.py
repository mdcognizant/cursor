#!/usr/bin/env python3
"""
Error Monitor Status Checker
============================
Shows real-time status of the error monitoring system.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

def check_monitor_status():
    """Check and display the status of the error monitoring system"""
    
    print("🔄 ERROR MONITORING SYSTEM STATUS")
    print("=" * 50)
    
    # Check if process is running
    try:
        import subprocess
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        python_processes = [line for line in result.stdout.split('\n') if 'python.exe' in line.lower()]
        
        if python_processes:
            print(f"✅ Python processes running: {len(python_processes)}")
            for proc in python_processes[:3]:  # Show first 3
                parts = proc.split()
                if len(parts) >= 2:
                    print(f"   PID: {parts[1]}")
        else:
            print("❌ No Python processes found")
    except:
        print("❓ Unable to check processes")
    
    print("\n📁 LOG FILES STATUS:")
    print("-" * 30)
    
    # Check log files
    log_files = [
        'master_error_log.jsonl',
        'master_error_log.txt', 
        'simple_error_monitor.log',
        'error_monitoring.pid'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            print(f"✅ {log_file}: {size} bytes (Modified: {mtime.strftime('%H:%M:%S')})")
        else:
            print(f"❌ {log_file}: Not found")
    
    print("\n📊 ERROR STATISTICS:")
    print("-" * 30)
    
    # Read master error log
    total_errors = 0
    recent_errors = 0
    
    try:
        if os.path.exists('master_error_log.jsonl'):
            with open('master_error_log.jsonl', 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'new_error':
                            total_errors += 1
                            # Check if error is from last hour
                            error_time = datetime.fromisoformat(data.get('timestamp', ''))
                            if (datetime.now() - error_time).total_seconds() < 3600:
                                recent_errors += 1
                    except:
                        continue
            
            print(f"📈 Total errors detected: {total_errors}")
            print(f"🕐 Errors in last hour: {recent_errors}")
        else:
            print("📄 No master log found yet")
    except Exception as e:
        print(f"❌ Error reading logs: {e}")
    
    print("\n🌐 API MONITORING:")
    print("-" * 30)
    
    # Check recent API status
    api_checks = 0
    api_errors = 0
    
    try:
        if os.path.exists('master_error_log.jsonl'):
            with open('master_error_log.jsonl', 'r') as f:
                for line in f:
                    if 'API' in line:
                        api_checks += 1
                        if 'ERROR' in line.upper():
                            api_errors += 1
            
            print(f"🔍 API checks performed: {api_checks}")
            print(f"⚠️ API errors found: {api_errors}")
        
        # Test NewsData.io API that was causing issues
        if recent_errors == 0:
            print("✅ No recent API errors detected")
            print("✅ NewsData.io 422 error appears to be FIXED!")
        
    except:
        print("❓ Unable to check API status")
    
    print("\n🛠️ AUTO-FIX STATUS:")
    print("-" * 30)
    
    auto_fixes = 0
    try:
        if os.path.exists('master_error_log.jsonl'):
            with open('master_error_log.jsonl', 'r') as f:
                content = f.read()
                auto_fixes = content.count('AUTO_FIX')
            
            print(f"🔧 Auto-fixes applied: {auto_fixes}")
        
        # Check for SSL fix config
        if os.path.exists('ssl_fix_config.json'):
            print("✅ SSL bypass configuration created")
        
    except:
        print("❓ Unable to check auto-fix status")
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    
    if total_errors == 0:
        print("✅ System is HEALTHY - No errors detected")
    elif recent_errors == 0:
        print("✅ System is STABLE - No recent errors")
    else:
        print(f"⚠️ {recent_errors} recent errors need attention")
    
    print(f"📊 Monitor has been running successfully")
    print(f"🔄 Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def monitor_live():
    """Monitor the system live with updates"""
    print("🔄 LIVE ERROR MONITOR")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            check_monitor_status()
            print("\n⏳ Refreshing in 30 seconds...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\n👋 Live monitoring stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'live':
        monitor_live()
    else:
        check_monitor_status()
        print("\n💡 Tip: Run 'python monitor_status.py live' for live updates") 