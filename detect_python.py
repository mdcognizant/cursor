#!/usr/bin/env python3
"""
Python Detection and Configuration Script
Helps find and configure Python on corporate machines with restricted PATH access.
Supports Windows, macOS, and Linux with extensive compatibility features.
"""

import os
import sys
import subprocess
import json
import platform
import tempfile
from pathlib import Path
from datetime import datetime

# Windows-specific imports (only import if on Windows)
try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

def get_python_versions():
    """Get a dynamic list of Python versions to search for."""
    # Start with common recent versions
    versions = []
    
    # Generate version numbers dynamically (3.8 to 3.15)
    for major in [3]:
        for minor in range(8, 16):  # Python 3.8 to 3.15
            versions.extend([
                f"python{major}.{minor}",
                f"python{major}{minor}",
                f"Python{major}.{minor}",
                f"Python{major}{minor}",
            ])
    
    # Add generic versions
    versions.extend([
        "python3", "python", "py", "python.exe", "python3.exe"
    ])
    
    return versions

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

def find_python_installations():
    """Find all Python installations on the system."""
    python_installations = []
    
    print(f"🔍 Scanning {platform.system()} {platform.release()} for Python installations...")
    
    if os.name == 'nt':  # Windows
        python_installations.extend(find_python_windows())
    else:  # Unix-like systems (Linux, macOS, etc.)
        python_installations.extend(find_python_unix())
    
    # Also check for virtual environments and conda
    python_installations.extend(find_python_virtual_envs())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_installations = []
    for install in python_installations:
        if install not in seen:
            seen.add(install)
            unique_installations.append(install)
    
    return unique_installations

def find_python_windows():
    """Find Python installations on Windows systems."""
    installations = []
    
    # Method 1: Try py launcher first (most reliable)
    try:
        result = safe_subprocess_run(['py', '--version'])
        if result and result.returncode == 0:
            installations.append('py')
            
            # Also try to get specific versions from py launcher
            for version in ['3.11', '3.10', '3.9', '3.8']:
                result = safe_subprocess_run(['py', f'-{version}', '--version'])
                if result and result.returncode == 0:
                    installations.append(f'py -{version}')
    except Exception:
        pass
    
    # Method 2: Windows Registry (if available)
    if HAS_WINREG:
        try:
            installations.extend(find_python_registry())
        except Exception as e:
            print(f"Registry search failed: {e}")
    
    # Method 3: Common installation paths with dynamic version detection
    base_paths = [
        r"C:\Python*",
        r"C:\Program Files\Python*",
        r"C:\Program Files (x86)\Python*",
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python*"),
        os.path.expanduser(r"~\AppData\Local\Microsoft\WindowsApps\python*.exe"),
        r"C:\Users\*\AppData\Local\Programs\Python\Python*",
        # Additional corporate-specific paths
        r"C:\Tools\Python*",
        r"C:\Dev\Python*",
        r"D:\Python*",  # Some companies use D: drive
        os.path.expanduser(r"~\Documents\Python*"),
        os.path.expanduser(r"~\Desktop\Python*"),
    ]
    
    # Check common paths
    for path_pattern in base_paths:
        try:
            import glob
            for path in glob.glob(path_pattern):
                python_exe = find_python_executable(path)
                if python_exe:
                    installations.append(python_exe)
        except Exception:
            continue
    
    # Method 4: Check Windows Store Python
    try:
        store_python = os.path.expanduser(r"~\AppData\Local\Microsoft\WindowsApps\python.exe")
        if os.path.exists(store_python) and is_valid_python(store_python):
            installations.append(store_python)
    except Exception:
        pass
    
    # Method 5: Check if python/python3 commands work
    for cmd in ['python', 'python3']:
        try:
            result = safe_subprocess_run([cmd, '--version'])
            if result and result.returncode == 0:
                # Try to get the actual path
                where_result = safe_subprocess_run(['where', cmd])
                if where_result and where_result.returncode == 0:
                    python_path = where_result.stdout.strip().split('\n')[0]
                    installations.append(python_path)
                else:
                    installations.append(cmd)
        except Exception:
            pass
    
    # Method 6: Check conda environments
    installations.extend(find_conda_pythons_windows())
    
    return installations

def find_python_registry():
    """Find Python installations from Windows Registry with enhanced error handling."""
    if not HAS_WINREG:
        return []
    
    installations = []
    
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Python\PythonCore"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Python\PythonCore"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Python\PythonCore"),
        # Additional registry paths for different Python distributions
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Python\ContinuumAnalytics"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Python\ContinuumAnalytics"),
    ]
    
    for hkey, path in registry_paths:
        try:
            with winreg.OpenKey(hkey, path) as key:
                i = 0
                while True:
                    try:
                        version = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, f"{version}\\InstallPath") as install_key:
                                install_path = winreg.QueryValue(install_key, "")
                                if install_path:
                                    python_exe = os.path.join(install_path, "python.exe")
                                    if os.path.exists(python_exe):
                                        installations.append(python_exe)
                        except Exception:
                            pass
                        i += 1
                    except OSError:
                        break
        except Exception:
            continue
    
    return installations

def find_conda_pythons_windows():
    """Find conda Python installations on Windows."""
    installations = []
    
    # Common conda installation paths
    conda_paths = [
        os.path.expanduser(r"~\Anaconda3"),
        os.path.expanduser(r"~\Miniconda3"),
        os.path.expanduser(r"~\anaconda3"),
        os.path.expanduser(r"~\miniconda3"),
        r"C:\Anaconda3",
        r"C:\Miniconda3",
        r"C:\ProgramData\Anaconda3",
        r"C:\ProgramData\Miniconda3",
        os.path.expanduser(r"~\AppData\Local\Continuum\anaconda3"),
        os.path.expanduser(r"~\AppData\Local\Continuum\miniconda3"),
    ]
    
    for conda_path in conda_paths:
        python_exe = os.path.join(conda_path, "python.exe")
        if os.path.exists(python_exe) and is_valid_python(python_exe):
            installations.append(python_exe)
            
        # Check for conda environments
        envs_path = os.path.join(conda_path, "envs")
        if os.path.exists(envs_path):
            try:
                for env_name in os.listdir(envs_path):
                    env_python = os.path.join(envs_path, env_name, "python.exe")
                    if os.path.exists(env_python) and is_valid_python(env_python):
                        installations.append(env_python)
            except Exception:
                pass
    
    return installations

def find_python_unix():
    """Find Python installations on Unix-like systems (Linux, macOS)."""
    installations = []
    
    # Method 1: Check common commands with dynamic versions
    python_commands = get_python_versions()
    
    for cmd in python_commands:
        try:
            result = safe_subprocess_run(['which', cmd])
            if result and result.returncode == 0 and result.stdout.strip():
                python_path = result.stdout.strip()
                if is_valid_python(python_path):
                    installations.append(python_path)
        except Exception:
            continue
    
    # Method 2: Check common installation paths
    common_paths = [
        "/usr/bin",
        "/usr/local/bin",
        "/opt/python*/bin",
        "/usr/local/opt/python*/bin",  # Homebrew on macOS
        os.path.expanduser("~/.local/bin"),
        os.path.expanduser("~/bin"),
        "/snap/bin",  # Snap packages on Linux
        "/usr/local/Cellar/python*/bin",  # Homebrew cellar
        # Additional paths for different distributions
        "/opt/local/bin",  # MacPorts
        "/sw/bin",  # Fink
    ]
    
    # Method 3: Check conda/virtual environment paths
    common_paths.extend([
        os.path.expanduser("~/anaconda*/bin"),
        os.path.expanduser("~/miniconda*/bin"),
        os.path.expanduser("~/miniforge*/bin"),
        os.path.expanduser("~/mambaforge*/bin"),
        "/opt/anaconda*/bin",
        "/opt/miniconda*/bin",
        os.path.expanduser("~/.conda/envs/*/bin"),
        os.path.expanduser("~/envs/*/bin"),
        os.path.expanduser("~/.virtualenvs/*/bin"),
    ])
    
    # Check all paths
    import glob
    for path_pattern in common_paths:
        try:
            for path in glob.glob(path_pattern):
                if os.path.isdir(path):
                    for cmd in python_commands:
                        python_exe = os.path.join(path, cmd)
                        if os.path.exists(python_exe) and is_valid_python(python_exe):
                            installations.append(python_exe)
        except Exception:
            continue
    
    # Method 4: Check /Applications on macOS
    if platform.system() == 'Darwin':
        app_paths = [
            "/Applications/Python */Python.app/Contents/MacOS/Python",
            "/Applications/Xcode.app/Contents/Developer/usr/bin/python*",
        ]
        for app_pattern in app_paths:
            try:
                for path in glob.glob(app_pattern):
                    if is_valid_python(path):
                        installations.append(path)
            except Exception:
                continue
    
    return installations

def find_python_virtual_envs():
    """Find Python installations in virtual environments."""
    installations = []
    
    # Check common virtual environment locations
    venv_patterns = [
        os.path.expanduser("~/.virtualenvs/*/bin/python*"),
        os.path.expanduser("~/.virtualenvs/*/Scripts/python*"),  # Windows virtualenv
        os.path.expanduser("~/venvs/*/bin/python*"),
        os.path.expanduser("~/venvs/*/Scripts/python*"),
        os.path.expanduser("~/.pyenv/versions/*/bin/python*"),
        "./venv/bin/python*",
        "./venv/Scripts/python*",
        "./.venv/bin/python*",
        "./.venv/Scripts/python*",
    ]
    
    import glob
    for pattern in venv_patterns:
        try:
            for path in glob.glob(pattern):
                if is_valid_python(path):
                    installations.append(path)
        except Exception:
            continue
    
    return installations

def find_python_executable(install_path):
    """Find the Python executable in an installation directory."""
    if os.path.isfile(install_path):
        # If it's already a file, check if it's a valid Python executable
        if any(install_path.lower().endswith(ext) for ext in ['.exe', '']):
            return install_path if is_valid_python(install_path) else None
    
    if not os.path.isdir(install_path):
        return None
    
    # Try different possible executable names
    possible_exes = [
        "python.exe", "python3.exe", "python", "python3",
        "python.bat", "python3.bat"  # Sometimes there are batch wrappers
    ]
    
    for exe in possible_exes:
        python_path = os.path.join(install_path, exe)
        if os.path.exists(python_path) and is_valid_python(python_path):
            return python_path
    
    # Check bin subdirectory (common in Unix-like systems)
    bin_dir = os.path.join(install_path, "bin")
    if os.path.exists(bin_dir):
        for exe in possible_exes:
            python_path = os.path.join(bin_dir, exe)
            if os.path.exists(python_path) and is_valid_python(python_path):
                return python_path
    
    # Check Scripts subdirectory (common in Windows virtual environments)
    scripts_dir = os.path.join(install_path, "Scripts")
    if os.path.exists(scripts_dir):
        for exe in possible_exes:
            python_path = os.path.join(scripts_dir, exe)
            if os.path.exists(python_path) and is_valid_python(python_path):
                return python_path
    
    return None

def is_valid_python(python_path):
    """Check if a given path is a valid Python executable with enhanced validation."""
    try:
        # Quick file existence check
        if not os.path.exists(python_path):
            return False
        
        # Check if it's executable (Unix-like systems)
        if os.name != 'nt' and not os.access(python_path, os.X_OK):
            return False
        
        # Test basic Python functionality
        result = safe_subprocess_run([python_path, '--version'], timeout=10)
        if not result or result.returncode != 0:
            return False
        
        # Verify it's actually Python
        version_output = result.stdout.strip()
        if not any(keyword in version_output.lower() for keyword in ['python', 'pypy', 'jython', 'ironpython']):
            return False
        
        # Test basic import functionality
        test_result = safe_subprocess_run([python_path, '-c', 'import sys; print(sys.version_info.major)'], timeout=10)
        if not test_result or test_result.returncode != 0:
            return False
        
        return True
        
    except Exception:
        return False

def get_python_info(python_path):
    """Get detailed information about a Python installation with enhanced error handling."""
    try:
        # Get version
        version_result = safe_subprocess_run([python_path, '--version'], timeout=10)
        if version_result and version_result.returncode == 0:
            version = version_result.stdout.strip()
        else:
            version = "Unknown"
        
        # Get detailed info with better error handling
        info_script = '''
import sys
import platform
try:
    import site
    site_packages = site.getsitepackages()[0] if site.getsitepackages() else "Unknown"
except:
    site_packages = "Unknown"

print(f"Version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.architecture()[0]}")
print(f"Executable: {sys.executable}")
print(f"Site packages: {site_packages}")
print(f"Python path: {':'.join(sys.path[:3])}")
'''
        
        info_result = safe_subprocess_run([python_path, '-c', info_script], timeout=15)
        
        details = info_result.stdout if (info_result and info_result.returncode == 0) else "Could not get details"
        
        return {
            "path": python_path,
            "version": version,
            "details": details,
            "valid": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "path": python_path,
            "version": "Unknown",
            "details": f"Error: {e}",
            "valid": False,
            "timestamp": datetime.now().isoformat()
        }

def create_python_launcher(python_path, output_dir="."):
    """Create a launcher script for the found Python installation with cross-platform support."""
    output_dir = Path(output_dir)
    launchers_created = []
    
    if os.name == 'nt':  # Windows
        # Create main launcher
        launcher_content = f'''@echo off
REM Auto-generated Python launcher
REM Found Python at: {python_path}
REM Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

setlocal
set "PYTHONPATH=%PYTHONPATH%;{os.getcwd()}"
"{python_path}" %*
endlocal
'''
        launcher_file = output_dir / "python_launcher.bat"
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        launchers_created.append(str(launcher_file))
        
        # Create simple python.bat for direct access
        python_bat = output_dir / "python.bat"
        with open(python_bat, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        launchers_created.append(str(python_bat))
        
        # Create launcher for pip
        pip_content = f'''@echo off
REM Auto-generated pip launcher
"{python_path}" -m pip %*
'''
        pip_bat = output_dir / "pip.bat"
        with open(pip_bat, 'w', encoding='utf-8') as f:
            f.write(pip_content)
        launchers_created.append(str(pip_bat))
        
    else:  # Unix-like
        # Create main launcher
        launcher_content = f'''#!/bin/bash
# Auto-generated Python launcher
# Found Python at: {python_path}
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

export PYTHONPATH="$PYTHONPATH:{os.getcwd()}"
"{python_path}" "$@"
'''
        launcher_file = output_dir / "python_launcher.sh"
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        os.chmod(launcher_file, 0o755)
        launchers_created.append(str(launcher_file))
        
        # Create simple python script
        python_sh = output_dir / "python.sh"
        with open(python_sh, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        os.chmod(python_sh, 0o755)
        launchers_created.append(str(python_sh))
        
        # Create launcher for pip
        pip_content = f'''#!/bin/bash
# Auto-generated pip launcher
"{python_path}" -m pip "$@"
'''
        pip_sh = output_dir / "pip.sh"
        with open(pip_sh, 'w', encoding='utf-8') as f:
            f.write(pip_content)
        os.chmod(pip_sh, 0o755)
        launchers_created.append(str(pip_sh))
    
    return launchers_created

def setup_local_environment(python_path):
    """Setup a local environment configuration with enhanced metadata."""
    config = {
        "python_path": python_path,
        "created_by": "Development Automation Suite",
        "created_at": datetime.now().isoformat(),
        "platform": platform.platform(),
        "python_version": None,
        "instructions": "Use the generated launcher scripts to run Python",
        "last_verified": datetime.now().isoformat()
    }
    
    # Get Python version info
    try:
        result = safe_subprocess_run([python_path, '--version'])
        if result and result.returncode == 0:
            config["python_version"] = result.stdout.strip()
    except Exception:
        pass
    
    try:
        with open("python_config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save configuration: {e}")
    
    return config

def check_tkinter_support(python_path):
    """Check if tkinter is available in the Python installation with enhanced testing."""
    try:
        # Test basic tkinter import
        result = safe_subprocess_run([python_path, '-c', 'import tkinter; print("tkinter available")'], timeout=15)
        if not result or result.returncode != 0:
            return False
        
        # Test tkinter functionality (create a window and destroy it immediately)
        tk_test = '''
import tkinter as tk
try:
    root = tk.Tk()
    root.withdraw()  # Hide the window
    root.destroy()
    print("tkinter functional")
except Exception as e:
    print(f"tkinter error: {e}")
    exit(1)
'''
        
        result2 = safe_subprocess_run([python_path, '-c', tk_test], timeout=15)
        return result2 and result2.returncode == 0
        
    except Exception:
        return False

def suggest_solutions():
    """Provide comprehensive solutions for different corporate environment scenarios."""
    solutions = f"""
🔧 COMPREHENSIVE SOLUTIONS FOR CORPORATE ENVIRONMENTS:

📊 SYSTEM DETECTED: {platform.system()} {platform.release()}

1. 📁 PORTABLE PYTHON INSTALLATION (No Admin Required):
   - Download from: https://www.python.org/downloads/
   - Choose "Windows embeddable zip file" (Windows) or "macOS installer"
   - Extract/Install to user directory (Documents, Desktop, etc.)
   - Fully functional Python with no admin rights needed!

2. 🏢 CORPORATE IT SOLUTIONS:
   - Check company software catalog/portal
   - Request Python through IT ticketing system
   - Ask for Python to be added to system PATH
   - Mention productivity and development automation needs

3. 🐍 PYTHON LAUNCHER ALTERNATIVES:
   - Windows: Try 'py' command (Python Launcher for Windows)
   - macOS: Try 'python3' from Xcode command line tools
   - Linux: Try package managers (apt, yum, dnf, snap)

4. 📦 ALTERNATIVE PYTHON DISTRIBUTIONS:
   - Microsoft Store Python (Windows 10/11 - often pre-approved)
   - Anaconda Individual Edition (includes many packages)
   - Miniconda (lighter version of Anaconda)
   - WinPython (portable Windows distribution)
   - Homebrew Python (macOS)

5. ⚡ VIRTUAL ENVIRONMENTS:
   - Create in user space: python -m venv ~/my_venv
   - No admin rights needed for packages
   - Isolated environment for development

6. 🔄 USE OUR GENERATED LAUNCHERS:
   - Bypass PATH restrictions completely
   - Direct executable references
   - Cross-platform compatibility

7. 🛠️ DEVELOPMENT ENVIRONMENTS:
   - VS Code with Python extension
   - PyCharm Community Edition
   - Jupyter Notebook/Lab
   - Google Colab (cloud-based)

8. 📱 MOBILE/CLOUD ALTERNATIVES:
   - GitHub Codespaces
   - Replit
   - Google Colab
   - GitPod
"""
    return solutions

def main():
    """Main function with enhanced user experience and comprehensive reporting."""
    print("🔍 ADVANCED PYTHON DETECTION AND CONFIGURATION TOOL")
    print("=" * 60)
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"👤 User: {os.getenv('USERNAME', os.getenv('USER', 'Unknown'))}")
    print()
    
    try:
        print("🔍 Comprehensive Python installation scan...")
        installations = find_python_installations()
        
        if not installations:
            print("❌ No Python installations found!")
            print()
            print(suggest_solutions())
            
            # Create detailed diagnostic report
            create_diagnostic_report()
            return
        
        print(f"✅ Found {len(installations)} Python installation(s):")
        print()
        
        best_python = None
        best_score = 0
        all_info = []
        
        for i, python_path in enumerate(installations, 1):
            print(f"📍 Installation {i}:")
            info = get_python_info(python_path)
            all_info.append(info)
            
            print(f"   Path: {info['path']}")
            print(f"   Version: {info['version']}")
            
            if info['valid']:
                # Check tkinter support
                has_tkinter = check_tkinter_support(python_path)
                tkinter_status = "✅ Yes" if has_tkinter else "❌ No (required for GUI)"
                print(f"   GUI Support: {tkinter_status}")
                
                # Enhanced scoring system
                score = calculate_python_score(info['version'], has_tkinter, python_path)
                
                if score > best_score:
                    best_score = score
                    best_python = python_path
                
                print(f"   Status: ✅ Valid (Score: {score})")
            else:
                print(f"   Status: ❌ Invalid - {info['details']}")
            
            print()
        
        # Create comprehensive report
        create_installation_report(all_info)
        
        if best_python:
            setup_best_python(best_python, best_score)
        else:
            print("❌ No suitable Python installation found for GUI applications.")
            print("   Required: Python 3.8+ with tkinter support")
            print()
            print(suggest_solutions())
            
    except KeyboardInterrupt:
        print("\n\n👋 Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during scan: {e}")
        print("Creating error report...")
        create_error_report(str(e))

def calculate_python_score(version_str, has_tkinter, python_path):
    """Calculate a score for Python installation preference."""
    score = 0
    
    # Version scoring (prefer newer versions)
    try:
        if "Python 3." in version_str:
            version_parts = version_str.split()
            if len(version_parts) >= 2:
                version_num = version_parts[1]
                major, minor = map(int, version_num.split('.')[:2])
                if major == 3:
                    score += minor * 5  # 5 points per minor version
                    if minor >= 10:  # Bonus for Python 3.10+
                        score += 10
    except:
        pass
    
    # GUI support (critical)
    if has_tkinter:
        score += 100
    
    # Path preferences (prefer certain installation types)
    path_lower = python_path.lower()
    if 'py -' in python_path:  # py launcher with version
        score += 20
    elif python_path == 'py':  # py launcher
        score += 15
    elif 'program files' in path_lower:  # System installation
        score += 10
    elif 'anaconda' in path_lower or 'miniconda' in path_lower:  # Conda
        score += 8
    elif 'appdata' in path_lower and 'local' in path_lower:  # User installation
        score += 5
    
    return score

def setup_best_python(best_python, score):
    """Setup the best Python installation found."""
    print(f"🎯 RECOMMENDED PYTHON: {best_python}")
    print(f"   Quality Score: {score}/100+")
    print()
    
    print("🚀 Creating launcher scripts...")
    try:
        launchers = create_python_launcher(best_python)
        config = setup_local_environment(best_python)
        
        print("✅ Created launcher scripts:")
        for launcher in launchers:
            print(f"   • {launcher}")
        print("✅ Created configuration: python_config.json")
        print()
        
        print("🎉 SETUP COMPLETE!")
        print("=" * 40)
        print("🚀 You can now use Python through:")
        for launcher in launchers:
            print(f"   • {os.path.basename(launcher)}")
        print()
        print("🎯 To start the Development Automation Suite:")
        if os.name == 'nt':
            print("   python_launcher.bat run.py")
            print("   python_launcher.bat main.py")
        else:
            print("   ./python_launcher.sh run.py")
            print("   ./python_launcher.sh main.py")
        print()
        print("📦 To install packages:")
        if os.name == 'nt':
            print("   pip.bat install package_name")
        else:
            print("   ./pip.sh install package_name")
            
    except Exception as e:
        print(f"❌ Error creating launcher: {e}")
        create_error_report(str(e))

def create_installation_report(all_info):
    """Create a detailed installation report."""
    try:
        report = {
            "scan_info": {
                "timestamp": datetime.now().isoformat(),
                "platform": platform.platform(),
                "user": os.getenv('USERNAME', os.getenv('USER', 'Unknown')),
                "working_directory": os.getcwd()
            },
            "installations_found": len(all_info),
            "installations": all_info
        }
        
        with open("python_installations_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("📊 Created detailed report: python_installations_report.json")
    except Exception as e:
        print(f"Warning: Could not create installation report: {e}")

def create_diagnostic_report():
    """Create a diagnostic report when no Python is found."""
    try:
        diagnostic = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.platform(),
            "issue": "No Python installations found",
            "search_locations": {
                "windows_paths": [
                    "C:\\Python*",
                    "C:\\Program Files\\Python*",
                    "%USERPROFILE%\\AppData\\Local\\Programs\\Python\\",
                    "%USERPROFILE%\\AppData\\Local\\Microsoft\\WindowsApps\\",
                ],
                "unix_paths": [
                    "/usr/bin/python*",
                    "/usr/local/bin/python*",
                    "~/.local/bin/python*",
                    "/opt/python*/bin",
                ],
                "commands_tried": get_python_versions()[:10]  # First 10 for brevity
            },
            "recommendations": [
                "Download portable Python from python.org",
                "Install Python from Microsoft Store (Windows)",
                "Contact IT for Python installation",
                "Use cloud-based Python environment"
            ]
        }
        
        with open("python_diagnostic_report.json", 'w', encoding='utf-8') as f:
            json.dump(diagnostic, f, indent=2, ensure_ascii=False)
        
        print("🔍 Created diagnostic report: python_diagnostic_report.json")
    except Exception as e:
        print(f"Warning: Could not create diagnostic report: {e}")

def create_error_report(error_message):
    """Create an error report for unexpected issues."""
    try:
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.platform(),
            "error": error_message,
            "python_version": sys.version,
            "working_directory": os.getcwd()
        }
        
        with open("python_detection_error.json", 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        
        print("📄 Created error report: python_detection_error.json")
    except Exception:
        pass  # Don't fail on error reporting

if __name__ == "__main__":
    main() 