#!/usr/bin/env python3
"""
Enhanced News Platform Launcher
===============================
Automatically starts:
1. Breaking News Scraper Service (CNN & BBC)
2. Enhanced News Platform (Ultimate v2)
3. Optional HTTP Server

Author: Assistant  
Date: 2025-01-27
"""

import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path
import threading
import requests

class EnhancedNewsLauncher:
    def __init__(self):
        self.breaking_news_process = None
        self.http_server_process = None
        
    def start_breaking_news_service(self):
        """Start the breaking news scraper service"""
        print("🔄 Starting Breaking News Scraper Service...")
        
        try:
            # Start the breaking news scraper
            self.breaking_news_process = subprocess.Popen([
                sys.executable, 'breaking_news_scraper.py'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"✅ Breaking News Service started (PID: {self.breaking_news_process.pid})")
            
            # Wait for service to be ready
            print("⏳ Waiting for breaking news service to be ready...")
            self.wait_for_service_ready()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start breaking news service: {e}")
            return False
    
    def wait_for_service_ready(self, max_attempts=10):
        """Wait for the breaking news service to be ready"""
        for attempt in range(max_attempts):
            try:
                response = requests.get('http://localhost:8888/health', timeout=2)
                if response.status_code == 200:
                    print("✅ Breaking News Service is ready!")
                    return True
            except:
                time.sleep(1)
                print(f"⏳ Attempt {attempt + 1}/{max_attempts} - waiting for service...")
        
        print("⚠️ Breaking News Service may not be fully ready, but continuing...")
        return False
    
    def start_http_server(self, port=8000):
        """Start HTTP server for local file serving"""
        print(f"🌐 Starting HTTP Server on port {port}...")
        
        try:
            self.http_server_process = subprocess.Popen([
                sys.executable, '-m', 'http.server', str(port)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"✅ HTTP Server started (PID: {self.http_server_process.pid})")
            print(f"🌐 Server available at: http://localhost:{port}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start HTTP server: {e}")
            return False
    
    def open_enhanced_platform(self, use_http_server=False, port=8000):
        """Open the enhanced news platform"""
        print("🚀 Opening Enhanced News Platform...")
        
        try:
            if use_http_server:
                url = f"http://localhost:{port}/enhanced_news_platform_ultimate_v2.html"
                print(f"🌐 Opening via HTTP: {url}")
                webbrowser.open(url)
            else:
                file_path = os.path.abspath("enhanced_news_platform_ultimate_v2.html")
                if os.path.exists(file_path):
                    print(f"📄 Opening file: {file_path}")
                    webbrowser.open(f"file:///{file_path}")
                else:
                    print(f"❌ File not found: {file_path}")
                    return False
            
            print("✅ Enhanced News Platform opened in browser")
            return True
            
        except Exception as e:
            print(f"❌ Failed to open platform: {e}")
            return False
    
    def check_dependencies(self):
        """Check if required files exist"""
        print("🔍 Checking dependencies...")
        
        required_files = [
            'breaking_news_scraper.py',
            'enhanced_news_platform_ultimate_v2.html'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        print("✅ All dependencies found")
        return True
    
    def launch_full_platform(self, with_http_server=False, port=8000):
        """Launch the complete enhanced news platform"""
        print("🚀 LAUNCHING ENHANCED NEWS PLATFORM")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Cannot launch - missing dependencies")
            return False
        
        success_count = 0
        total_components = 2 if not with_http_server else 3
        
        # 1. Start breaking news service
        if self.start_breaking_news_service():
            success_count += 1
        
        # 2. Start HTTP server (optional)
        if with_http_server:
            if self.start_http_server(port):
                success_count += 1
                time.sleep(2)  # Give server time to start
        
        # 3. Open enhanced platform
        if self.open_enhanced_platform(with_http_server, port):
            success_count += 1
        
        # Report results
        print("\n" + "=" * 50)
        print(f"📊 LAUNCH SUMMARY: {success_count}/{total_components} components started")
        
        if success_count == total_components:
            print("✅ ENHANCED NEWS PLATFORM FULLY OPERATIONAL!")
            print("\n🎯 Features Active:")
            print("   📡 Breaking News: Real-time from CNN & BBC (30s refresh)")
            print("   📰 News Articles: From NewsData.io & Currents API")
            print("   💹 Financial Ticker: Live market data updates")
            print("   🎨 Premium Design: Inspired by 20+ major news sites")
            print("   🔗 External Links: All articles open in new tabs")
            print("   📊 Compact Stats: Professional footer metrics")
            
            print("\n💡 Usage Instructions:")
            print("   🔄 Breaking news updates automatically every 30 seconds")
            print("   🔐 Admin access: Use 'lemonade' password for unlimited refreshes")
            print("   📱 Responsive design works on all devices")
            print("   ⚡ Hover effects and animations throughout")
            
            return True
        else:
            print("⚠️ Some components failed to start")
            print("💡 Platform may still work with reduced functionality")
            return False
    
    def cleanup(self):
        """Clean up processes"""
        print("\n🛑 Shutting down services...")
        
        if self.breaking_news_process:
            try:
                self.breaking_news_process.terminate()
                print("✅ Breaking News Service stopped")
            except:
                pass
        
        if self.http_server_process:
            try:
                self.http_server_process.terminate()
                print("✅ HTTP Server stopped")
            except:
                pass
        
        print("👋 Enhanced News Platform launcher stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Launch Enhanced News Platform with real breaking news from CNN & BBC"
    )
    parser.add_argument('--with-server', action='store_true', 
                       help='Start HTTP server for local file serving')
    parser.add_argument('--port', type=int, default=8000, 
                       help='HTTP server port (default: 8000)')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check dependencies, don\'t launch')
    
    args = parser.parse_args()
    
    launcher = EnhancedNewsLauncher()
    
    if args.check_only:
        launcher.check_dependencies()
        return
    
    try:
        success = launcher.launch_full_platform(
            with_http_server=args.with_server,
            port=args.port
        )
        
        if success:
            print("\n⏳ Platform is running. Press Ctrl+C to stop all services...")
            # Keep the script running to maintain services
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested...")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    main() 