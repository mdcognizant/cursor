#!/usr/bin/env python3
"""
Development Automation Suite Launcher
Simple script to launch the application with proper error handling.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is supported."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again.")
        return False
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_modules = [
        ('tkinter', 'tkinter'),
        ('yaml', 'PyYAML'),
        ('pathlib', 'pathlib')
    ]
    
    missing_modules = []
    
    for module, package in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(package)
    
    if missing_modules:
        print("❌ Error: Missing required dependencies:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n🔧 To install missing dependencies, run:")
        print("   pip install -r requirements.txt")
        print("   or")
        print("   pip install development-automation-suite")
        return False
    
    return True

def setup_environment():
    """Setup necessary environment and paths."""
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Create necessary directories
    config_dir = Path.home() / ".dev_automation"
    config_dir.mkdir(exist_ok=True)
    
    logs_dir = config_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    templates_dir = config_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    return True

def main():
    """Main launcher function."""
    print("🚀 Starting Development Automation Suite...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    print("⚙️  Setting up environment...")
    if not setup_environment():
        print("❌ Failed to setup environment")
        sys.exit(1)
    
    print("✅ All checks passed!")
    print("🎯 Launching GUI application...")
    print("-" * 50)
    
    try:
        # Import and run the main application
        from main import main as app_main
        app_main()
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
        sys.exit(0)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure you're running from the correct directory")
        print("   and all dependencies are installed.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Please check the logs for more details.")
        print("   If the problem persists, please report it as an issue.")
        sys.exit(1)

if __name__ == "__main__":
    main() 