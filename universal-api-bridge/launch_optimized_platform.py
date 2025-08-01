#!/usr/bin/env python3
"""
Organization-Friendly Platform Launcher
=======================================
Launches news platform without localhost dependencies.
Designed for corporate/restricted environments.

Features:
- Direct file access (no servers needed)
- External APIs only (NewsData.io + Currents)
- Corporate firewall compatible
- Full platform functionality

Author: Assistant
Date: 2025-01-27
"""

import webbrowser
import os
import sys
import json
from datetime import datetime
from pathlib import Path

class OrganizationFriendlyLauncher:
    def __init__(self):
        self.current_dir = Path(__file__).parent.absolute()
        self.v2_platform = self.current_dir / "enhanced_news_platform_ultimate_v2.html"
        self.api_test = self.current_dir / "api_test_external.html"
        self.running = True
        
        # External API configuration (no localhost)
        self.api_config = {
            'newsdata': {
                'name': 'NewsData.io API',
                'endpoint': 'https://newsdata.io/api/1/latest',
                'limit': '50 articles per call, 200 calls/day',
                'status': 'External - no localhost needed'
            },
            'currents': {
                'name': 'Currents API',
                'endpoint': 'https://api.currentsapi.services/v1/latest-news',
                'limit': '50 articles per call',
                'status': 'External - backup source'
            }
        }

    def launch_platform(self):
        """Launch the organization-friendly platform"""
        print("🚀 ORGANIZATION-FRIENDLY NEWS PLATFORM")
        print("=" * 50)
        print("🏢 Corporate environment optimized")
        print("🚫 No localhost dependencies")
        print("🌐 External APIs only")
        print("📄 Direct file access")
        print()

        try:
            # Check if platform files exist
            if not self.check_platform_files():
                return False

            # Show platform features
            self.show_platform_features()

            # Launch API test page first
            self.launch_api_test()

            # Launch main platform
            self.launch_main_platform()

            # Show usage instructions
            self.show_usage_instructions()

            # Show troubleshooting
            self.show_troubleshooting()

            print("\n🎉 Platform launched successfully!")
            print("Press any key to exit...")
            input()
            
            return True

        except Exception as e:
            print(f"❌ Launch error: {e}")
            self.show_manual_instructions()
            return False

    def check_platform_files(self):
        """Check if required platform files exist"""
        print("📁 Checking platform files...")
        
        if not self.v2_platform.exists():
            print(f"❌ V2 platform not found: {self.v2_platform}")
            return False
        print(f"   ✅ V2 platform: {self.v2_platform.name}")
        
        if not self.api_test.exists():
            print(f"   ⚠️ API test page not found: {self.api_test}")
        else:
            print(f"   ✅ API test page: {self.api_test.name}")
        
        return True

    def show_platform_features(self):
        """Show organization-friendly features"""
        print("\n✅ ORGANIZATION-FRIENDLY FEATURES:")
        print("   🌐 External APIs: NewsData.io + Currents")
        print("   📄 Direct file access - no servers required")
        print("   🔒 Corporate firewall compatible")
        print("   🎨 Premium V2 design with full functionality")
        print("   🖼️ Category-specific images from Unsplash")
        print("   📱 Responsive mobile-friendly interface")
        print("   ⚡ Fast loading with optimized performance")

    def launch_api_test(self):
        """Launch API test page"""
        if self.api_test.exists():
            print(f"\n🧪 Opening API Test Page...")
            print(f"   📍 Location: {self.api_test}")
            webbrowser.open(f"file:///{self.api_test}")
            print("   ✅ Use this to verify external API connectivity")
            print("   🔧 Test both NewsData.io and Currents APIs")
        else:
            print("   ⚠️ API test page not available")

    def launch_main_platform(self):
        """Launch main V2 platform"""
        print(f"\n🖥️ Opening V2 News Platform...")
        print(f"   📍 Location: {self.v2_platform}")
        webbrowser.open(f"file:///{self.v2_platform}")
        print("   ✅ Platform opened successfully")

    def show_usage_instructions(self):
        """Show how to use the platform"""
        print("\n🎯 HOW TO USE:")
        print("   1. Test APIs first using the API test page")
        print("   2. Click 'Refresh News' to load fresh articles")
        print("   3. Browse categories with the filter buttons")
        print("   4. Click articles to read full content")
        print("   5. Check footer for API call statistics")

    def show_troubleshooting(self):
        """Show troubleshooting information"""
        print("\n🔧 TROUBLESHOOTING:")
        print("   📊 API Test Page:")
        print("     • Test NewsData.io API individually")
        print("     • Test Currents API individually")
        print("     • Check combined API test results")
        print("   🌐 Network Issues:")
        print("     • Verify external internet access")
        print("     • Check corporate firewall settings")
        print("     • Try different browser if needed")
        print("   🔍 Browser Console:")
        print("     • Press F12 to open developer tools")
        print("     • Check Console tab for error details")
        print("     • Look for API call responses")

    def show_manual_instructions(self):
        """Show manual launch instructions"""
        print("\n🔧 MANUAL LAUNCH INSTRUCTIONS:")
        print("1. Open enhanced_news_platform_ultimate_v2.html in browser")
        print("2. Use api_test_external.html to test API connectivity")
        print("3. Click 'Refresh News' to load articles from external APIs")

    def show_api_status(self):
        """Show API configuration status"""
        print("\n🌐 EXTERNAL API STATUS:")
        print("-" * 40)
        
        for api_name, config in self.api_config.items():
            print(f"✅ {config['name']}:")
            print(f"   📊 Limit: {config['limit']}")
            print(f"   🌐 Endpoint: {config['endpoint']}")
            print(f"   🔧 Status: {config['status']}")
            print()

    def generate_platform_report(self):
        """Generate a platform status report"""
        report = {
            'platform': 'Organization-Friendly News Platform',
            'timestamp': datetime.now().isoformat(),
            'localhost_dependencies': False,
            'files': {
                'v2_platform': str(self.v2_platform),
                'api_test': str(self.api_test),
                'v2_exists': self.v2_platform.exists(),
                'api_test_exists': self.api_test.exists()
            },
            'apis': self.api_config,
            'compatibility': {
                'corporate_firewall': True,
                'external_apis_only': True,
                'direct_file_access': True,
                'no_servers_required': True
            }
        }
        
        try:
            report_file = self.current_dir / "organization_friendly_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📋 Platform report saved: {report_file}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

def show_help():
    """Show help information"""
    print("🚀 Organization-Friendly News Platform Launcher")
    print("=" * 50)
    print()
    print("USAGE:")
    print("  python launch_optimized_platform.py [options]")
    print()
    print("OPTIONS:")
    print("  --api-status    Show API configuration")
    print("  --report        Generate platform report")
    print("  --help          Show this help")
    print()
    print("FEATURES:")
    print("  ✅ No localhost dependencies")
    print("  ✅ Corporate firewall compatible")
    print("  ✅ External APIs only")
    print("  ✅ Direct file access")
    print("  ✅ Premium V2 design")
    print()
    print("FILES:")
    print("  • enhanced_news_platform_ultimate_v2.html - Main platform")
    print("  • api_test_external.html - API testing tool")

def main():
    """Main function"""
    launcher = OrganizationFriendlyLauncher()
    
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            show_help()
            return
        elif "--api-status" in sys.argv:
            launcher.show_api_status()
            return
        elif "--report" in sys.argv:
            launcher.generate_platform_report()
            return
    
    success = launcher.launch_platform()
    
    if success:
        print("✅ Platform launched successfully")
    else:
        print("❌ Platform launch failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 