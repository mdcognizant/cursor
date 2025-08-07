#!/bin/bash
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
