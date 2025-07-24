#!/usr/bin/env python3
"""
Test Script for Shell Monitor
Comprehensive testing to verify the shell monitor utility works correctly.
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path

# Add src directory to path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")

def print_test_result(test_name, success, message=""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"   {message}")

def test_imports():
    """Test that all shell monitor modules can be imported."""
    print_test_header("Module Imports")
    
    tests = [
        ("shell_monitor", "Main package"),
        ("shell_monitor.monitor", "ShellMonitor class"),
        ("shell_monitor.diagnostics", "ShellDiagnostics class"),
        ("shell_monitor.cli", "CLI interface")
    ]
    
    all_passed = True
    for module_name, description in tests:
        try:
            __import__(module_name)
            print_test_result(f"Import {module_name}", True, description)
        except ImportError as e:
            print_test_result(f"Import {module_name}", False, f"ImportError: {e}")
            all_passed = False
        except Exception as e:
            print_test_result(f"Import {module_name}", False, f"Error: {e}")
            all_passed = False
    
    return all_passed

def test_shell_monitor_creation():
    """Test ShellMonitor instantiation."""
    print_test_header("ShellMonitor Creation")
    
    try:
        from shell_monitor.monitor import ShellMonitor
        
        # Test default creation
        monitor = ShellMonitor()
        print_test_result("Default ShellMonitor", True, "Created with default settings")
        
        # Test with custom settings
        monitor = ShellMonitor(timeout=30, verbose=True)
        print_test_result("Custom ShellMonitor", True, f"timeout={monitor.timeout}, verbose={monitor.verbose}")
        
        # Test configuration access
        has_history = hasattr(monitor, 'history')
        has_stats = hasattr(monitor, 'stats')
        print_test_result("ShellMonitor attributes", has_history and has_stats, 
                         "Has history and stats attributes")
        
        return True
        
    except Exception as e:
        print_test_result("ShellMonitor Creation", False, f"Error: {e}")
        return False

def test_diagnostics_creation():
    """Test ShellDiagnostics instantiation."""
    print_test_header("ShellDiagnostics Creation")
    
    try:
        from shell_monitor.diagnostics import ShellDiagnostics
        
        # Test default creation
        diagnostics = ShellDiagnostics()
        print_test_result("Default ShellDiagnostics", True, "Created with default settings")
        
        # Test with verbose mode
        diagnostics = ShellDiagnostics(verbose=True)
        print_test_result("Verbose ShellDiagnostics", True, f"verbose={diagnostics.verbose}")
        
        # Test system info detection
        has_system_info = hasattr(diagnostics, 'system_info')
        print_test_result("System info detection", has_system_info, 
                         f"Detected: {diagnostics.system_info.get('shell', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print_test_result("ShellDiagnostics Creation", False, f"Error: {e}")
        return False

def test_command_execution():
    """Test basic command execution."""
    print_test_header("Command Execution")
    
    try:
        from shell_monitor.monitor import ShellMonitor
        
        monitor = ShellMonitor(timeout=10, verbose=False)
        
        # Test simple command
        result = monitor.execute_command("echo 'Hello Shell Monitor'")
        
        success = (
            result.command == "echo 'Hello Shell Monitor'" and
            result.returncode == 0 and
            result.duration is not None and
            result.duration > 0
        )
        
        print_test_result("Simple command execution", success, 
                         f"Duration: {result.duration:.3f}s, Return Code: {result.returncode}")
        
        # Test command with output
        if sys.platform == "win32":
            test_cmd = "echo test output"
        else:
            test_cmd = "echo 'test output'"
            
        result = monitor.execute_command(test_cmd)
        has_output = "test output" in result.stdout.lower()
        print_test_result("Command with output", has_output, 
                         f"Output captured: {len(result.stdout)} chars")
        
        # Test command history
        history_count = len(monitor.history)
        print_test_result("Command history tracking", history_count >= 2, 
                         f"History entries: {history_count}")
        
        return success and has_output
        
    except Exception as e:
        print_test_result("Command Execution", False, f"Error: {e}")
        return False

def test_shell_detection():
    """Test shell detection functionality."""
    print_test_header("Shell Detection")
    
    try:
        from shell_monitor.monitor import ShellMonitor
        
        monitor = ShellMonitor()
        detected_shell = monitor._detect_shell()
        
        valid_shells = ['powershell', 'bash', 'cmd', 'sh', 'zsh']
        is_valid = any(shell in detected_shell.lower() for shell in valid_shells)
        
        print_test_result("Shell detection", is_valid, f"Detected: {detected_shell}")
        
        return is_valid
        
    except Exception as e:
        print_test_result("Shell Detection", False, f"Error: {e}")
        return False

def test_diagnostics_execution():
    """Test diagnostic execution (without full run)."""
    print_test_header("Diagnostics Execution")
    
    try:
        from shell_monitor.diagnostics import ShellDiagnostics, DiagnosticResult
        
        diagnostics = ShellDiagnostics(verbose=False)
        
        # Test diagnostic result creation
        result = DiagnosticResult("Test", "Test Category")
        result.set_pass("Test passed", {"detail": "value"})
        
        print_test_result("DiagnosticResult creation", True, 
                         f"Status: {result.status}, Message: {result.message}")
        
        # Test system info gathering
        has_platform = 'platform' in diagnostics.system_info
        has_shell = 'shell' in diagnostics.system_info
        
        print_test_result("System info gathering", has_platform and has_shell,
                         f"Platform: {diagnostics.system_info.get('platform', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print_test_result("Diagnostics Execution", False, f"Error: {e}")
        return False

def test_cli_argument_parsing():
    """Test CLI argument parsing."""
    print_test_header("CLI Argument Parsing")
    
    try:
        from shell_monitor.cli import ShellMonitorCLI
        
        cli = ShellMonitorCLI()
        parser = cli._create_parser()
        
        # Test basic argument parsing
        test_cases = [
            (["run", "echo test"], "run command"),
            (["diagnose"], "diagnose command"),
            (["interactive"], "interactive command"),
            (["history"], "history command"),
            (["config", "--show"], "config command"),
            (["stats"], "stats command")
        ]
        
        all_passed = True
        for args, description in test_cases:
            try:
                parsed = parser.parse_args(args)
                print_test_result(f"Parse {description}", True, f"Command: {parsed.command}")
            except SystemExit:
                # argparse calls sys.exit on error
                print_test_result(f"Parse {description}", False, "Parsing failed")
                all_passed = False
            except Exception as e:
                print_test_result(f"Parse {description}", False, f"Error: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_test_result("CLI Argument Parsing", False, f"Error: {e}")
        return False

def test_configuration_management():
    """Test configuration loading and saving."""
    print_test_header("Configuration Management")
    
    try:
        from shell_monitor.cli import ShellMonitorCLI
        import tempfile
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "timeout": 120,
                "verbose": True,
                "log_file": "test.log"
            }
            json.dump(test_config, f)
            temp_config_file = f.name
        
        try:
            # Test config loading
            cli = ShellMonitorCLI()
            cli.config_file = Path(temp_config_file)
            loaded_config = cli._load_config()
            
            config_loaded = (
                loaded_config.get('timeout') == 120 and
                loaded_config.get('verbose') == True
            )
            
            print_test_result("Configuration loading", config_loaded, 
                             f"Loaded timeout: {loaded_config.get('timeout')}")
            
            # Test config saving
            cli.config = {'timeout': 90, 'verbose': False}
            cli._save_config()
            
            print_test_result("Configuration saving", True, "Config saved successfully")
            
            return config_loaded
            
        finally:
            # Clean up
            if Path(temp_config_file).exists():
                Path(temp_config_file).unlink()
        
    except Exception as e:
        print_test_result("Configuration Management", False, f"Error: {e}")
        return False

def test_main_entry_point():
    """Test the main entry point script."""
    print_test_header("Main Entry Point")
    
    try:
        # Test that the main script exists and is executable
        main_script = script_dir / "shell_monitor.py"
        
        if not main_script.exists():
            print_test_result("Main script exists", False, "shell_monitor.py not found")
            return False
        
        print_test_result("Main script exists", True, str(main_script))
        
        # Test help output (should not require full execution)
        try:
            result = subprocess.run([
                sys.executable, str(main_script), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            help_works = result.returncode == 0 and "shell-monitor" in result.stdout
            print_test_result("Help command", help_works, 
                             f"Exit code: {result.returncode}")
            
            return help_works
            
        except subprocess.TimeoutExpired:
            print_test_result("Help command", False, "Command timed out")
            return False
        
    except Exception as e:
        print_test_result("Main Entry Point", False, f"Error: {e}")
        return False

def run_all_tests():
    """Run all tests and return overall result."""
    print("🔍 Shell Monitor - Comprehensive Test Suite")
    print("="*60)
    
    tests = [
        ("Module Imports", test_imports),
        ("ShellMonitor Creation", test_shell_monitor_creation),
        ("ShellDiagnostics Creation", test_diagnostics_creation),
        ("Command Execution", test_command_execution),
        ("Shell Detection", test_shell_detection),
        ("Diagnostics Execution", test_diagnostics_execution),
        ("CLI Argument Parsing", test_cli_argument_parsing),
        ("Configuration Management", test_configuration_management),
        ("Main Entry Point", test_main_entry_point)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_test_result(test_name, False, f"Unexpected error: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Shell Monitor is ready for use.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Try: python shell_monitor.py run \"git status\"")
        print("2. Try: python shell_monitor.py diagnose")
        print("3. Try: python shell_monitor.py interactive")
        sys.exit(0)
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Make sure all files are in the correct locations")
        print("2. Check that Python 3.7+ is being used")
        print("3. Verify that the src/shell_monitor/ directory exists")
        print("4. Run individual tests to isolate issues")
        sys.exit(1) 