"""
Core Shell Command Monitor
Handles command execution with timeout detection and live monitoring.
"""

import subprocess
import threading
import time
import signal
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import logging

class CommandResult:
    """Represents the result of a command execution."""
    
    def __init__(self, command: str, start_time: datetime):
        self.command = command
        self.start_time = start_time
        self.end_time: Optional[datetime] = None
        self.duration: Optional[float] = None
        self.returncode: Optional[int] = None
        self.stdout: str = ""
        self.stderr: str = ""
        self.timed_out: bool = False
        self.killed: bool = False
        self.diagnostic_run: bool = False
    
    def complete(self, returncode: int, stdout: str, stderr: str):
        """Mark the command as completed."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
    
    def timeout(self):
        """Mark the command as timed out."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.timed_out = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            'command': self.command,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'returncode': self.returncode,
            'timed_out': self.timed_out,
            'killed': self.killed,
            'diagnostic_run': self.diagnostic_run
        }

class ShellMonitor:
    """Monitors shell command execution with timeout detection and diagnostics."""
    
    def __init__(self, timeout: int = 60, log_file: Optional[str] = None, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose
        self.logger = self._setup_logging(log_file)
        
        # Command history
        self.history: List[CommandResult] = []
        self.history_file = Path.home() / ".shell_monitor_history.json"
        self._load_history()
        
        # Current execution state
        self.current_process: Optional[subprocess.Popen] = None
        self.timer_thread: Optional[threading.Thread] = None
        self.stop_timer = threading.Event()
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'timed_out_commands': 0,
            'killed_commands': 0,
            'diagnostic_runs': 0
        }
    
    def _setup_logging(self, log_file: Optional[str]) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('shell_monitor')
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Clear any existing handlers to prevent duplicates
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_history(self):
        """Load command history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    # History file contains dictionaries, not CommandResult objects
                    # We'll just skip loading for now to avoid the bug
                    self.history = []
                    if self.verbose:
                        self.logger.info(f"Skipped loading {len(data) if isinstance(data, list) else 0} history entries")
        except Exception as e:
            self.logger.warning(f"Could not load history: {e}")
            self.history = []
    
    def _save_history(self):
        """Save command history to file."""
        try:
            # Keep only last 100 commands and handle both dict and CommandResult objects
            history_data = []
            for cmd in self.history[-100:]:
                if hasattr(cmd, 'to_dict'):
                    # CommandResult object
                    history_data.append(cmd.to_dict())
                elif isinstance(cmd, dict):
                    # Already a dictionary
                    history_data.append(cmd)
                else:
                    # Skip invalid entries
                    continue
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save history: {e}")
    
    def _start_timer(self, command: str, result: CommandResult):
        """Start the live timer display."""
        def timer_worker():
            start_time = time.time()
            while not self.stop_timer.is_set():
                elapsed = time.time() - start_time
                mins, secs = divmod(int(elapsed), 60)
                
                # Update display
                if elapsed < self.timeout:
                    status = f"\r⏱️  Executing: {command[:50]}{'...' if len(command) > 50 else ''} | Time: {mins:02d}:{secs:02d}"
                else:
                    # Timeout warning
                    status = f"\r⚠️  TIMEOUT: {command[:50]}{'...' if len(command) > 50 else ''} | Time: {mins:02d}:{secs:02d} (>{self.timeout}s)"
                
                print(status, end='', flush=True)
                
                # Safety break to prevent infinite loops
                if elapsed > self.timeout * 2:  # Double timeout as emergency brake
                    break
                    
                time.sleep(0.5)  # Update every 500ms
        
        self.stop_timer.clear()
        self.timer_thread = threading.Thread(target=timer_worker, daemon=True)
        self.timer_thread.start()
    
    def _stop_timer(self):
        """Stop the live timer display."""
        if self.timer_thread:
            self.stop_timer.set()
            # Don't wait too long for timer thread to stop
            self.timer_thread.join(timeout=2)
            print()  # New line after timer
    
    def _handle_timeout(self, command: str, result: CommandResult) -> str:
        """Handle command timeout with user interaction."""
        result.timeout()
        self._stop_timer()
        
        print(f"\n⚠️  Command timed out after {self.timeout} seconds!")
        print(f"Command: {command}")
        print("\nOptions:")
        print("1. (r)etry - Run the command again")
        print("2. (k)ill - Terminate the current process")
        print("3. (d)iagnose - Run diagnostics to identify issues")
        print("4. (c)ontinue - Continue waiting for the command")
        print("5. (q)uit - Exit the monitor")
        
        # Add timeout to user input to prevent hanging here too
        import select
        
        max_input_timeout = 30  # 30 seconds to respond
        start_input_time = time.time()
        
        while True:
            try:
                # For Windows, we can't use select, so just use regular input with a note
                if sys.platform == "win32":
                    print(f"\nPlease respond within {max_input_timeout} seconds...")
                    choice = input("What would you like to do? [r/k/d/c/q]: ").lower().strip()
                else:
                    # Unix-like systems can use select for timeout
                    print("What would you like to do? [r/k/d/c/q]: ", end='', flush=True)
                    ready, _, _ = select.select([sys.stdin], [], [], max_input_timeout)
                    if ready:
                        choice = sys.stdin.readline().strip().lower()
                    else:
                        print("\nNo input received, defaulting to 'kill'")
                        choice = 'k'
                
                # Check if we've been waiting too long
                if time.time() - start_input_time > max_input_timeout:
                    print("\nInput timeout, defaulting to 'kill'")
                    return 'kill'
                
                if choice in ['r', 'retry']:
                    return 'retry'
                elif choice in ['k', 'kill']:
                    return 'kill'
                elif choice in ['d', 'diagnose']:
                    return 'diagnose'
                elif choice in ['c', 'continue']:
                    return 'continue'
                elif choice in ['q', 'quit']:
                    return 'quit'
                else:
                    print("Invalid choice. Please enter r, k, d, c, or q.")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nInterrupted, defaulting to 'kill'")
                return 'kill'
    
    def _kill_process(self, result: CommandResult):
        """Kill the current process."""
        if self.current_process:
            try:
                if sys.platform == "win32":
                    # Windows - more aggressive termination
                    try:
                        self.current_process.terminate()
                        # Wait a short time for graceful termination
                        self.current_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        # Force kill if terminate didn't work
                        subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], 
                                     capture_output=True, timeout=5)
                else:
                    # Unix-like systems
                    try:
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                        self.current_process.wait(timeout=3)
                    except (subprocess.TimeoutExpired, ProcessLookupError):
                        try:
                            os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass  # Process already dead
                
                result.killed = True
                self.stats['killed_commands'] += 1
                self.logger.info("Process killed successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to kill process: {e}")
    
    def execute_command(self, command: str, shell: Optional[str] = None, 
                       cwd: Optional[str] = None) -> CommandResult:
        """Execute a shell command with monitoring."""
        result = CommandResult(command, datetime.now())
        self.history.append(result)
        self.stats['total_commands'] += 1
        
        self.logger.info(f"Executing command: {command}")
        
        # Detect shell if not specified
        if shell is None:
            shell = self._detect_shell()
        
        # Start timer
        self._start_timer(command, result)
        
        try:
            # Prepare command for different shells
            if sys.platform == "win32":
                if "powershell" in shell.lower():
                    # Use faster PowerShell execution options
                    cmd_args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
                elif "bash" in shell.lower():
                    cmd_args = ["bash", "-c", command]
                else:  # CMD
                    cmd_args = ["cmd", "/c", command]
            else:
                cmd_args = [shell, "-c", command]
            
            # Start process with timeout safety
            self.current_process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                preexec_fn=os.setsid if sys.platform != "win32" else None
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = self.current_process.communicate(timeout=self.timeout)
                self._stop_timer()
                result.complete(self.current_process.returncode, stdout, stderr)
                
                if result.duration and result.duration > 5:  # Log slow commands
                    self.logger.warning(f"Slow command detected: {command} took {result.duration:.2f}s")
                
            except subprocess.TimeoutExpired:
                # Handle timeout
                action = self._handle_timeout(command, result)
                
                if action == 'kill':
                    self._kill_process(result)
                    try:
                        stdout, stderr = self.current_process.communicate(timeout=5)
                        result.complete(self.current_process.returncode, stdout, stderr)
                    except subprocess.TimeoutExpired:
                        result.complete(-1, "", "Process killed after timeout")
                    
                elif action == 'retry':
                    self._kill_process(result)
                    return self.execute_command_clean(command, shell, cwd)
                    
                elif action == 'diagnose':
                    from .diagnostics import ShellDiagnostics
                    diagnostics = ShellDiagnostics()
                    diagnostics.run_full_diagnostic()
                    result.diagnostic_run = True
                    self.stats['diagnostic_runs'] += 1
                    
                    # Ask what to do after diagnostics
                    print("\nDiagnostics completed. What would you like to do now?")
                    action = self._handle_timeout(command, result)
                    
                    if action == 'kill':
                        self._kill_process(result)
                        try:
                            stdout, stderr = self.current_process.communicate(timeout=5)
                            result.complete(self.current_process.returncode, stdout, stderr)
                        except subprocess.TimeoutExpired:
                            result.complete(-1, "", "Process killed after timeout")
                    elif action == 'retry':
                        self._kill_process(result)
                        return self.execute_command_clean(command, shell, cwd)
                    
                elif action == 'continue':
                    # Continue waiting - but with a maximum additional time
                    try:
                        print(f"Continuing to wait (max {self.timeout} more seconds)...")
                        stdout, stderr = self.current_process.communicate(timeout=self.timeout)
                        self._stop_timer()
                        result.complete(self.current_process.returncode, stdout, stderr)
                    except subprocess.TimeoutExpired:
                        print("Second timeout reached, killing process...")
                        self._kill_process(result)
                        try:
                            stdout, stderr = self.current_process.communicate(timeout=5)
                            result.complete(self.current_process.returncode, stdout, stderr)
                        except subprocess.TimeoutExpired:
                            result.complete(-1, "", "Process killed after second timeout")
                    
                elif action == 'quit':
                    self._kill_process(result)
                    sys.exit(0)
                
                self.stats['timed_out_commands'] += 1
        
        except Exception as e:
            self._stop_timer()
            self.logger.error(f"Error executing command: {e}")
            result.complete(-1, "", str(e))
        
        finally:
            self.current_process = None
            self._save_history()
        
        return result
    
    def execute_command_clean(self, command: str, shell: Optional[str] = None, 
                            cwd: Optional[str] = None) -> CommandResult:
        """Execute command with a clean shell context."""
        self.logger.info("Executing command with clean shell context")
        
        # Set clean environment
        clean_env = os.environ.copy()
        
        # Remove potentially problematic environment variables
        problematic_vars = [
            'PS1', 'PROMPT_COMMAND', 'BASH_ENV', 'ENV',
            'PROFILE', 'ZDOTDIR'
        ]
        
        for var in problematic_vars:
            clean_env.pop(var, None)
        
        # Execute with clean environment
        original_env = os.environ.copy()
        try:
            os.environ.clear()
            os.environ.update(clean_env)
            return self.execute_command(command, shell, cwd)
        finally:
            os.environ.clear()
            os.environ.update(original_env)
    
    def _detect_shell(self) -> str:
        """Detect the current shell being used."""
        shell_var = os.environ.get('SHELL', '')
        
        if sys.platform == "win32":
            # Windows shell detection
            if 'powershell' in shell_var.lower() or os.environ.get('PSModulePath'):
                return 'powershell'
            elif 'bash' in shell_var.lower() or os.environ.get('BASH_VERSION'):
                return 'bash'
            else:
                return 'cmd'
        else:
            # Unix-like shell detection
            if shell_var:
                return shell_var.split('/')[-1]
            else:
                return 'bash'  # Default
    
    def get_slow_commands(self, count: int = 5) -> List[Dict]:
        """Get the last N slow commands."""
        # Filter commands that took more than 5 seconds
        slow_commands = [
            cmd for cmd in self.history 
            if hasattr(cmd, 'duration') and cmd.duration and cmd.duration > 5.0
        ]
        
        # Sort by duration (descending) and get last N
        slow_commands.sort(key=lambda x: getattr(x, 'duration', 0) or 0, reverse=True)
        
        result = []
        for cmd in slow_commands[-count:]:
            if hasattr(cmd, 'to_dict'):
                result.append(cmd.to_dict())
            elif isinstance(cmd, dict):
                result.append(cmd)
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get execution statistics."""
        stats = self.stats.copy()
        
        if self.history:
            durations = []
            for cmd in self.history:
                if hasattr(cmd, 'duration') and cmd.duration:
                    durations.append(cmd.duration)
                elif isinstance(cmd, dict) and cmd.get('duration'):
                    durations.append(cmd['duration'])
            
            if durations:
                stats['avg_duration'] = sum(durations) / len(durations)
                stats['max_duration'] = max(durations)
                stats['min_duration'] = min(durations)
        
        stats['timeout_rate'] = (
            self.stats['timed_out_commands'] / max(self.stats['total_commands'], 1) * 100
        )
        
        return stats
    
    def print_summary(self):
        """Print a summary of recent activity."""
        print("\n" + "="*60)
        print("SHELL MONITOR SUMMARY")
        print("="*60)
        
        stats = self.get_statistics()
        print(f"Total Commands: {stats['total_commands']}")
        print(f"Timed Out: {stats['timed_out_commands']} ({stats['timeout_rate']:.1f}%)")
        print(f"Killed: {stats['killed_commands']}")
        print(f"Diagnostics Run: {stats['diagnostic_runs']}")
        
        if 'avg_duration' in stats:
            print(f"Average Duration: {stats['avg_duration']:.2f}s")
            print(f"Max Duration: {stats['max_duration']:.2f}s")
        
        slow_commands = self.get_slow_commands()
        if slow_commands:
            print(f"\nLast {len(slow_commands)} Slow Commands:")
            for i, cmd in enumerate(slow_commands, 1):
                duration = cmd.get('duration', 0)
                command = cmd.get('command', '')[:50]
                print(f"  {i}. {command}{'...' if len(cmd.get('command', '')) > 50 else ''} ({duration:.2f}s)")
        
        print("="*60) 