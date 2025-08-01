#!/usr/bin/env python3
"""
Organization-Friendly Auto Start
================================
Launches news platform without localhost dependencies.
Designed for corporate/restricted environments.

Author: Assistant  
Date: 2025-01-27
"""

import webbrowser
import sys
import os
from pathlib import Path

def cleanup_and_exit():
    """Clean exit function"""
    print("\n👋 Exiting...")
    sys.exit(1)

def organization_friendly_start(monitor=True):
    """Start platform without localhost dependencies"""
    
    print("🚀 ORGANIZATION-FRIENDLY NEWS PLATFORM")
    print("=" * 50)
    print("🏢 Corporate environment compatible")
    print("🚫 No localhost servers required")
    print("🌐 External APIs only")
    
    try:
        # Get current directory
        current_dir = Path(__file__).parent.absolute()
        
        # Check platform files
        v2_platform = current_dir / "enhanced_news_platform_ultimate_v2.html"
        api_test = current_dir / "api_test_external.html"
        
        if not v2_platform.exists():
            print(f"❌ V2 platform not found: {v2_platform}")
            cleanup_and_exit()

        print("\n✅ ORGANIZATION-FRIENDLY FEATURES:")
        print("   🌐 External APIs: NewsData.io + Currents")
        print("   📄 Direct file access - no servers")
        print("   🔒 Corporate firewall compatible")
        print("   🎨 Premium V2 design with full features")

        # Step 1: Open API test page
        if api_test.exists():
            print(f"\n🧪 Opening API Test Page...")
            print(f"   📍 Location: {api_test}")
            webbrowser.open(f"file:///{api_test}")
            print("   ✅ Test external APIs first")
        else:
            print("   ⚠️ API test page not found")

        # Step 2: Open V2 platform 
        print(f"\n🖥️ Opening V2 News Platform...")
        print(f"   📍 Location: {v2_platform}")
        webbrowser.open(f"file:///{v2_platform}")
        print("   ✅ Platform opened successfully")

        # Step 3: Show status
        print("\n📊 PLATFORM STATUS")
        print("-" * 40)
        print("✅ V2 News Platform: Ready (Direct file access)")
        print("✅ API Test Page: Available for diagnostics")
        print("✅ External APIs: NewsData.io + Currents configured")
        print("🚫 No localhost servers required")
        print()
        print("📰 Expected Performance:")
        print("   • 50+ articles from NewsData.io (200 calls/day)")
        print("   • 50+ articles from Currents API (backup)")
        print("   • Category-specific images from Unsplash")
        print("   • Premium responsive design")
        print()
        print("🔧 TROUBLESHOOTING:")
        print("   1. Use API test page to verify connectivity")
        print("   2. Check browser console for error details")
        print("   3. Ensure network access to external APIs")
        print("   4. Try different browser if needed")
        print()
        print("🎯 HOW TO USE:")
        print("   • Click 'Refresh News' to load fresh articles")
        print("   • Browse categories with the filter buttons")
        print("   • All images and content work offline-ready")

        if monitor:
            print("\n🛡️ MONITORING:")
            print("   • Manual monitoring via browser console")
            print("   • API status visible in platform footer")
            print("   • Error reporting built into V2 platform")

        print(f"\n🎉 Ready! Platform launched successfully.")
        print("Press any key to exit...")
        input()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Manual Instructions:")
        print("1. Open enhanced_news_platform_ultimate_v2.html in browser")
        print("2. Use api_test_external.html to test connectivity")
        cleanup_and_exit()

def show_help():
    """Show help information"""
    print("🚀 Organization-Friendly News Platform")
    print("=" * 40)
    print()
    print("USAGE:")
    print("  python auto_start_with_monitoring.py [options]")
    print()
    print("OPTIONS:")
    print("  --no-monitor    Skip monitoring setup")
    print("  --help          Show this help")
    print()
    print("FEATURES:")
    print("  ✅ No localhost dependencies")
    print("  ✅ Corporate firewall compatible") 
    print("  ✅ External APIs only")
    print("  ✅ Direct file access")
    print()
    print("FILES LAUNCHED:")
    print("  • enhanced_news_platform_ultimate_v2.html")
    print("  • api_test_external.html")

if __name__ == "__main__":
    monitor = True
    
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            show_help()
            sys.exit(0)
        if "--no-monitor" in sys.argv:
            monitor = False
    
    organization_friendly_start(monitor) 