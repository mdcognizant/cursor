#!/bin/bash

echo "🚀 NASA MCP gRPC SERVER LAUNCHER (UNIX/LINUX)"
echo "==============================================="
echo "🧮 Full NASA Mathematical Optimizations"
echo "🏢 Enterprise MCP gRPC Architecture Only"
echo "🚫 NO FALLBACK - NASA Enhanced Only"
echo "==============================================="

# Only use the full NASA MCP gRPC server
NASA_SERVER="nasa_polygon_universal_bridge_server.py"

if [ ! -f "$NASA_SERVER" ]; then
    echo "❌ NASA MCP gRPC server not found: $NASA_SERVER"
    echo "🚫 Full NASA MCP gRPC architecture required"
    exit 1
fi

echo "🌌 Launching: $NASA_SERVER"

# Launch the NASA MCP gRPC server
python3 "$NASA_SERVER" || python "$NASA_SERVER" 