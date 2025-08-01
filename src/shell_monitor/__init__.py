"""
Shell Monitor - Cursor Command Execution Monitor
A Python utility to monitor and diagnose shell command execution issues in Cursor.
"""

__version__ = "1.0.0"
__author__ = "Development Automation Suite"

from .monitor import ShellMonitor
from .diagnostics import ShellDiagnostics
from .cli import main

__all__ = ['ShellMonitor', 'ShellDiagnostics', 'main'] 