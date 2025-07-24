#!/usr/bin/env python3
"""
Shell Monitor - Standalone Entry Point
A Python utility to monitor and diagnose shell command execution issues in Cursor.

This script provides a standalone entry point for the shell monitor utility.
It can be run directly without installing the package.

Usage:
    python shell_monitor.py run "git status"
    python shell_monitor.py diagnose
    python shell_monitor.py interactive
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
script_dir = Path(__file__).parent
parent_dir = script_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from shellmonitor.cli import main
except ImportError as e:
    print(f"❌ Error importing shell monitor modules: {e}")
    print("Make sure you're running this script from the shellmonitor directory.")
    print("Required directory structure:")
    print("  ./shellmonitor/")
    print("    ├── __init__.py")
    print("    ├── monitor.py")
    print("    ├── diagnostics.py")
    print("    └── cli.py")
    sys.exit(1)

def show_banner():
    """Show the application banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                          SHELL MONITOR                           ║
║                   Cursor Command Execution Monitor               ║
║                                                                   ║
║  A Python utility to monitor shell commands and diagnose         ║
║  performance issues that cause Cursor to get stuck.              ║
╚═══════════════════════════════════════════════════════════════════╝
""")

def show_quick_help():
    """Show quick help information."""
    print("""
🚀 Quick Start:

  Monitor a command:
    python shell_monitor.py run "git status"
    python shell_monitor.py run "npm install" --timeout 300

  Run diagnostics:
    python shell_monitor.py diagnose

  Interactive mode:
    python shell_monitor.py interactive

  Show command history:
    python shell_monitor.py history

  Configure settings:
    python shell_monitor.py config --show
    python shell_monitor.py config --set-timeout 120

  Get full help:
    python shell_monitor.py --help

🔍 Features:
  • Live command execution timer
  • Configurable timeout detection (default: 60s)
  • Interactive retry/kill/diagnose options
  • Comprehensive shell performance diagnostics
  • Command history tracking
  • Clean shell environment execution
  • Verbose logging and file output

💡 Pro Tips:
  • Use --verbose for detailed output
  • Use --clean for clean shell environment
  • Use interactive mode for ongoing monitoring
  • Run diagnostics if commands are frequently slow
""")

if __name__ == "__main__":
    # Check if no arguments provided or help requested
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']):
        show_banner()
        show_quick_help()
        sys.exit(0)
    
    # Run the CLI
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 