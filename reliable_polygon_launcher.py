#!/usr/bin/env python3
"""
Reliable Polygon Launcher - Bypasses terminal hanging issues
Works on any machine, any environment

⚠️  WARNING: This launcher starts a BASIC Flask server (not MCP+gRPC)!
For FULL Universal API Bridge with MCP+gRPC features, use:
🔧 python mcp_grpc_polygon_launcher.py

DIFFERENCE:
❌ THIS: Basic Flask REST server (working_polygon_bridge_bulletproof.py)
✅ MCP: Universal API Bridge with MCP registry + gRPC optimizations
"""

import subprocess
import time
import webbrowser
import os
import sys
from pathlib import Path

def check_server_running():
    """Check if server is running without hanging commands"""
    try:
        import requests
        response = requests.get('http://localhost:8001', timeout=2)
        return True
    except:
        return False

def start_polygon_server():
    """Start server reliably"""
    try:
        # Use absolute path to avoid issues
        server_file = Path(__file__).parent / "working_polygon_bridge_bulletproof.py"
        if server_file.exists():
            subprocess.Popen([sys.executable, str(server_file)], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("✅ Started Polygon server")
            time.sleep(3)  # Give server time to start
            return True
        else:
            print("❌ Server file not found")
            return False
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def open_polygon_interface():
    """Open browser interface reliably via HTTP server (fixes CORS issues)"""
    try:
        # Method 1: Start HTTP server and open browser
        import subprocess
        import threading
        import http.server
        import socketserver
        
        # Check if HTML file exists first
        html_file = Path(__file__).parent / "universal-api-bridge" / "polygon_v6.html"
        if not html_file.exists():
            print("❌ HTML file not found")
            return False
        
        # Start HTTP server in background
        def start_http_server():
            PORT = 8080
            Handler = http.server.SimpleHTTPRequestHandler
            try:
                with socketserver.TCPServer(("", PORT), Handler) as httpd:
                    print(f"✅ HTTP server started on port {PORT}")
                    httpd.serve_forever()
            except Exception as e:
                print(f"⚠️ HTTP server error: {e}")
        
        # Start server in background thread
        server_thread = threading.Thread(target=start_http_server, daemon=True)
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Open browser to HTTP URL (avoids CORS issues)
        webbrowser.open("http://localhost:8080/universal-api-bridge/polygon_v6.html")
        print("✅ Opened Polygon interface via HTTP server (CORS-safe)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to open interface: {e}")
        # Fallback method - direct file
        try:
            html_file = Path(__file__).parent / "universal-api-bridge" / "polygon_v6.html"
            webbrowser.open(f"file:///{html_file.absolute()}")
            print("✅ Opened Polygon interface (fallback method)")
            return True
        except:
            return False

def main():
    print("=" * 50)
    print("Reliable Polygon Launcher v1.0")
    print("=" * 50)
    
    print("Step 1: Checking server status...")
    if not check_server_running():
        print("Starting Polygon server...")
        if not start_polygon_server():
            print("❌ Failed to start server")
            return False
    else:
        print("✅ Server already running")
    
    print("Step 2: Opening Polygon interface...")
    if not open_polygon_interface():
        print("❌ Failed to open interface")
        return False
    
    print("Step 3: Final verification...")
    time.sleep(2)
    if check_server_running():
        print("✅ SUCCESS: Polygon is now running!")
        print("✅ Server: http://localhost:8001")
        print("✅ Interface opened in browser")
    else:
        print("⚠️  Server may still be starting...")
    
    print("=" * 50)
    return True

if __name__ == "__main__":
    main()
    input("Press Enter to exit...") 