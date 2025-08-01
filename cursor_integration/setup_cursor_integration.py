#!/usr/bin/env python3
"""
Quick Setup for Cursor Shell Monitor Integration
One-command setup to integrate shell monitoring with Cursor IDE.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
import platform

def main():
    """Quick setup for Cursor integration."""
    print("🚀 Cursor Shell Monitor - Quick Setup")
    print("="*50)
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "shellmonitor").exists():
        print("❌ Error: Please run this from the project root directory")
        print("   (the directory containing shellmonitor/)")
        sys.exit(1)
    
    print("✅ Project structure found")
    
    # Run the installer
    try:
        installer_path = current_dir / "cursor_integration" / "install_cursor_integration.py"
        if installer_path.exists():
            print("🔧 Running main installer...")
            result = subprocess.run([sys.executable, str(installer_path)])
            if result.returncode != 0:
                print("❌ Installation failed")
                sys.exit(1)
        else:
            print("❌ Installer not found. Please ensure cursor_integration directory exists.")
            sys.exit(1)
        
        # Copy Cursor settings
        setup_cursor_settings()
        
        # Create quick launch script
        create_quick_launch()
        
        print("\n🎉 Quick Setup Complete!")
        print("="*50)
        
        print("\n📋 To activate in Cursor:")
        if platform.system() == "Windows":
            print("1. Copy these settings to your Cursor settings.json:")
            print("   File -> Preferences -> Settings -> Open Settings (JSON)")
        else:
            print("1. Copy the settings from cursor_integration/cursor_settings.json")
            print("   to your Cursor settings.json")
        
        print("\n2. Restart Cursor")
        print("3. Open a terminal in Cursor - you should see:")
        print("   🔍 Shell Monitor Active")
        
        print("\n✅ All commands in Cursor will now be monitored!")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

def setup_cursor_settings():
    """Setup Cursor-specific settings."""
    print("⚙️  Setting up Cursor configuration...")
    
    settings_file = Path.cwd() / "cursor_integration" / "cursor_settings.json"
    if not settings_file.exists():
        print("⚠️  Cursor settings file not found")
        return
    
    # Try to find Cursor's settings directory
    system = platform.system()
    cursor_dirs = []
    
    if system == "Windows":
        cursor_dirs = [
            Path.home() / "AppData" / "Roaming" / "Cursor" / "User",
            Path.home() / "AppData" / "Local" / "Cursor" / "User"
        ]
    elif system == "Darwin":  # macOS
        cursor_dirs = [
            Path.home() / "Library" / "Application Support" / "Cursor" / "User"
        ]
    else:  # Linux
        cursor_dirs = [
            Path.home() / ".config" / "Cursor" / "User"
        ]
    
    cursor_settings_path = None
    for cursor_dir in cursor_dirs:
        if cursor_dir.exists():
            cursor_settings_path = cursor_dir / "settings.json"
            break
    
    if cursor_settings_path and cursor_settings_path.parent.exists():
        try:
            # Backup existing settings
            if cursor_settings_path.exists():
                backup_path = cursor_settings_path.with_suffix('.json.backup')
                shutil.copy(cursor_settings_path, backup_path)
                print(f"📋 Backed up existing settings to {backup_path}")
            
            # Read our settings
            with open(settings_file, 'r') as f:
                our_settings = json.load(f)
            
            # Read existing settings if they exist
            existing_settings = {}
            if cursor_settings_path.exists():
                try:
                    with open(cursor_settings_path, 'r') as f:
                        existing_settings = json.load(f)
                except Exception:
                    existing_settings = {}
            
            # Merge settings (our settings take precedence)
            merged_settings = {**existing_settings, **our_settings}
            
            # Write merged settings
            with open(cursor_settings_path, 'w') as f:
                json.dump(merged_settings, f, indent=2)
            
            print(f"✅ Cursor settings updated: {cursor_settings_path}")
            
        except Exception as e:
            print(f"⚠️  Could not update Cursor settings: {e}")
            print("   Please manually copy settings from cursor_integration/cursor_settings.json")
    else:
        print("⚠️  Cursor settings directory not found")
        print("   Please manually copy settings from cursor_integration/cursor_settings.json")
        print("   to your Cursor settings.json file")

def create_quick_launch():
    """Create quick launch scripts."""
    print("🚀 Creating quick launch scripts...")
    
    integration_dir = Path.cwd() / "cursor_integration"
    
    if platform.system() == "Windows":
        # Windows batch script
        launch_script = integration_dir / "start_cursor_with_monitor.bat"
        script_content = f'''@echo off
echo 🚀 Starting Cursor with Shell Monitor...

REM Activate shell monitor
call "{integration_dir / 'setup_cursor_path.bat'}"

REM Start Cursor
echo [OK] Shell Monitor activated
echo [INFO] Opening Cursor...
start "" "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\cursor\\Cursor.exe" .

echo [INFO] Cursor is starting with shell monitoring enabled!
pause
'''
    else:
        # Unix shell script
        launch_script = integration_dir / "start_cursor_with_monitor.sh"
        script_content = f'''#!/bin/bash
echo "🚀 Starting Cursor with Shell Monitor..."

# Activate shell monitor
source "{integration_dir / 'setup_cursor_path.sh'}"

# Start Cursor
echo "✅ Shell Monitor activated"
echo "🔍 Opening Cursor..."

# Try common Cursor installation paths
if command -v cursor >/dev/null 2>&1; then
    cursor .
elif [ -f "/Applications/Cursor.app/Contents/MacOS/Cursor" ]; then
    /Applications/Cursor.app/Contents/MacOS/Cursor .
elif [ -f "/usr/local/bin/cursor" ]; then
    /usr/local/bin/cursor .
else
    echo "❌ Cursor not found. Please start Cursor manually."
fi

echo "💡 Cursor is starting with shell monitoring enabled!"
'''
    
    with open(launch_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    if platform.system() != "Windows":
        os.chmod(launch_script, 0o755)
    
    print(f"✅ Quick launch script created: {launch_script}")

if __name__ == "__main__":
    main() 