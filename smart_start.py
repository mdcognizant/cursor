#!/usr/bin/env python3
"""
Smart Startup Script for Development Automation Suite
Automatically detects and uses Python installations even in corporate environments.
Enhanced with robust error handling and cross-platform compatibility.
"""

import os
import sys
import subprocess
import json
import platform
import tempfile
from pathlib import Path
from datetime import datetime

def safe_subprocess_run(cmd, timeout=10, **kwargs):
    """Safely run subprocess with proper error handling and encoding."""
    try:
        # Handle encoding issues in corporate environments
        encoding = kwargs.pop('encoding', None)
        if encoding is None:
            encoding = 'utf-8' if os.name != 'nt' else 'cp1252'
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            encoding=encoding,
            errors='replace',  # Replace problematic characters
            **kwargs
        )
        return result
    except subprocess.TimeoutExpired:
        return None
    except (OSError, UnicodeDecodeError, FileNotFoundError):
        return None

def get_python_candidates():
    """Get comprehensive list of Python candidates based on platform."""
    candidates = []
    
    if os.name == 'nt':  # Windows
        # Try py launcher with specific versions first (most reliable)
        py_versions = ['', ' -3.11', ' -3.10', ' -3.9', ' -3.8']
        for version in py_versions:
            candidates.append(f'py{version}')
        
        # Common Windows paths with dynamic version detection
        version_patterns = ['39', '38', '310', '311', '312']
        base_paths = [
            r'C:\Python{}\python.exe',
            r'C:\Program Files\Python{}\python.exe',
            r'C:\Program Files (x86)\Python{}\python.exe',
            os.path.expanduser(r'~\AppData\Local\Programs\Python\Python{}\python.exe'),
        ]
        
        for pattern in base_paths:
            for version in version_patterns:
                candidates.append(pattern.format(version))
        
        # Additional Windows-specific paths
        candidates.extend([
            os.path.expanduser(r'~\AppData\Local\Microsoft\WindowsApps\python.exe'),
            r'C:\Tools\Python\python.exe',
            r'C:\Dev\Python\python.exe',
            r'D:\Python\python.exe',
        ])
        
        # Conda installations
        conda_bases = [
            os.path.expanduser(r'~\Anaconda3\python.exe'),
            os.path.expanduser(r'~\Miniconda3\python.exe'),
            r'C:\Anaconda3\python.exe',
            r'C:\Miniconda3\python.exe',
            r'C:\ProgramData\Anaconda3\python.exe',
            r'C:\ProgramData\Miniconda3\python.exe',
        ]
        candidates.extend(conda_bases)
        
        # Standard commands
        candidates.extend(['python', 'python3'])
        
    else:  # Unix-like systems
        # Standard commands with version variations
        python_commands = [
            'python3', 'python', 'python3.11', 'python3.10', 
            'python3.9', 'python3.8', 'python3.12'
        ]
        candidates.extend(python_commands)
        
        # Common Unix paths
        common_paths = [
            '/usr/bin/python3', '/usr/bin/python',
            '/usr/local/bin/python3', '/usr/local/bin/python',
            '/opt/python3/bin/python3', '/opt/python/bin/python',
            os.path.expanduser('~/.local/bin/python3'),
            os.path.expanduser('~/.local/bin/python'),
        ]
        candidates.extend(common_paths)
        
        # Homebrew paths (macOS)
        if platform.system() == 'Darwin':
            homebrew_paths = [
                '/usr/local/opt/python@3.11/bin/python3',
                '/usr/local/opt/python@3.10/bin/python3',
                '/usr/local/opt/python@3.9/bin/python3',
                '/opt/homebrew/bin/python3',  # Apple Silicon
                '/usr/local/Cellar/python*/bin/python3',
            ]
            candidates.extend(homebrew_paths)
        
        # Conda installations
        conda_paths = [
            os.path.expanduser('~/anaconda3/bin/python'),
            os.path.expanduser('~/miniconda3/bin/python'),
            os.path.expanduser('~/miniforge3/bin/python'),
            '/opt/anaconda3/bin/python',
            '/opt/miniconda3/bin/python',
        ]
        candidates.extend(conda_paths)
    
    return candidates

def find_python_executable():
    """Smart Python detection for corporate environments with enhanced reliability."""
    candidates = []
    
    # Method 1: Check saved configuration first
    config_python = load_saved_config()
    if config_python:
        candidates.append(config_python)
    
    # Method 2: Get platform-specific candidates
    candidates.extend(get_python_candidates())
    
    # Method 3: Use which/where command for dynamic discovery
    if os.name == 'nt':
        # Windows: Use where command
        for cmd in ['python', 'python3', 'py']:
            try:
                result = safe_subprocess_run(['where', cmd])
                if result and result.returncode == 0:
                    paths = result.stdout.strip().split('\n')
                    candidates.extend(paths)
            except:
                pass
    else:
        # Unix: Use which command
        for cmd in ['python3', 'python']:
            try:
                result = safe_subprocess_run(['which', cmd])
                if result and result.returncode == 0 and result.stdout.strip():
                    candidates.append(result.stdout.strip())
            except:
                pass
    
    # Method 4: Check virtual environments
    venv_candidates = find_virtual_environment_pythons()
    candidates.extend(venv_candidates)
    
    # Test candidates and return the best one
    best_python = None
    best_score = 0
    
    for candidate in candidates:
        if candidate and test_python_installation(candidate):
            score = score_python_installation(candidate)
            if score > best_score:
                best_score = score
                best_python = candidate
                # If we find a very good Python, use it immediately
                if score >= 100:
                    break
    
    return best_python

def load_saved_config():
    """Load previously saved Python configuration."""
    config_files = ['python_config.json', '.python_config.json']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    python_path = config.get('python_path')
                    if python_path:
                        # Verify the saved path still works
                        if test_python_installation(python_path):
                            return python_path
                        else:
                            print(f"⚠️  Saved Python path no longer valid: {python_path}")
            except Exception:
                pass
    
    return None

def find_virtual_environment_pythons():
    """Find Python in common virtual environment locations."""
    candidates = []
    
    # Current directory virtual environments
    local_venvs = [
        './venv/bin/python', './venv/Scripts/python.exe',
        './.venv/bin/python', './.venv/Scripts/python.exe',
        './env/bin/python', './env/Scripts/python.exe',
    ]
    candidates.extend(local_venvs)
    
    # User virtual environments
    user_venv_patterns = [
        os.path.expanduser('~/.virtualenvs/*/bin/python'),
        os.path.expanduser('~/.virtualenvs/*/Scripts/python.exe'),
        os.path.expanduser('~/venvs/*/bin/python'),
        os.path.expanduser('~/venvs/*/Scripts/python.exe'),
        os.path.expanduser('~/.pyenv/versions/*/bin/python'),
    ]
    
    import glob
    for pattern in user_venv_patterns:
        try:
            candidates.extend(glob.glob(pattern))
        except:
            pass
    
    return candidates

def test_python_installation(python_cmd):
    """Test if a Python installation is suitable for our needs with comprehensive validation."""
    try:
        # Handle py launcher special case
        if python_cmd.startswith('py'):
            cmd_parts = python_cmd.split()
        else:
            cmd_parts = [python_cmd]
        
        # Test 1: Basic version check
        version_result = safe_subprocess_run(cmd_parts + ['--version'], timeout=10)
        if not version_result or version_result.returncode != 0:
            return False
        
        version_line = version_result.stdout.strip()
        if not any(keyword in version_line.lower() for keyword in ['python', 'pypy']):
            return False
        
        # Test 2: Check minimum version (3.8+)
        try:
            if 'Python 3.' in version_line:
                version_parts = version_line.split()[1].split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1])
                if major < 3 or (major == 3 and minor < 8):
                    return False
        except:
            pass  # If version parsing fails, continue with other tests
        
        # Test 3: Basic Python functionality
        basic_test = safe_subprocess_run(
            cmd_parts + ['-c', 'import sys; print("Python OK")'], 
            timeout=10
        )
        if not basic_test or basic_test.returncode != 0:
            return False
        
        # Test 4: tkinter test (required for GUI)
        tkinter_test = safe_subprocess_run(
            cmd_parts + ['-c', 'import tkinter; print("GUI OK")'], 
            timeout=15
        )
        if not tkinter_test or tkinter_test.returncode != 0:
            return False
        
        # Test 5: Test sys.executable accessibility
        exe_test = safe_subprocess_run(
            cmd_parts + ['-c', 'import sys; print(sys.executable)'], 
            timeout=10
        )
        if not exe_test or exe_test.returncode != 0:
            return False
        
        return True
        
    except Exception:
        return False

def score_python_installation(python_cmd):
    """Score a Python installation for preference ranking."""
    score = 0
    
    try:
        # Get version info
        if python_cmd.startswith('py'):
            cmd_parts = python_cmd.split()
        else:
            cmd_parts = [python_cmd]
        
        version_result = safe_subprocess_run(cmd_parts + ['--version'], timeout=5)
        if version_result and version_result.returncode == 0:
            version_line = version_result.stdout.strip()
            
            # Version scoring
            try:
                if 'Python 3.' in version_line:
                    version_num = version_line.split()[1]
                    major, minor = map(int, version_num.split('.')[:2])
                    if major == 3:
                        score += minor * 10  # 10 points per minor version
                        if minor >= 10:  # Bonus for newer versions
                            score += 20
            except:
                pass
        
        # Installation type scoring
        cmd_lower = python_cmd.lower()
        
        if python_cmd.startswith('py '):  # py launcher with version
            score += 50
        elif python_cmd == 'py':  # py launcher default
            score += 40
        elif 'program files' in cmd_lower:  # System installation
            score += 30
        elif 'anaconda' in cmd_lower or 'miniconda' in cmd_lower:  # Conda
            score += 25
        elif 'appdata' in cmd_lower and 'local' in cmd_lower:  # User installation
            score += 20
        elif cmd_lower in ['python3', 'python']:  # System commands
            score += 15
        
        # Virtual environment bonus
        if any(venv in cmd_lower for venv in ['venv', '.venv', 'env', 'virtualenv']):
            score += 5
        
    except Exception:
        pass
    
    return score

def create_error_report(error_details=None):
    """Create a detailed error report for troubleshooting."""
    try:
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "user": os.getenv('USERNAME', os.getenv('USER', 'Unknown')),
            "working_directory": os.getcwd(),
            "python_version": sys.version if 'sys' in globals() else 'Unknown',
            "error_details": error_details,
            "paths_checked": [],
            "commands_tried": []
        }
        
        # Add platform-specific information
        if os.name == 'nt':
            report_data["paths_checked"] = [
                'py',
                'python',
                'python3',
                r'C:\Python*\python.exe',
                r'C:\Program Files\Python*\python.exe',
                os.path.expanduser(r'~\AppData\Local\Programs\Python\Python*\python.exe'),
                os.path.expanduser(r'~\AppData\Local\Microsoft\WindowsApps\python.exe'),
            ]
            report_data["commands_tried"] = ['py --version', 'python --version', 'where python']
        else:
            report_data["paths_checked"] = [
                'python3',
                'python',
                '/usr/bin/python*',
                '/usr/local/bin/python*',
                os.path.expanduser('~/.local/bin/python*'),
            ]
            report_data["commands_tried"] = ['python3 --version', 'python --version', 'which python3']
        
        # Save detailed report
        with open('python_detection_error.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Also create a simple text report
        text_report = f"""
PYTHON DETECTION ERROR REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Platform: {platform.platform()}
Working Directory: {os.getcwd()}

PROBLEM: No suitable Python installation found

REQUIREMENTS:
- Python 3.8 or higher
- tkinter package (for GUI support)
- Accessible without admin rights

CORPORATE ENVIRONMENT SOLUTIONS:

1. PORTABLE PYTHON (Recommended):
   - Download from: https://www.python.org/downloads/
   - Choose "embeddable zip file" (Windows) or standard installer
   - Extract/install to user directory
   - No admin rights required

2. MICROSOFT STORE PYTHON (Windows):
   - Often available in corporate environments
   - Search "Python" in Microsoft Store
   - Usually includes tkinter

3. PYTHON LAUNCHER:
   - Try: py --version
   - Often works when python command doesn't

4. CONTACT IT SUPPORT:
   - Request Python 3.8+ installation
   - Ask for tkinter package inclusion
   - Mention development productivity needs

5. CLOUD ALTERNATIVES:
   - GitHub Codespaces
   - Google Colab
   - Replit
   - GitPod

Next Steps:
1. Try portable Python installation
2. Contact IT with this report
3. Re-run: python detect_python.py
4. Or use: start_corporate.bat (Windows)
"""
        
        with open('python_help.txt', 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        return True
        
    except Exception:
        return False

def save_working_python(python_cmd):
    """Save working Python configuration for future use."""
    try:
        # Get additional information about this Python
        version_info = "Unknown"
        executable_path = "Unknown"
        
        if python_cmd.startswith('py'):
            cmd_parts = python_cmd.split()
        else:
            cmd_parts = [python_cmd]
        
        # Get version
        version_result = safe_subprocess_run(cmd_parts + ['--version'], timeout=5)
        if version_result and version_result.returncode == 0:
            version_info = version_result.stdout.strip()
        
        # Get executable path
        exe_result = safe_subprocess_run(cmd_parts + ['-c', 'import sys; print(sys.executable)'], timeout=5)
        if exe_result and exe_result.returncode == 0:
            executable_path = exe_result.stdout.strip()
        
        config = {
            'python_path': python_cmd,
            'executable_path': executable_path,
            'version': version_info,
            'platform': platform.platform(),
            'detected_at': datetime.now().isoformat(),
            'last_verified': datetime.now().isoformat(),
            'detection_method': 'smart_start.py'
        }
        
        with open('python_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception:
        return False

def check_application_requirements():
    """Check if all application requirements are met."""
    issues = []
    
    # Check for main.py
    if not os.path.exists('main.py'):
        issues.append("main.py not found in current directory")
    
    # Check for run.py (alternative entry point)
    if not os.path.exists('run.py') and not os.path.exists('main.py'):
        issues.append("Neither main.py nor run.py found")
    
    # Check for requirements.txt
    if not os.path.exists('requirements.txt'):
        issues.append("requirements.txt not found (may need to install dependencies)")
    
    # Check for core directories
    core_dirs = ['src', 'src/core', 'src/gui']
    for dir_name in core_dirs:
        if not os.path.exists(dir_name):
            issues.append(f"Missing directory: {dir_name}")
    
    return issues

def install_requirements(python_cmd):
    """Attempt to install requirements if requirements.txt exists."""
    if not os.path.exists('requirements.txt'):
        return True, "No requirements.txt found"
    
    try:
        print("📦 Installing/updating dependencies...")
        
        if python_cmd.startswith('py'):
            cmd_parts = python_cmd.split()
        else:
            cmd_parts = [python_cmd]
        
        # Use pip to install requirements
        result = safe_subprocess_run(
            cmd_parts + ['-m', 'pip', 'install', '-r', 'requirements.txt', '--user'], 
            timeout=120  # Longer timeout for pip operations
        )
        
        if result and result.returncode == 0:
            return True, "Dependencies installed successfully"
        else:
            error_msg = result.stderr if result else "Unknown error"
            return False, f"Failed to install dependencies: {error_msg}"
            
    except Exception as e:
        return False, f"Error installing requirements: {e}"

def main():
    """Main smart startup function with comprehensive error handling."""
    print("🚀 Smart Startup - Development Automation Suite")
    print("=" * 65)
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"📁 Directory: {os.getcwd()}")
    print(f"👤 User: {os.getenv('USERNAME', os.getenv('USER', 'Unknown'))}")
    print()
    
    try:
        # Step 1: Find Python
        print("🔍 Detecting Python installation...")
        python_cmd = find_python_executable()
        
        if not python_cmd:
            print("❌ No suitable Python installation found!")
            print()
            print("🔧 IMMEDIATE SOLUTIONS:")
            print("1. Run: detect_python.py (comprehensive scan)")
            print("2. Try: py --version (Windows py launcher)")
            print("3. Download portable Python from python.org")
            print("4. Install Python from Microsoft Store (Windows)")
            print("5. Contact IT for Python installation help")
            print()
            
            # Create comprehensive error report
            if create_error_report():
                print("📄 Created error reports:")
                print("   • python_detection_error.json (technical details)")
                print("   • python_help.txt (user-friendly guide)")
            
            input("\nPress Enter to exit...")
            return 1
        
        print(f"✅ Found Python: {python_cmd}")
        
        # Step 2: Validate Python installation
        print("🧪 Validating Python installation...")
        if not test_python_installation(python_cmd):
            print("❌ Python installation validation failed!")
            print("   Required: Python 3.8+ with tkinter support")
            print()
            print("🔧 Try running: detect_python.py for alternative installations")
            input("Press Enter to exit...")
            return 1
        
        print("✅ Python installation validated!")
        
        # Step 3: Check application requirements
        print("📋 Checking application requirements...")
        issues = check_application_requirements()
        
        if issues:
            print("⚠️  Application issues found:")
            for issue in issues:
                print(f"   • {issue}")
            
            if not any('main.py' in issue or 'run.py' in issue for issue in issues):
                print("   → Continuing anyway (non-critical issues)")
            else:
                print("\n❌ Critical files missing. Make sure you're in the correct directory.")
                input("Press Enter to exit...")
                return 1
        else:
            print("✅ All requirements satisfied!")
        
        # Step 4: Install/update dependencies if needed
        if os.path.exists('requirements.txt'):
            success, message = install_requirements(python_cmd)
            if success:
                print(f"✅ {message}")
            else:
                print(f"⚠️  {message}")
                print("   → Continuing anyway (may cause runtime errors)")
        
        # Step 5: Save working configuration
        print("💾 Saving Python configuration...")
        if save_working_python(python_cmd):
            print("✅ Configuration saved for future launches")
        else:
            print("⚠️  Could not save configuration")
        
        print()
        print("🎯 Starting Development Automation Suite...")
        print("-" * 50)
        
        # Step 6: Launch the application
        try:
            entry_points = ['main.py', 'run.py']
            entry_point = None
            
            for ep in entry_points:
                if os.path.exists(ep):
                    entry_point = ep
                    break
            
            if not entry_point:
                print("❌ No entry point found (main.py or run.py)")
                return 1
            
            print(f"🚀 Launching {entry_point}...")
            
            if python_cmd.startswith('py'):
                # Handle py launcher
                if ' ' in python_cmd:
                    # py with version
                    parts = python_cmd.split()
                    os.system(f'{parts[0]} {parts[1]} {entry_point}')
                else:
                    os.system(f'py {entry_point}')
            else:
                # Regular python command
                os.system(f'"{python_cmd}" {entry_point}')
                
        except KeyboardInterrupt:
            print("\n\n👋 Application interrupted by user")
            return 0
        except Exception as e:
            print(f"\n❌ Error launching application: {e}")
            create_error_report(str(e))
            return 1
    
    except KeyboardInterrupt:
        print("\n\n👋 Startup interrupted by user")
        return 0
    except Exception as e:
        print(f"\n💥 Unexpected error during startup: {e}")
        create_error_report(str(e))
        print("\n📄 Error report created for troubleshooting")
        input("Press Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        try:
            create_error_report(str(e))
            print("📄 Error report created")
        except:
            pass
        input("Press Enter to exit...")
        sys.exit(1) 