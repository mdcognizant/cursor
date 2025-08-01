#!/usr/bin/env python3
"""
Test Script for Robust Auto Startup System
==========================================
This script tests and validates the robust startup system.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime

def test_startup_system():
    """Test the robust startup system"""
    print("🧪 TESTING ROBUST AUTO STARTUP SYSTEM")
    print("=" * 50)
    
    # Step 1: Check if all required files exist
    print("\n1️⃣ Checking required files...")
    required_files = [
        'robust_auto_startup.py',
        'enhanced_news_scraper.py',
        'breaking_news_scraper.py',
        'enhanced_news_platform_ultimate_v2.html',
        'enhanced_delta_news_platform_complete.html'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (MISSING)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    
    # Step 2: Check Python modules
    print("\n2️⃣ Checking Python dependencies...")
    try:
        import psutil
        print("   ✅ psutil")
    except ImportError:
        print("   ❌ psutil (install with: pip install psutil)")
        return False
    
    try:
        import requests
        print("   ✅ requests")
    except ImportError:
        print("   ❌ requests (install with: pip install requests)")
        return False
    
    # Step 3: Test individual service startup capability
    print("\n3️⃣ Testing individual services...")
    
    # Test enhanced scraper import
    try:
        import enhanced_news_scraper
        print("   ✅ Enhanced News Scraper module can be imported")
    except Exception as e:
        print(f"   ❌ Enhanced News Scraper import failed: {e}")
        return False
    
    # Test breaking news scraper import
    try:
        import breaking_news_scraper
        print("   ✅ Breaking News Scraper module can be imported")
    except Exception as e:
        print(f"   ❌ Breaking News Scraper import failed: {e}")
        return False
    
    # Step 4: Test port availability
    print("\n4️⃣ Checking port availability...")
    test_ports = [8000, 8888, 8889]
    
    for port in test_ports:
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    print(f"   ⚠️  Port {port} is in use (may be from previous session)")
                else:
                    print(f"   ✅ Port {port} is available")
        except Exception as e:
            print(f"   ❌ Port {port} check failed: {e}")
    
    # Step 5: Test startup system import
    print("\n5️⃣ Testing startup system...")
    try:
        import robust_auto_startup
        print("   ✅ Robust Auto Startup module can be imported")
        
        # Test class instantiation
        startup = robust_auto_startup.RobustAutoStartup()
        print("   ✅ RobustAutoStartup class can be instantiated")
        
        # Test configuration
        if startup.service_configs:
            print(f"   ✅ Service configurations loaded ({len(startup.service_configs)} services)")
        else:
            print("   ❌ No service configurations found")
            return False
            
    except Exception as e:
        print(f"   ❌ Startup system test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED! The robust startup system is ready to use.")
    print("\n💡 To start the system, run:")
    print("   python robust_auto_startup.py")
    
    return True

def show_startup_instructions():
    """Show detailed startup instructions"""
    print("\n" + "=" * 60)
    print("📋 STARTUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n🚀 Quick Start:")
    print("   python robust_auto_startup.py")
    
    print("\n🛡️ Features:")
    print("   • Anti-hang protection for PowerShell environments")
    print("   • Automatic retry for failed services")
    print("   • Health monitoring and auto-restart")
    print("   • Comprehensive error logging")
    print("   • Service dependency management")
    print("   • Frontend auto-launch")
    
    print("\n📊 Services Started:")
    print("   • Enhanced News Scraper (Port 8889)")
    print("   • Breaking News Scraper (Port 8888)")
    print("   • Error Monitoring System")
    print("   • HTTP Server (Port 8000)")
    
    print("\n🌐 Frontend Applications:")
    print("   • Enhanced News Platform")
    print("   • Delta News Platform")
    
    print("\n🔧 Troubleshooting:")
    print("   • If services fail to start, check startup_report.json")
    print("   • View detailed logs in the console output")
    print("   • Ensure ports 8000, 8888, 8889 are available")
    print("   • Install missing dependencies with pip")

if __name__ == "__main__":
    success = test_startup_system()
    show_startup_instructions()
    
    if success:
        print("\n🎉 System is ready for automatic startup!")
        sys.exit(0)
    else:
        print("\n❌ System has issues that need to be resolved.")
        sys.exit(1) 