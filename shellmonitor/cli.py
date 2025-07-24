"""
Command Line Interface for Shell Monitor
Provides interactive CLI for monitoring shell commands and running diagnostics.
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import Optional, List
import signal

from .monitor import ShellMonitor
from .diagnostics import ShellDiagnostics

class ShellMonitorCLI:
    """Command line interface for the shell monitor."""
    
    def __init__(self):
        self.monitor: Optional[ShellMonitor] = None
        self.config_file = Path.home() / ".shell_monitor_config.json"
        self.config = self._load_config()
        
        # Setup signal handlers for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        default_config = {
            'timeout': 60,
            'verbose': False,
            'log_file': None,
            'auto_diagnose': False,
            'max_history': 100
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception:
            pass  # Use defaults if config file is corrupted
        
        return default_config
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        print("\n\n🛑 Interrupted. Cleaning up...")
        if self.monitor:
            self.monitor.stop_auto_commit_monitoring()
            self.monitor.print_summary()
        sys.exit(0)
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            prog='shell-monitor',
            description='Monitor shell command execution and diagnose performance issues',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  shell-monitor run "git status"              # Monitor a single command
  shell-monitor run "npm install" --timeout 300  # Set custom timeout
  shell-monitor diagnose                      # Run diagnostic tests
  shell-monitor interactive                   # Start interactive mode
  shell-monitor history                       # Show command history
  shell-monitor config --timeout 120         # Configure settings
            """
        )
        
        parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
        parser.add_argument('--verbose', '-v', action='store_true', 
                          help='Enable verbose output')
        parser.add_argument('--timeout', '-t', type=int, default=self.config['timeout'],
                          help=f'Command timeout in seconds (default: {self.config["timeout"]})')
        parser.add_argument('--log-file', '-l', type=str, default=self.config['log_file'],
                          help='Log file path for detailed logging')
        parser.add_argument('--shell', '-s', type=str, 
                          help='Force specific shell (powershell, bash, cmd)')
        parser.add_argument('--cwd', '-d', type=str, 
                          help='Working directory for command execution')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Run command
        run_parser = subparsers.add_parser('run', help='Run a single command with monitoring')
        run_parser.add_argument('cmd', help='Command to execute')
        run_parser.add_argument('--clean', action='store_true', 
                               help='Run with clean shell environment')
        run_parser.add_argument('--no-diagnostics', action='store_true',
                               help='Disable auto-diagnostics on timeout')
        
        # Diagnose command
        diag_parser = subparsers.add_parser('diagnose', help='Run diagnostic tests')
        diag_parser.add_argument('--save-report', action='store_true',
                                help='Save detailed report to file')
        
        # Interactive mode
        interactive_parser = subparsers.add_parser('interactive', help='Start interactive mode')
        interactive_parser.add_argument('--auto-diagnose', action='store_true',
                                       help='Automatically run diagnostics on timeouts')
        
        # History command
        history_parser = subparsers.add_parser('history', help='Show command execution history')
        history_parser.add_argument('--slow-only', action='store_true',
                                   help='Show only slow commands (>5s)')
        history_parser.add_argument('--count', '-n', type=int, default=10,
                                   help='Number of commands to show (default: 10)')
        
        # Configuration command
        config_parser = subparsers.add_parser('config', help='Configure shell monitor settings')
        config_parser.add_argument('--show', action='store_true',
                                  help='Show current configuration')
        config_parser.add_argument('--reset', action='store_true',
                                  help='Reset to default configuration')
        config_parser.add_argument('--set-timeout', type=int,
                                  help='Set default timeout')
        config_parser.add_argument('--set-log-file', type=str,
                                  help='Set default log file')
        config_parser.add_argument('--enable-auto-diagnose', action='store_true',
                                  help='Enable automatic diagnostics')
        config_parser.add_argument('--disable-auto-diagnose', action='store_true',
                                  help='Disable automatic diagnostics')
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show execution statistics')
        
        return parser
    
    def run_single_command(self, args) -> int:
        """Run a single command with monitoring."""
        self.monitor = ShellMonitor(
            timeout=args.timeout,
            log_file=args.log_file,
            verbose=args.verbose
        )
        
        print(f"🚀 Monitoring command: {args.cmd}")
        print(f"⏱️  Timeout: {args.timeout}s")
        
        if args.clean:
            print("🧹 Using clean shell environment")
            result = self.monitor.execute_command_clean(args.cmd, args.shell, args.cwd)
        else:
            result = self.monitor.execute_command(args.cmd, args.shell, args.cwd)
        
        # Print results
        print(f"\n📋 Command Results:")
        print(f"   Command: {result.command}")
        print(f"   Duration: {result.duration:.2f}s" if result.duration else "   Duration: N/A")
        print(f"   Return Code: {result.returncode}")
        
        if result.timed_out:
            print("   ⚠️  Command timed out")
        if result.killed:
            print("   🔪 Command was killed")
        if result.diagnostic_run:
            print("   🔍 Diagnostics were run")
        
        if args.verbose:
            if result.stdout:
                print(f"\n📤 STDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"\n📤 STDERR:\n{result.stderr}")
        
        return result.returncode if result.returncode is not None else 1
    
    def run_diagnostics(self, args) -> int:
        """Run diagnostic tests."""
        print("🔍 Starting Shell Performance Diagnostics...")
        
        diagnostics = ShellDiagnostics(verbose=args.verbose)
        results = diagnostics.run_full_diagnostic()
        
        # Count results by status
        passed = len([r for r in results if r.status == 'pass'])
        warnings = len([r for r in results if r.status == 'warning'])
        failures = len([r for r in results if r.status == 'fail'])
        
        print(f"\n📊 Summary: {passed} passed, {warnings} warnings, {failures} failures")
        
        return 0 if failures == 0 else 1
    
    def run_interactive_mode(self, args) -> int:
        """Run interactive command mode."""
        self.monitor = ShellMonitor(
            timeout=args.timeout,
            log_file=args.log_file,
            verbose=args.verbose
        )
        
        print("🖥️  Shell Monitor - Interactive Mode")
        print("="*50)
        print("Enter shell commands to monitor. Type 'exit' to quit.")
        print("Available commands:")
        print("  exit, quit     - Exit interactive mode")
        print("  diagnose       - Run diagnostic tests")
        print("  history        - Show command history")
        print("  stats          - Show execution statistics")
        print("  clear          - Clear screen")
        print("  help           - Show this help")
        print("-"*50)
        
        try:
            while True:
                try:
                    command = input("\n🔍 shell-monitor> ").strip()
                    
                    if not command:
                        continue
                    
                    if command.lower() in ['exit', 'quit']:
                        break
                    elif command.lower() == 'diagnose':
                        diagnostics = ShellDiagnostics(verbose=args.verbose)
                        diagnostics.run_full_diagnostic()
                        continue
                    elif command.lower() == 'history':
                        self._show_history(count=5)
                        continue
                    elif command.lower() == 'stats':
                        self._show_stats()
                        continue
                    elif command.lower() == 'clear':
                        os.system('cls' if os.name == 'nt' else 'clear')
                        continue
                    elif command.lower() == 'help':
                        print("\nAvailable commands:")
                        print("  exit, quit     - Exit interactive mode")
                        print("  diagnose       - Run diagnostic tests")
                        print("  history        - Show command history")
                        print("  stats          - Show execution statistics")
                        print("  clear          - Clear screen")
                        print("  help           - Show this help")
                        continue
                    
                    # Execute the command
                    result = self.monitor.execute_command(command)
                    
                    # Show brief result
                    status = "✅" if result.returncode == 0 else "❌"
                    duration = f" ({result.duration:.2f}s)" if result.duration else ""
                    print(f"{status} Command completed{duration}")
                    
                    if result.timed_out and args.auto_diagnose:
                        print("🔍 Running auto-diagnostics...")
                        diagnostics = ShellDiagnostics(verbose=False)
                        diagnostics.run_full_diagnostic()
                
                except KeyboardInterrupt:
                    print("\n\n🛑 Use 'exit' to quit interactive mode.")
                    continue
                except EOFError:
                    break
        
        finally:
            if self.monitor:
                self.monitor.print_summary()
        
        return 0
    
    def show_history(self, args) -> int:
        """Show command execution history."""
        self._show_history(args.count, args.slow_only)
        return 0
    
    def _show_history(self, count: int = 10, slow_only: bool = False):
        """Internal method to show command history."""
        # Create a temporary monitor to access history
        temp_monitor = ShellMonitor()
        
        if not temp_monitor.history:
            print("📭 No command history found.")
            return
        
        history = temp_monitor.history
        if slow_only:
            history = [cmd for cmd in history if cmd.duration and cmd.duration > 5.0]
        
        if not history:
            print("📭 No slow commands found in history.")
            return
        
        # Get last N commands
        recent_commands = history[-count:] if len(history) > count else history
        
        print(f"\n📜 Command History (last {len(recent_commands)} commands):")
        print("="*60)
        
        for i, cmd in enumerate(recent_commands, 1):
            duration = f"{cmd.duration:.2f}s" if cmd.duration else "N/A"
            status = "⚠️" if cmd.timed_out else ("❌" if cmd.returncode != 0 else "✅")
            command_short = cmd.command[:50] + "..." if len(cmd.command) > 50 else cmd.command
            
            print(f"{i:2d}. {status} {command_short} ({duration})")
            
            if cmd.timed_out:
                print(f"      ⚠️  Timed out")
            if cmd.killed:
                print(f"      🔪 Killed")
            if cmd.diagnostic_run:
                print(f"      🔍 Diagnostics run")
    
    def _show_stats(self):
        """Internal method to show execution statistics."""
        temp_monitor = ShellMonitor()
        stats = temp_monitor.get_statistics()
        
        print(f"\n📊 Execution Statistics:")
        print("="*40)
        print(f"Total Commands: {stats['total_commands']}")
        print(f"Timed Out: {stats['timed_out_commands']} ({stats['timeout_rate']:.1f}%)")
        print(f"Killed: {stats['killed_commands']}")
        print(f"Diagnostics Run: {stats['diagnostic_runs']}")
        
        if 'avg_duration' in stats:
            print(f"Average Duration: {stats['avg_duration']:.2f}s")
            print(f"Max Duration: {stats['max_duration']:.2f}s")
            print(f"Min Duration: {stats['min_duration']:.2f}s")
    
    def configure_settings(self, args) -> int:
        """Configure shell monitor settings."""
        if args.show:
            print("📋 Current Configuration:")
            print("="*30)
            for key, value in self.config.items():
                print(f"  {key}: {value}")
            return 0
        
        if args.reset:
            self.config = {
                'timeout': 60,
                'verbose': False,
                'log_file': None,
                'auto_diagnose': False,
                'max_history': 100
            }
            self._save_config()
            print("✅ Configuration reset to defaults")
            return 0
        
        # Update configuration
        updated = False
        
        if args.set_timeout:
            self.config['timeout'] = args.set_timeout
            updated = True
            print(f"✅ Timeout set to {args.set_timeout}s")
        
        if args.set_log_file:
            self.config['log_file'] = args.set_log_file
            updated = True
            print(f"✅ Log file set to {args.set_log_file}")
        
        if args.enable_auto_diagnose:
            self.config['auto_diagnose'] = True
            updated = True
            print("✅ Auto-diagnostics enabled")
        
        if args.disable_auto_diagnose:
            self.config['auto_diagnose'] = False
            updated = True
            print("✅ Auto-diagnostics disabled")
        
        if updated:
            self._save_config()
        else:
            print("ℹ️  No configuration changes made. Use --help for options.")
        
        return 0
    
    def show_statistics(self, args) -> int:
        """Show execution statistics."""
        self._show_stats()
        
        # Also show slow commands
        temp_monitor = ShellMonitor()
        slow_commands = temp_monitor.get_slow_commands()
        
        if slow_commands:
            print(f"\n🐌 Slowest Commands:")
            print("="*40)
            for i, cmd in enumerate(slow_commands, 1):
                duration = cmd.get('duration', 0)
                command = cmd.get('command', '')[:40]
                print(f"{i}. {command}{'...' if len(cmd.get('command', '')) > 40 else ''} ({duration:.2f}s)")
        
        return 0
    
    def run(self, argv: Optional[List[str]] = None) -> int:
        """Run the CLI application."""
        parser = self._create_parser()
        args = parser.parse_args(argv)
        
        # Update config with command line args
        if hasattr(args, 'verbose') and args.verbose:
            self.config['verbose'] = True
        if hasattr(args, 'timeout') and args.timeout != self.config['timeout']:
            self.config['timeout'] = args.timeout
        if hasattr(args, 'log_file') and args.log_file != self.config['log_file']:
            self.config['log_file'] = args.log_file
        
        # Route to appropriate handler
        try:
            if args.command == 'run':
                return self.run_single_command(args)
            elif args.command == 'diagnose':
                return self.run_diagnostics(args)
            elif args.command == 'interactive':
                return self.run_interactive_mode(args)
            elif args.command == 'history':
                return self.show_history(args)
            elif args.command == 'config':
                return self.configure_settings(args)
            elif args.command == 'stats':
                return self.show_statistics(args)
            else:
                # No subcommand provided, show help
                parser.print_help()
                return 0
                
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.config.get('verbose', False):
                import traceback
                traceback.print_exc()
            return 1

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI application."""
    cli = ShellMonitorCLI()
    return cli.run(argv)

if __name__ == '__main__':
    sys.exit(main()) 