"""
🚀 OPEN NASA SERVER - MCP gRPC Enhanced Command Alias
====================================================
This launches the full NASA MCP gRPC enhanced server only.
No fallbacks - enterprise architecture required.
"""

import subprocess
import sys
import os

def main():
    print("🚀 OPEN NASA MCP gRPC SERVER")
    print("=" * 40)
    print("🧮 NASA Mathematical Optimizations")
    print("🏢 Enterprise MCP gRPC Only")
    print("🚫 NO FALLBACK ALLOWED")
    print("=" * 40)
    
    # Only launch the full NASA MCP gRPC server
    nasa_server = "nasa_polygon_universal_bridge_server.py"
    
    if not os.path.exists(nasa_server):
        print(f"❌ NASA MCP gRPC server not found: {nasa_server}")
        print("🚫 Full NASA MCP gRPC architecture required")
        return 1
    
    print(f"🌌 Opening: {nasa_server}")
    
    try:
        subprocess.run([sys.executable, nasa_server])
        return 0
    except KeyboardInterrupt:
        print("\n⚠️ Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🚫 NO FALLBACK - NASA MCP gRPC required")
        return 1

if __name__ == "__main__":
    exit(main()) 