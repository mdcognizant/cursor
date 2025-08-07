@echo off
echo 🚀 NASA MCP gRPC SERVER LAUNCHER (WINDOWS)
echo ==========================================
echo 🧮 Full NASA Mathematical Optimizations
echo 🏢 Enterprise MCP gRPC Architecture Only
echo 🚫 NO FALLBACK - NASA Enhanced Only
echo ==========================================

REM Only use the full NASA MCP gRPC server
set NASA_SERVER=nasa_polygon_universal_bridge_server.py

if not exist "%NASA_SERVER%" (
    echo ❌ NASA MCP gRPC server not found: %NASA_SERVER%
    echo 🚫 Full NASA MCP gRPC architecture required
    pause
    exit /b 1
)

echo 🌌 Launching: %NASA_SERVER%

REM Launch the NASA MCP gRPC server
python "%NASA_SERVER%"
if errorlevel 1 (
    echo ❌ Error launching NASA MCP gRPC server
    echo 🚫 NO FALLBACK - Full architecture required
    pause
    exit /b 1
)

echo ⚠️ Server stopped
pause 