"""
🚀 NASA SERVER - MCP gRPC Enhanced Launcher
============================================
Only launches the full NASA MCP gRPC enhanced server.
No fallbacks allowed - enterprise architecture only.
"""

import subprocess
import sys
import os

def main():
    print("🚀 NASA MCP gRPC SERVER LAUNCHER")
    print("=" * 50)
    print("🧮 Full NASA Mathematical Optimizations")
    print("🏢 Enterprise MCP gRPC Architecture Only")
    print("🚫 NO FALLBACK - NASA Enhanced Only")
    print("=" * 50)
    
    # Only use the full NASA MCP gRPC server
    nasa_server = "nasa_polygon_universal_bridge_server.py"
    
    if not os.path.exists(nasa_server):
        print(f"❌ NASA MCP gRPC server not found: {nasa_server}")
        print("🚫 NO FALLBACK - Full NASA MCP gRPC architecture required")
        return 1
    
    print(f"🌌 Launching: {nasa_server}")
    
    try:
        subprocess.run([sys.executable, nasa_server])
        return 0
    except KeyboardInterrupt:
        print("\n⚠️ Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🚫 NO FALLBACK - Full NASA MCP gRPC architecture required")
        return 1

if __name__ == "__main__":
    exit(main()) 