#!/usr/bin/env python3
"""
Cursor Shell Monitor Wrapper
Universal command wrapper that routes all shell commands through the monitoring system.
This prevents Cursor from hanging on stuck commands.
"""

import sys
import os
import subprocess
import json
from pathlib import Path
import time

# Add the shell monitor to Python path
CURSOR_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CURSOR_ROOT))

try:
    from shellmonitor.monitor import ShellMonitor
    from shellmonitor.monitor import CommandResult
except ImportError:
    print("❌ Error: Shell Monitor not found. Please ensure the shell monitor is installed.")
    sys.exit(1)

class CursorCommandWrapper:
    """Wrapper that monitors commands executed by Cursor."""
    
    def __init__(self):
        self.monitor = ShellMonitor(timeout=60, verbose=False)  # Default 60s timeout
        self.config_file = Path.home() / ".cursor_monitor_config.json"
        self.load_config()
        
    def load_config(self):
        """Load configuration for Cursor integration."""
        default_config = {
            "default_timeout": 60,
            "fast_commands": ["echo", "pwd", "ls", "dir", "cd"],
            "slow_commands": ["npm install", "git clone", "docker build"],
            "command_timeouts": {
                "git": 30,
                "npm": 300,
                "python": 120,
                "node": 120,
                "docker": 600
            },
            "auto_kill": False,  # Whether to auto-kill without prompting
            "log_all_commands": True,
            "cursor_integration": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception:
                pass  # Use default config if loading fails
        else:
            # Create default config file
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
            except Exception:
                pass
        
        self.config = default_config
    
    def get_command_timeout(self, command_parts):
        """Get appropriate timeout for a command."""
        if not command_parts:
            return self.config["default_timeout"]
        
        command_name = command_parts[0].lower()
        
        # Check for exact command matches
        if command_name in self.config["command_timeouts"]:
            return self.config["command_timeouts"][command_name]
        
        # Check for fast commands (short timeout)
        full_command = " ".join(command_parts)
        for fast_cmd in self.config["fast_commands"]:
            if fast_cmd in full_command.lower():
                return 10  # 10 seconds for fast commands
        
        # Check for slow commands (long timeout)
        for slow_cmd in self.config["slow_commands"]:
            if slow_cmd in full_command.lower():
                return 600  # 10 minutes for slow commands
        
        return self.config["default_timeout"]
    
    def wrap_command(self, original_command, command_args):
        """Wrap a command execution through the shell monitor."""
        # Reconstruct the full command
        if command_args:
            full_command = f"{original_command} {' '.join(command_args)}"
            command_parts = [original_command] + command_args
        else:
            full_command = original_command
            command_parts = [original_command]
        
        # Get appropriate timeout
        timeout = self.get_command_timeout(command_parts)
        
        # Update monitor timeout
        self.monitor.timeout = timeout
        
        # Log the command execution
        if self.config["log_all_commands"]:
            log_entry = {
                "timestamp": time.time(),
                "command": full_command,
                "timeout": timeout,
                "source": "cursor_wrapper"
            }
            self._log_command(log_entry)
        
        # Execute through monitor
        try:
            print(f"🔍 Cursor Monitor: Executing '{full_command}' (timeout: {timeout}s)")
            result = self.monitor.execute_command(full_command)
            
            # Print command output
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='', file=sys.stderr)
            
            if result.returncode == 0:
                print(f"✅ Command completed in {result.duration:.2f}s")
                return result.returncode
            else:
                print(f"❌ Command failed (exit code: {result.returncode})")
                return result.returncode
                
        except KeyboardInterrupt:
            print("\n⚠️  Command interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Wrapper error: {e}")
            return 1
    
    def _log_command(self, log_entry):
        """Log command execution to file."""
        log_file = Path.home() / ".cursor_monitor_commands.log"
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass  # Ignore logging errors
    
    def fallback_execution(self, original_command, command_args):
        """Fallback to direct execution if monitor fails."""
        try:
            if command_args:
                result = subprocess.run([original_command] + command_args)
            else:
                result = subprocess.run([original_command])
            return result.returncode
        except Exception:
            return 1

def main():
    """Main wrapper execution."""
    if len(sys.argv) < 2:
        print("Usage: cursor_monitor_wrapper.py <original_command> [args...]")
        sys.exit(1)
    
    # Get the original command and its arguments
    original_command = sys.argv[1]
    command_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Create wrapper instance
    wrapper = CursorCommandWrapper()
    
    # Execute through monitor
    try:
        exit_code = wrapper.wrap_command(original_command, command_args)
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Wrapper failed: {e}")
        print("🔄 Falling back to direct execution...")
        exit_code = wrapper.fallback_execution(original_command, command_args)
        sys.exit(exit_code)

if __name__ == "__main__":
    main() 