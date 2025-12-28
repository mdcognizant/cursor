#!/usr/bin/env python3
"""
Debug Script for Simple Error Monitor
=====================================
This script will help us identify what's causing the error monitor to crash.
"""

import sys
import traceback

def debug_error_monitor():
    """Debug the error monitor to find the crash cause"""
    print("🔍 DEBUGGING SIMPLE ERROR MONITOR")
    print("=" * 50)
    
    try:
        print("📋 Step 1: Testing imports...")
        import simple_error_monitor
        print("   ✅ simple_error_monitor imported successfully")
        
        print("\n📋 Step 2: Testing class instantiation...")
        monitor = simple_error_monitor.SimpleErrorMonitor()
        print("   ✅ SimpleErrorMonitor instantiated successfully")
        
        print("\n📋 Step 3: Testing initialization...")
        monitor.initialize_master_log()
        print("   ✅ Master log initialized successfully")
        
        print("\n📋 Step 4: Testing individual methods...")
        
        # Test write to master log
        monitor.write_to_master_log("INFO", "TEST", "Debug test message")
        print("   ✅ Master log write successful")
        
        print("\n📋 Step 5: Testing threading methods individually...")
        
        # Test each threading method individually
        try:
            monitor.discover_log_files()
            print("   ✅ discover_log_files() successful")
        except Exception as e:
            print(f"   ❌ discover_log_files() failed: {e}")
            traceback.print_exc()
        
        try:
            # Just test API health once, don't loop
            monitor.check_api_health("https://httpbin.org/status/200")
            print("   ✅ check_api_health() successful")
        except Exception as e:
            print(f"   ❌ check_api_health() failed: {e}")
            traceback.print_exc()
        
        print("\n📋 Step 6: Testing short monitoring run...")
        
        # Try a very short monitoring session
        monitor.running = True
        import threading
        import time
        
        def short_monitor():
            try:
                time.sleep(2)  # Run for 2 seconds only
                monitor.running = False
                print("   ✅ Short monitoring session completed")
            except Exception as e:
                print(f"   ❌ Short monitoring failed: {e}")
                traceback.print_exc()
        
        thread = threading.Thread(target=short_monitor, daemon=True)
        thread.start()
        
        # Start monitoring but stop after 3 seconds
        print("   🔄 Starting short monitoring session...")
        monitor.start_monitoring()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   The simple_error_monitor module cannot be imported")
        traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        
        # Additional debugging info
        print("\n🔧 System Information:")
        print(f"   Python version: {sys.version}")
        print(f"   Platform: {sys.platform}")
        print(f"   Working directory: {sys.path[0]}")

if __name__ == "__main__":
    debug_error_monitor() 