"""
Shell Diagnostics Engine
Comprehensive diagnostic tools to identify shell performance issues and bottlenecks.
"""

import os
import sys
import subprocess
import time
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import tempfile
from collections import defaultdict

class DiagnosticResult:
    """Represents the result of a diagnostic test."""
    
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.status: str = "pending"  # pending, pass, warning, fail
        self.message: str = ""
        self.details: Dict[str, Any] = {}
        self.recommendations: List[str] = []
        self.execution_time: Optional[float] = None
    
    def set_pass(self, message: str, details: Optional[Dict] = None):
        """Mark test as passed."""
        self.status = "pass"
        self.message = message
        self.details = details or {}
    
    def set_warning(self, message: str, details: Optional[Dict] = None, recommendations: Optional[List[str]] = None):
        """Mark test as warning."""
        self.status = "warning"
        self.message = message
        self.details = details or {}
        self.recommendations = recommendations or []
    
    def set_fail(self, message: str, details: Optional[Dict] = None, recommendations: Optional[List[str]] = None):
        """Mark test as failed."""
        self.status = "fail"
        self.message = message
        self.details = details or {}
        self.recommendations = recommendations or []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            'name': self.name,
            'category': self.category,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'recommendations': self.recommendations,
            'execution_time': self.execution_time
        }

class ShellDiagnostics:
    """Comprehensive shell performance diagnostics."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger('shell_diagnostics')
        self.results: List[DiagnosticResult] = []
        
        # System information
        self.system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture(),
            'python_version': sys.version,
            'shell': self._detect_current_shell()
        }
    
    def _detect_current_shell(self) -> str:
        """Detect the current shell being used."""
        shell_var = os.environ.get('SHELL', '')
        
        if sys.platform == "win32":
            if 'powershell' in shell_var.lower() or os.environ.get('PSModulePath'):
                return 'PowerShell'
            elif 'bash' in shell_var.lower() or os.environ.get('BASH_VERSION'):
                return 'Git Bash'
            else:
                return 'CMD'
        else:
            if shell_var:
                return shell_var.split('/')[-1]
            else:
                return 'bash'
    
    def _time_execution(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Time the execution of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    
    def _run_command_with_timing(self, command: List[str], timeout: int = 10) -> Tuple[subprocess.CompletedProcess, float]:
        """Run a command and measure its execution time with strict timeout."""
        start_time = time.time()
        try:
            # Use shorter default timeout and ensure proper process cleanup
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                preexec_fn=os.setsid if sys.platform != "win32" else None
            )
            execution_time = time.time() - start_time
            return result, execution_time
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            # Create a mock result for timeout
            result = subprocess.CompletedProcess(
                command, -1, "", f"Command timed out after {timeout}s"
            )
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            # Create a mock result for other errors
            result = subprocess.CompletedProcess(
                command, -1, "", f"Command failed: {str(e)}"
            )
            return result, execution_time
    
    def run_full_diagnostic(self) -> List[DiagnosticResult]:
        """Run complete diagnostic suite with timeout protection."""
        print("\n🔍 Running Shell Performance Diagnostics...")
        print("="*60)
        
        # Clear previous results
        self.results = []
        
        diagnostic_functions = [
            ("Shell Environment", self._diagnose_shell_environment),
            ("PowerShell Profile", self._diagnose_powershell_profile),
            ("PATH Configuration", self._diagnose_path_configuration),
            ("Git Environment", self._diagnose_git_environment),
            ("Command Performance", self._diagnose_command_performance),
            ("System Resources", self._diagnose_system_resources)
        ]
        
        for category_name, diagnostic_func in diagnostic_functions:
            try:
                print(f"🔍 Testing {category_name}...")
                # Add timeout to each diagnostic section
                start_time = time.time()
                diagnostic_func()
                elapsed = time.time() - start_time
                
                if elapsed > 15:  # Warn if any section takes too long
                    print(f"⚠️  {category_name} took {elapsed:.1f}s (unexpectedly long)")
                    
            except Exception as e:
                print(f"❌ Error in {category_name}: {e}")
                # Add an error result
                error_result = DiagnosticResult(f"{category_name} Error", category_name)
                error_result.set_fail(f"Diagnostic section failed: {str(e)}")
                self.results.append(error_result)
        
        # Print results
        self._print_diagnostic_results()
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _diagnose_shell_environment(self):
        """Diagnose shell environment configuration."""
        category = "Shell Environment"
        
        # Test 1: Shell detection
        result = DiagnosticResult("Shell Detection", category)
        detected_shell = self.system_info['shell']
        result.set_pass(f"Detected shell: {detected_shell}", {'shell': detected_shell})
        self.results.append(result)
        
        # Test 2: Environment variable count
        result = DiagnosticResult("Environment Variables", category)
        env_count = len(os.environ)
        if env_count > 500:
            result.set_warning(
                f"High number of environment variables: {env_count}",
                {'count': env_count},
                ["Consider cleaning up unnecessary environment variables"]
            )
        else:
            result.set_pass(f"Environment variable count: {env_count}", {'count': env_count})
        self.results.append(result)
        
        # Test 3: Shell startup files
        if sys.platform == "win32":
            self._check_windows_shell_startup()
        else:
            self._check_unix_shell_startup()
    
    def _check_windows_shell_startup(self):
        """Check Windows shell startup configuration."""
        category = "Shell Environment"
        
        # Check for common startup scripts
        startup_files = []
        potential_files = [
            Path.home() / ".bashrc",
            Path.home() / ".bash_profile",
            Path.home() / ".profile",
        ]
        
        for file_path in potential_files:
            if file_path.exists():
                size = file_path.stat().st_size
                startup_files.append({'path': str(file_path), 'size': size})
        
        result = DiagnosticResult("Startup Scripts", category)
        if startup_files:
            large_files = [f for f in startup_files if f['size'] > 10000]  # > 10KB
            if large_files:
                result.set_warning(
                    f"Found {len(large_files)} large startup script(s)",
                    {'files': startup_files},
                    ["Consider optimizing large startup scripts", 
                     "Move heavy operations to separate scripts"]
                )
            else:
                result.set_pass(f"Found {len(startup_files)} startup script(s)", {'files': startup_files})
        else:
            result.set_pass("No startup scripts found", {'files': []})
        self.results.append(result)
    
    def _check_unix_shell_startup(self):
        """Check Unix shell startup configuration."""
        category = "Shell Environment"
        
        startup_files = []
        potential_files = [
            Path.home() / ".bashrc",
            Path.home() / ".bash_profile",
            Path.home() / ".zshrc",
            Path.home() / ".profile",
            "/etc/bash.bashrc",
            "/etc/profile"
        ]
        
        for file_path in potential_files:
            if file_path.exists():
                try:
                    size = file_path.stat().st_size
                    startup_files.append({'path': str(file_path), 'size': size})
                except (OSError, PermissionError):
                    continue
        
        result = DiagnosticResult("Startup Scripts", category)
        if startup_files:
            large_files = [f for f in startup_files if f['size'] > 10000]
            if large_files:
                result.set_warning(
                    f"Found {len(large_files)} large startup script(s)",
                    {'files': startup_files},
                    ["Consider optimizing large startup scripts"]
                )
            else:
                result.set_pass(f"Found {len(startup_files)} startup script(s)", {'files': startup_files})
        else:
            result.set_pass("No startup scripts found", {'files': []})
        self.results.append(result)
    
    def _diagnose_powershell_profile(self):
        """Diagnose PowerShell profile configuration with timeout protection."""
        if sys.platform != "win32" or self.system_info['shell'] != 'PowerShell':
            return
        
        category = "PowerShell Profile"
        
        # Test PowerShell profile locations with shorter timeout
        profile_locations = [
            "$PROFILE.CurrentUserCurrentHost",
            "$PROFILE.CurrentUserAllHosts",
            "$PROFILE.AllUsersCurrentHost",
            "$PROFILE.AllUsersAllHosts"
        ]
        
        result = DiagnosticResult("Profile Detection", category)
        profiles_found = []
        
        try:
            for profile_var in profile_locations:
                cmd_result, exec_time = self._run_command_with_timing([
                    "powershell", "-NoProfile", "-Command",
                    f"if (Test-Path {profile_var}) {{ Get-Item {profile_var} | Select-Object FullName, Length }}"
                ], timeout=5)  # Shorter timeout
                
                if cmd_result.returncode == 0 and cmd_result.stdout.strip():
                    profiles_found.append({
                        'location': profile_var,
                        'details': cmd_result.stdout.strip()
                    })
            
            if profiles_found:
                result.set_pass(f"Found {len(profiles_found)} PowerShell profile(s)", 
                              {'profiles': profiles_found})
            else:
                result.set_pass("No PowerShell profiles found", {'profiles': []})
                
        except Exception as e:
            result.set_warning(f"Could not check PowerShell profiles: {e}")
        
        self.results.append(result)
    
    def _diagnose_path_configuration(self):
        """Diagnose PATH environment variable configuration."""
        category = "PATH Configuration"
        
        # Test 1: PATH length and entry count
        result = DiagnosticResult("PATH Analysis", category)
        path_env = os.environ.get('PATH', '')
        path_entries = [p.strip() for p in path_env.split(os.pathsep) if p.strip()]
        
        path_info = {
            'total_length': len(path_env),
            'entry_count': len(path_entries),
            'entries': path_entries
        }
        
        if len(path_entries) > 50:
            result.set_warning(
                f"PATH has many entries: {len(path_entries)}",
                path_info,
                ["Consider cleaning up unused PATH entries",
                 "Remove duplicate entries"]
            )
        elif len(path_env) > 8192:  # Windows PATH limit
            result.set_fail(
                f"PATH is very long: {len(path_env)} characters",
                path_info,
                ["PATH is approaching system limits",
                 "Remove unnecessary entries immediately"]
            )
        else:
            result.set_pass(f"PATH has {len(path_entries)} entries ({len(path_env)} chars)", path_info)
        
        self.results.append(result)
        
        # Test 2: PATH entry validation (with limits to prevent hanging)
        result = DiagnosticResult("PATH Validation", category)
        invalid_entries = []
        duplicate_entries = []
        
        seen_paths = set()
        # Limit validation to first 30 entries to prevent hanging on very long PATHs
        entries_to_check = path_entries[:30]
        
        for entry in entries_to_check:
            # Check for duplicates
            if entry.lower() in seen_paths:
                duplicate_entries.append(entry)
            seen_paths.add(entry.lower())
            
            # Check if path exists (with timeout protection)
            try:
                if not Path(entry).exists():
                    invalid_entries.append(entry)
            except (OSError, ValueError):
                # Invalid path format
                invalid_entries.append(entry)
        
        issues = []
        if invalid_entries:
            issues.append(f"{len(invalid_entries)} non-existent paths")
        if duplicate_entries:
            issues.append(f"{len(duplicate_entries)} duplicate paths")
        if len(path_entries) > 30:
            issues.append(f"Only checked first 30 of {len(path_entries)} entries")
        
        if issues:
            result.set_warning(
                f"PATH issues found: {', '.join(issues)}",
                {
                    'invalid_entries': invalid_entries[:10],  # Limit output size
                    'duplicate_entries': duplicate_entries[:10],
                    'total_entries': len(path_entries),
                    'checked_entries': len(entries_to_check)
                },
                ["Remove non-existent PATH entries",
                 "Remove duplicate PATH entries",
                 "Use a PATH manager tool"]
            )
        else:
            result.set_pass("All checked PATH entries are valid and unique")
        
        self.results.append(result)
    
    def _diagnose_git_environment(self):
        """Diagnose Git environment and hooks with timeout protection."""
        category = "Git Environment"
        
        # Test 1: Git availability and version
        result = DiagnosticResult("Git Installation", category)
        try:
            cmd_result, exec_time = self._run_command_with_timing(["git", "--version"], timeout=5)
            if cmd_result.returncode == 0:
                version = cmd_result.stdout.strip()
                result.set_pass(f"Git found: {version}", 
                              {'version': version, 'check_time': exec_time})
            else:
                result.set_fail("Git not found or not working", 
                              {'error': cmd_result.stderr})
        except Exception as e:
            result.set_fail(f"Error checking Git: {e}")
        
        self.results.append(result)
        
        # Test 2: Git hooks in current repository
        result = DiagnosticResult("Git Hooks", category)
        try:
            git_dir = Path.cwd() / ".git"
            if git_dir.exists():
                hooks_dir = git_dir / "hooks"
                if hooks_dir.exists():
                    hooks = list(hooks_dir.glob("*"))
                    active_hooks = [h for h in hooks if h.is_file() and not h.name.endswith('.sample')]
                    
                    if active_hooks:
                        hook_info = []
                        for hook in active_hooks:
                            try:
                                size = hook.stat().st_size
                                hook_info.append({'name': hook.name, 'size': size})
                            except OSError:
                                continue
                        
                        large_hooks = [h for h in hook_info if h['size'] > 1000]  # > 1KB
                        if large_hooks:
                            result.set_warning(
                                f"Found {len(large_hooks)} large Git hook(s)",
                                {'hooks': hook_info},
                                ["Consider optimizing large Git hooks",
                                 "Move complex logic to external scripts"]
                            )
                        else:
                            result.set_pass(f"Found {len(active_hooks)} Git hook(s)", 
                                          {'hooks': hook_info})
                    else:
                        result.set_pass("No active Git hooks found", {'hooks': []})
                else:
                    result.set_pass("No Git hooks directory found", {'hooks': []})
            else:
                result.set_pass("Not in a Git repository", {'hooks': []})
                
        except Exception as e:
            result.set_warning(f"Error checking Git hooks: {e}")
        
        self.results.append(result)
    
    def _diagnose_command_performance(self):
        """Diagnose performance of common commands with strict timeouts."""
        category = "Command Performance"
        
        # Test common Git commands with very short timeouts
        git_commands = [
            (["git", "status"], "git status"),
            (["git", "tag", "-l"], "git tag -l"),
            (["git", "branch"], "git branch"),
            (["git", "log", "--oneline", "-1"], "git log")
        ]
        
        for cmd, name in git_commands:
            result = DiagnosticResult(f"Command: {name}", category)
            exec_time = 0
            try:
                cmd_result, exec_time = self._run_command_with_timing(cmd, timeout=8)  # Strict 8s timeout
                
                if cmd_result.returncode == 0:
                    if exec_time > 8:
                        result.set_fail(
                            f"Timed out: >{exec_time:.2f}s",
                            {'execution_time': exec_time, 'command': name},
                            [f"'{name}' is hanging or extremely slow",
                             "Check repository status and network connectivity"]
                        )
                    elif exec_time > 5:
                        result.set_warning(
                            f"Very slow: {exec_time:.2f}s",
                            {'execution_time': exec_time, 'command': name},
                            [f"'{name}' is much slower than expected",
                             "Check repository size and Git configuration"]
                        )
                    elif exec_time > 2:
                        result.set_warning(
                            f"Slow: {exec_time:.2f}s",
                            {'execution_time': exec_time, 'command': name},
                            [f"'{name}' is slower than expected"]
                        )
                    else:
                        result.set_pass(f"Fast: {exec_time:.2f}s", 
                                      {'execution_time': exec_time, 'command': name})
                else:
                    # Command failed - might not be in a git repo or timeout
                    if "timed out" in cmd_result.stderr.lower():
                        result.set_fail(f"Command timed out: {exec_time:.2f}s",
                                      {'execution_time': exec_time, 'command': name})
                    elif "not a git repository" in cmd_result.stderr.lower():
                        result.set_pass("Not in Git repository", 
                                      {'execution_time': exec_time, 'command': name})
                    else:
                        result.set_warning(f"Command failed: {cmd_result.stderr.strip()}")
                        
            except Exception as e:
                result.set_warning(f"Error testing command: {e}")
            
            result.execution_time = exec_time
            self.results.append(result)
        
        # Test shell startup time with protection
        result = DiagnosticResult("Shell Startup Time", category)
        try:
            if sys.platform == "win32":
                # Use optimized PowerShell command
                cmd = ["powershell", "-NoProfile", "-Command", "echo 'test'"]
            else:
                cmd = ["bash", "-c", "echo 'test'"]
            
            cmd_result, exec_time = self._run_command_with_timing(cmd, timeout=5)
            
            if exec_time > 5:
                result.set_fail(
                    f"Shell startup timed out: >{exec_time:.2f}s",
                    {'execution_time': exec_time, 'shell': cmd[0]},
                    ["Shell startup is extremely slow or hanging",
                     "Check for problematic shell initialization"]
                )
            elif exec_time > 3:
                result.set_warning(
                    f"Slow shell startup: {exec_time:.2f}s",
                    {'execution_time': exec_time, 'shell': cmd[0]},
                    ["Check shell profile scripts",
                     "Remove heavy initialization code",
                     "Use lazy loading for modules"]
                )
            elif exec_time > 1:
                result.set_warning(
                    f"Moderate shell startup: {exec_time:.2f}s",
                    {'execution_time': exec_time, 'shell': cmd[0]},
                    ["Consider optimizing shell startup"]
                )
            else:
                result.set_pass(f"Fast shell startup: {exec_time:.2f}s",
                              {'execution_time': exec_time, 'shell': cmd[0]})
                
        except Exception as e:
            result.set_warning(f"Error testing shell startup: {e}")
        
        self.results.append(result)
    
    def _diagnose_system_resources(self):
        """Diagnose system resource constraints with timeout protection."""
        category = "System Resources"
        
        # Test 1: Available memory
        result = DiagnosticResult("Memory Usage", category)
        try:
            if sys.platform == "win32":
                cmd_result, _ = self._run_command_with_timing([
                    "powershell", "-NoProfile", "-Command",
                    "Get-WmiObject -Class Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory"
                ], timeout=5)
                if cmd_result.returncode == 0:
                    output = cmd_result.stdout.strip()
                    result.set_pass(f"Memory info retrieved", {'output': output})
                else:
                    result.set_warning("Could not retrieve memory information")
            else:
                cmd_result, _ = self._run_command_with_timing(["free", "-h"], timeout=3)
                if cmd_result.returncode == 0:
                    result.set_pass("Memory info retrieved", {'output': cmd_result.stdout})
                else:
                    result.set_warning("Could not retrieve memory information")
                    
        except Exception as e:
            result.set_warning(f"Error checking memory: {e}")
        
        self.results.append(result)
        
        # Test 2: Disk space
        result = DiagnosticResult("Disk Space", category)
        try:
            current_dir = Path.cwd()
            if sys.platform == "win32":
                cmd_result, _ = self._run_command_with_timing([
                    "powershell", "-NoProfile", "-Command",
                    f"Get-WmiObject -Class Win32_LogicalDisk -Filter \"DeviceID='{current_dir.anchor}'\" | Select-Object Size, FreeSpace"
                ], timeout=5)
            else:
                cmd_result, _ = self._run_command_with_timing(["df", "-h", str(current_dir)], timeout=3)
            
            if cmd_result.returncode == 0:
                result.set_pass("Disk space info retrieved", {'output': cmd_result.stdout})
            else:
                result.set_warning("Could not retrieve disk space information")
                
        except Exception as e:
            result.set_warning(f"Error checking disk space: {e}")
        
        self.results.append(result)
    
    def _print_diagnostic_results(self):
        """Print formatted diagnostic results."""
        print("\n📊 Diagnostic Results:")
        print("="*60)
        
        # Group results by category
        by_category = defaultdict(list)
        for result in self.results:
            by_category[result.category].append(result)
        
        # Status icons
        status_icons = {
            'pass': '✅',
            'warning': '⚠️',
            'fail': '❌',
            'pending': '⏳'
        }
        
        for category, results in by_category.items():
            print(f"\n📁 {category}")
            print("-" * 40)
            
            for result in results:
                icon = status_icons.get(result.status, '?')
                exec_time = f" ({result.execution_time:.2f}s)" if result.execution_time else ""
                print(f"  {icon} {result.name}: {result.message}{exec_time}")
                
                if result.recommendations and self.verbose:
                    for rec in result.recommendations:
                        print(f"    💡 {rec}")
    
    def _generate_recommendations(self):
        """Generate overall recommendations based on diagnostic results."""
        print("\n💡 Recommendations:")
        print("="*60)
        
        # Collect all recommendations
        all_recommendations = []
        warning_count = 0
        fail_count = 0
        
        for result in self.results:
            if result.status == 'warning':
                warning_count += 1
            elif result.status == 'fail':
                fail_count += 1
            
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates while preserving order
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in unique_recommendations:
                unique_recommendations.append(rec)
        
        if fail_count > 0:
            print(f"🚨 Critical Issues Found: {fail_count}")
            print("   These issues require immediate attention!")
        
        if warning_count > 0:
            print(f"⚠️  Warnings Found: {warning_count}")
            print("   These issues may impact performance.")
        
        if unique_recommendations:
            print("\n🔧 Recommended Actions:")
            for i, rec in enumerate(unique_recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("\n🎉 No issues found! Your shell environment looks good.")
        
        # Save detailed report
        self._save_diagnostic_report()
    
    def _save_diagnostic_report(self):
        """Save detailed diagnostic report to file."""
        try:
            report_file = Path.home() / f".shell_diagnostic_report_{int(time.time())}.json"
            
            report_data = {
                'timestamp': time.time(),
                'system_info': self.system_info,
                'results': [result.to_dict() for result in self.results],
                'summary': {
                    'total_tests': len(self.results),
                    'passed': len([r for r in self.results if r.status == 'pass']),
                    'warnings': len([r for r in self.results if r.status == 'warning']),
                    'failures': len([r for r in self.results if r.status == 'fail'])
                }
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print(f"\n📄 Detailed report saved: {report_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save diagnostic report: {e}") 