#!/usr/bin/env python3
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
