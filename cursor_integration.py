#!/usr/bin/env python3
"""
🚀 CURSOR INTEGRATION FOR NASA SERVER COMMANDS

Sets up Cursor IDE to automatically recognize and execute NASA server commands.

This script:
1. Creates command aliases for Cursor
2. Sets up natural language command recognition
3. Integrates with Cursor's terminal
4. Provides seamless NASA server control

Usage:
  python cursor_integration.py --setup
  python cursor_integration.py --test
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

def print_banner():
    """Print integration banner."""
    print("🚀 CURSOR NASA SERVER INTEGRATION")
    print("=" * 40)
    print("✅ Setting up natural language commands")
    print("✅ Creating command aliases")
    print("✅ Integrating with Cursor terminal")
    print("=" * 40)

def create_cursor_tasks_json():
    """Create/update .vscode/tasks.json for Cursor command integration."""
    vscode_dir = Path('.vscode')
    vscode_dir.mkdir(exist_ok=True)
    
    tasks_file = vscode_dir / 'tasks.json'
    
    # Define NASA server tasks
    tasks_config = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "NASA Server: Launch",
                "type": "shell",
                "command": "python",
                "args": ["cursor_commands.py", "run nasa server"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "new",
                    "showReuseMessage": True,
                    "clear": False
                },
                "problemMatcher": [],
                "detail": "Launch NASA server with automatic configuration"
            },
            {
                "label": "NASA Server: Launch with MCP+gRPC",
                "type": "shell",
                "command": "python",
                "args": ["cursor_commands.py", "run nasa server with mcp and grpc"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "new",
                    "showReuseMessage": True,
                    "clear": False
                },
                "problemMatcher": [],
                "detail": "Launch full MCP+gRPC NASA server"
            },
            {
                "label": "NASA Server: Status Check",
                "type": "shell",
                "command": "python",
                "args": ["cursor_commands.py", "nasa server status"],
                "group": "test",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared",
                    "showReuseMessage": True,
                    "clear": False
                },
                "problemMatcher": [],
                "detail": "Check NASA server status"
            },
            {
                "label": "NASA Server: Stop",
                "type": "shell",
                "command": "python",
                "args": ["cursor_commands.py", "stop nasa server"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared",
                    "showReuseMessage": True,
                    "clear": False
                },
                "problemMatcher": [],
                "detail": "Stop NASA server"
            }
        ]
    }
    
    # Write tasks.json
    with open(tasks_file, 'w') as f:
        json.dump(tasks_config, f, indent=2)
    
    print(f"✅ Created {tasks_file}")
    return True

def create_cursor_launch_json():
    """Create/update .vscode/launch.json for debugging NASA server."""
    vscode_dir = Path('.vscode')
    vscode_dir.mkdir(exist_ok=True)
    
    launch_file = vscode_dir / 'launch.json'
    
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "🚀 NASA Server Debug",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/run_nasa_server.py",
                "console": "integratedTerminal",
                "args": [],
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                },
                "cwd": "${workspaceFolder}",
                "stopOnEntry": False,
                "justMyCode": False
            },
            {
                "name": "🚀 NASA MCP+gRPC Debug",
                "type": "python", 
                "request": "launch",
                "program": "${workspaceFolder}/nasa_mcp_grpc_polygon_launcher.py",
                "console": "integratedTerminal",
                "args": [],
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                },
                "cwd": "${workspaceFolder}",
                "stopOnEntry": False,
                "justMyCode": False
            }
        ]
    }
    
    with open(launch_file, 'w') as f:
        json.dump(launch_config, f, indent=2)
    
    print(f"✅ Created {launch_file}")
    return True

def create_cursor_settings_json():
    """Create/update .vscode/settings.json for NASA server integration."""
    vscode_dir = Path('.vscode')
    vscode_dir.mkdir(exist_ok=True)
    
    settings_file = vscode_dir / 'settings.json'
    
    # Load existing settings if they exist
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        except:
            settings = {}
    
    # Add NASA server specific settings
    nasa_settings = {
        "terminal.integrated.cwd": "${workspaceFolder}",
        "python.defaultInterpreterPath": "python",
        "terminal.integrated.env.windows": {
            "NASA_SERVER_PATH": "${workspaceFolder}"
        },
        "terminal.integrated.env.linux": {
            "NASA_SERVER_PATH": "${workspaceFolder}"
        },
        "terminal.integrated.env.osx": {
            "NASA_SERVER_PATH": "${workspaceFolder}"
        },
        "files.associations": {
            "cursor_commands.py": "python",
            "nasa*.py": "python",
            "run_nasa_server.*": "shellscript"
        },
        "terminal.integrated.commandsToSkipShell": [
            "python cursor_commands.py"
        ]
    }
    
    # Merge settings
    settings.update(nasa_settings)
    
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print(f"✅ Updated {settings_file}")
    return True

def create_command_palette_integration():
    """Create command palette integration for Cursor."""
    
    # Create a simple command wrapper script
    wrapper_script = '''#!/usr/bin/env python3
"""
Cursor Command Wrapper for NASA Server
Allows natural language commands in Cursor terminal
"""

import sys
import subprocess

# Map of natural language commands to actual commands
COMMAND_MAP = {
    "run nasa server": ["python", "cursor_commands.py", "run nasa server"],
    "run nasa server with mcp and grpc": ["python", "cursor_commands.py", "run nasa server with mcp and grpc"],
    "open nasa server": ["python", "cursor_commands.py", "open nasa server"],
    "start nasa server": ["python", "cursor_commands.py", "start nasa server"],
    "stop nasa server": ["python", "cursor_commands.py", "stop nasa server"],
    "nasa server status": ["python", "cursor_commands.py", "nasa server status"],
    "nasa": ["python", "cursor_commands.py", "run nasa server"],
    "nasa help": ["python", "cursor_commands.py", "nasa server help"]
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Available commands:")
        for cmd in COMMAND_MAP.keys():
            print(f"  {cmd}")
        sys.exit(0)
    
    user_command = " ".join(sys.argv[1:]).lower()
    
    if user_command in COMMAND_MAP:
        subprocess.run(COMMAND_MAP[user_command])
    else:
        print(f"Unknown command: {user_command}")
        print("Available commands:")
        for cmd in COMMAND_MAP.keys():
            print(f"  {cmd}")
'''
    
    with open('cursor_nasa_wrapper.py', 'w') as f:
        f.write(wrapper_script)
    
    print("✅ Created cursor_nasa_wrapper.py")
    return True

def create_batch_aliases():
    """Create batch/shell aliases for easy command access."""
    
    # Windows batch file
    batch_content = '''@echo off
REM NASA Server Command Aliases for Windows

if /i "%1"=="run" if /i "%2"=="nasa" if /i "%3"=="server" (
    if /i "%4"=="with" if /i "%5"=="mcp" (
        python cursor_commands.py "run nasa server with mcp and grpc"
    ) else (
        python cursor_commands.py "run nasa server"
    )
    goto :eof
)

if /i "%1"=="nasa" (
    python cursor_commands.py "run nasa server"
    goto :eof
)

if /i "%1"=="open" if /i "%2"=="nasa" (
    python cursor_commands.py "open nasa server"
    goto :eof
)

if /i "%1"=="start" if /i "%2"=="nasa" (
    python cursor_commands.py "start nasa server"
    goto :eof
)

if /i "%1"=="stop" if /i "%2"=="nasa" (
    python cursor_commands.py "stop nasa server"
    goto :eof
)

echo Unknown command: %*
echo Available commands:
echo   run nasa server
echo   run nasa server with mcp and grpc
echo   open nasa server
echo   start nasa server
echo   stop nasa server
echo   nasa
'''
    
    with open('nasa_alias.bat', 'w') as f:
        f.write(batch_content)
    
    # Shell script for Linux/Mac
    shell_content = '''#!/bin/bash
# NASA Server Command Aliases for Linux/Mac

case "$*" in
    "run nasa server with mcp and grpc"|"run nasa server with mcp"*)
        python cursor_commands.py "run nasa server with mcp and grpc"
        ;;
    "run nasa server"|"run nasa")
        python cursor_commands.py "run nasa server"
        ;;
    "open nasa server"|"open nasa")
        python cursor_commands.py "open nasa server"
        ;;
    "start nasa server"|"start nasa")
        python cursor_commands.py "start nasa server"
        ;;
    "stop nasa server"|"stop nasa")
        python cursor_commands.py "stop nasa server"
        ;;
    "nasa server status"|"check nasa")
        python cursor_commands.py "nasa server status"
        ;;
    "nasa")
        python cursor_commands.py "run nasa server"
        ;;
    *)
        echo "Unknown command: $*"
        echo "Available commands:"
        echo "  run nasa server"
        echo "  run nasa server with mcp and grpc"
        echo "  open nasa server"
        echo "  start nasa server"
        echo "  stop nasa server"
        echo "  nasa"
        ;;
esac
'''
    
    with open('nasa_alias.sh', 'w') as f:
        f.write(shell_content)
    
    # Make shell script executable
    try:
        os.chmod('nasa_alias.sh', 0o755)
    except:
        pass
    
    print("✅ Created nasa_alias.bat and nasa_alias.sh")
    return True

def test_integration():
    """Test the Cursor integration setup."""
    print("\n🧪 TESTING CURSOR INTEGRATION")
    print("-" * 40)
    
    # Test command interpreter
    print("1. Testing command interpreter...")
    try:
        result = subprocess.run([
            sys.executable, 'cursor_commands.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ Command interpreter working")
        else:
            print("   ❌ Command interpreter failed")
            return False
    except Exception as e:
        print(f"   ❌ Command interpreter error: {e}")
        return False
    
    # Test file existence
    print("2. Checking integration files...")
    required_files = [
        'cursor_commands.py',
        '.vscode/tasks.json', 
        '.vscode/launch.json',
        '.vscode/settings.json',
        'cursor_nasa_wrapper.py',
        'nasa_alias.bat',
        'nasa_alias.sh'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} missing")
            all_files_exist = False
    
    if all_files_exist:
        print("\n🎯 Integration setup complete! You can now use:")
        print("  - 'run nasa server' in Cursor terminal")
        print("  - 'run nasa server with mcp and grpc'")
        print("  - Ctrl+Shift+P → 'Tasks: Run Task' → NASA Server options")
        print("  - F5 to debug NASA server")
        return True
    else:
        print("\n❌ Integration setup incomplete")
        return False

def setup_integration():
    """Setup complete Cursor integration."""
    print_banner()
    
    success = True
    success &= create_cursor_tasks_json()
    success &= create_cursor_launch_json()
    success &= create_cursor_settings_json()
    success &= create_command_palette_integration()
    success &= create_batch_aliases()
    
    if success:
        print("\n✅ CURSOR INTEGRATION SETUP COMPLETE!")
        print("\nYou can now use these commands in Cursor:")
        print("  📝 Type in terminal: 'run nasa server'")
        print("  📝 Type in terminal: 'run nasa server with mcp and grpc'")
        print("  🎛️ Press Ctrl+Shift+P → 'Tasks: Run Task' → NASA Server")
        print("  🐛 Press F5 to debug NASA server")
        print("  🖥️ Use Command Palette for quick access")
        return True
    else:
        print("\n❌ Integration setup failed")
        return False

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cursor_integration.py --setup")
        print("  python cursor_integration.py --test")
        return 1
    
    action = sys.argv[1].lower()
    
    if action == '--setup':
        return 0 if setup_integration() else 1
    elif action == '--test':
        return 0 if test_integration() else 1
    else:
        print(f"Unknown action: {action}")
        return 1

if __name__ == "__main__":
    exit(main()) 