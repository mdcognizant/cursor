#!/bin/bash
# Enhanced Corporate-Friendly Launcher for Development Automation Suite
# Handles restricted environments and various Python installation scenarios
# Version 2.0 - Enhanced compatibility and error handling for Unix/Linux/macOS

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect platform
PLATFORM=$(uname -s)
ARCH=$(uname -m)
OS_VERSION=$(uname -r)
USER_NAME=$(whoami)
WORKING_DIR=$(pwd)

# Initialize variables
working_python=""
best_python=""
best_score=0
detection_log=""

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to log detection attempts
log_attempt() {
    detection_log="${detection_log}$1\n"
}

# Enhanced function to test Python command with scoring
test_python_with_score() {
    local python_cmd="$1"
    local current_score=0
    
    echo "Testing: $python_cmd"
    log_attempt "Tested: $python_cmd"
    
    # Test basic functionality
    if ! "$python_cmd" --version >/dev/null 2>&1; then
        print_color $RED "  ❌ $python_cmd - Version check failed"
        return 1
    fi
    
    # Get version info for scoring
    local version_info=$("$python_cmd" --version 2>&1)
    print_color $GREEN "  ✅ $python_cmd - $version_info"
    
    # Score based on version (Python 3.8+ gets base score)
    if echo "$version_info" | grep -i "Python 3\." >/dev/null; then
        current_score=$((current_score + 50))
        
        # Bonus for newer versions
        if echo "$version_info" | grep -E "Python 3\.(1[0-9]|[2-9][0-9])" >/dev/null; then
            current_score=$((current_score + 20))
        fi
        
        if echo "$version_info" | grep "Python 3\.11" >/dev/null; then
            current_score=$((current_score + 10))
        fi
    else
        print_color $RED "  ❌ Version not suitable (need Python 3.8+)"
        return 1
    fi
    
    # Test GUI support (critical for tkinter)
    echo "  🧪 Testing GUI support..."
    if "$python_cmd" -c "import tkinter; print('GUI OK')" >/dev/null 2>&1; then
        print_color $GREEN "  ✅ GUI support available"
        current_score=$((current_score + 100))
    else
        print_color $RED "  ❌ No GUI support (tkinter missing)"
        return 1
    fi
    
    # Score based on installation type and path
    if echo "$python_cmd" | grep -q "python3"; then
        current_score=$((current_score + 15))
    fi
    
    if echo "$python_cmd" | grep -q "/usr/local"; then
        current_score=$((current_score + 10))
    fi
    
    if echo "$python_cmd" | grep -q "anaconda\|miniconda"; then
        current_score=$((current_score + 25))
    fi
    
    if echo "$python_cmd" | grep -q "homebrew\|opt/homebrew"; then
        current_score=$((current_score + 20))
    fi
    
    print_color $CYAN "  📊 Score: $current_score"
    
    # Update best Python if this one is better
    if [ $current_score -gt $best_score ]; then
        best_python="$python_cmd"
        best_score=$current_score
        print_color $PURPLE "  🎯 New best candidate! (Score: $current_score)"
    fi
    
    return 0
}

# Function to find Python in virtual environments
find_venv_pythons() {
    local venv_paths=(
        "./venv/bin/python"
        "./venv/bin/python3"
        "./.venv/bin/python"
        "./.venv/bin/python3"
        "./env/bin/python"
        "./env/bin/python3"
        "$HOME/.virtualenvs/*/bin/python"
        "$HOME/.virtualenvs/*/bin/python3"
        "$HOME/venvs/*/bin/python"
        "$HOME/venvs/*/bin/python3"
        "$HOME/.pyenv/versions/*/bin/python"
    )
    
    for pattern in "${venv_paths[@]}"; do
        for python_path in $pattern; do
            if [ -x "$python_path" ] && [ ! -d "$python_path" ]; then
                test_python_with_score "$python_path"
            fi
        done
    done
}

# Main function
main() {
    clear
    print_color $BLUE "============================================================"
    print_color $BLUE "  Development Automation Suite - Corporate Environment"
    print_color $BLUE "  Enhanced Version 2.0 - Maximum Compatibility"
    print_color $BLUE "============================================================"
    echo "  Platform: $PLATFORM $OS_VERSION"
    echo "  Architecture: $ARCH"
    echo "  Directory: $WORKING_DIR"
    echo "  User: $USER_NAME"
    echo "  Hostname: $(hostname)"
    print_color $BLUE "============================================================"
    echo
    
    print_color $CYAN "🔍 Comprehensive Python Detection Starting..."
    echo
    
    # Method 1: Standard commands with version variations
    print_color $YELLOW "📍 Method 1: Standard Python Commands"
    local standard_commands=("python3" "python" "python3.11" "python3.10" "python3.9" "python3.8" "python3.12")
    
    for cmd in "${standard_commands[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            test_python_with_score "$cmd"
        fi
    done
    echo
    
    # Method 2: Check saved configuration
    if [ -f "python_config.json" ]; then
        print_color $YELLOW "📍 Method 2: Saved Configuration"
        local config_python=$(grep -o '"python_path":\s*"[^"]*"' python_config.json 2>/dev/null | cut -d'"' -f4)
        if [ -n "$config_python" ] && [ -x "$config_python" ]; then
            test_python_with_score "$config_python"
        fi
        echo
    fi
    
    # Method 3: Common installation paths
    print_color $YELLOW "📍 Method 3: Common Installation Paths"
    local common_paths=(
        "/usr/bin/python3" "/usr/bin/python"
        "/usr/local/bin/python3" "/usr/local/bin/python"
        "/opt/python3/bin/python3" "/opt/python/bin/python"
        "$HOME/.local/bin/python3" "$HOME/.local/bin/python"
        "/snap/bin/python3" "/snap/bin/python"
    )
    
    for path in "${common_paths[@]}"; do
        if [ -x "$path" ]; then
            test_python_with_score "$path"
        fi
    done
    echo
    
    # Method 4: Platform-specific paths
    print_color $YELLOW "📍 Method 4: Platform-Specific Paths"
    
    case "$PLATFORM" in
        "Darwin")  # macOS
            print_color $CYAN "  Detected macOS - Checking Homebrew and system paths"
            local macos_paths=(
                "/usr/local/opt/python@3.11/bin/python3"
                "/usr/local/opt/python@3.10/bin/python3"
                "/usr/local/opt/python@3.9/bin/python3"
                "/opt/homebrew/bin/python3"  # Apple Silicon
                "/usr/local/Cellar/python@*/bin/python3"
                "/opt/local/bin/python3"  # MacPorts
                "/sw/bin/python3"  # Fink
                "/Applications/Python 3.*/Python.app/Contents/MacOS/Python"
            )
            
            for pattern in "${macos_paths[@]}"; do
                for path in $pattern; do
                    if [ -x "$path" ] && [ ! -d "$path" ]; then
                        test_python_with_score "$path"
                    fi
                done
            done
            ;;
            
        "Linux")  # Linux
            print_color $CYAN "  Detected Linux - Checking distribution-specific paths"
            local linux_paths=(
                "/usr/bin/python3.*"
                "/opt/python*/bin/python3"
                "/usr/local/python*/bin/python3"
            )
            
            for pattern in "${linux_paths[@]}"; do
                for path in $pattern; do
                    if [ -x "$path" ] && [ ! -d "$path" ]; then
                        test_python_with_score "$path"
                    fi
                done
            done
            ;;
    esac
    echo
    
    # Method 5: Conda installations
    print_color $YELLOW "📍 Method 5: Conda Installations"
    local conda_paths=(
        "$HOME/anaconda3/bin/python"
        "$HOME/miniconda3/bin/python"
        "$HOME/miniforge3/bin/python"
        "$HOME/mambaforge3/bin/python"
        "/opt/anaconda3/bin/python"
        "/opt/miniconda3/bin/python"
        "$HOME/.conda/envs/*/bin/python"
    )
    
    for pattern in "${conda_paths[@]}"; do
        for path in $pattern; do
            if [ -x "$path" ] && [ ! -d "$path" ]; then
                test_python_with_score "$path"
            fi
        done
    done
    echo
    
    # Method 6: Virtual environments
    print_color $YELLOW "📍 Method 6: Virtual Environments"
    find_venv_pythons
    echo
    
    # Method 7: Try comprehensive detection script
    print_color $YELLOW "📍 Method 7: Enhanced Detection Script"
    if [ -f "detect_python.py" ]; then
        echo "Attempting to run Python detection script..."
        
        local script_runners=("python3" "python")
        for runner in "${script_runners[@]}"; do
            if command -v "$runner" >/dev/null 2>&1; then
                if "$runner" detect_python.py >/dev/null 2>&1; then
                    print_color $GREEN "✅ Detection script completed successfully"
                    if [ -f "python_config.json" ]; then
                        print_color $CYAN "🔄 Reloading configuration..."
                        local new_config_python=$(grep -o '"python_path":\s*"[^"]*"' python_config.json 2>/dev/null | cut -d'"' -f4)
                        if [ -n "$new_config_python" ] && [ -x "$new_config_python" ]; then
                            test_python_with_score "$new_config_python"
                        fi
                    fi
                    break
                fi
            fi
        done
    else
        print_color $YELLOW "⚠️  detect_python.py not found"
    fi
    echo
    
    # Evaluate results
    if [ -n "$best_python" ] && [ $best_score -ge 150 ]; then
        start_application
    else
        no_python_found
    fi
}

no_python_found() {
    echo
    print_color $RED "❌ NO SUITABLE PYTHON INSTALLATION FOUND"
    echo
    print_color $CYAN "🔍 Detection Summary:"
    echo "   Platform: $PLATFORM $OS_VERSION"
    echo "   Architecture: $ARCH"
    echo "   Best score achieved: $best_score"
    echo "   Minimum required score: 150 (50 version + 100 GUI)"
    echo
    print_color $YELLOW "🔧 COMPREHENSIVE SOLUTIONS FOR CORPORATE ENVIRONMENTS:"
    echo
    echo "1. 📦 SYSTEM PACKAGE MANAGER (Recommended):"
    
    case "$PLATFORM" in
        "Darwin")  # macOS
            echo "   • Homebrew: brew install python-tk"
            echo "   • MacPorts: sudo port install python311 +universal"
            echo "   • Official installer: https://www.python.org/downloads/"
            ;;
        "Linux")
            if command -v apt >/dev/null 2>&1; then
                echo "   • Ubuntu/Debian: sudo apt install python3 python3-tk"
            elif command -v yum >/dev/null 2>&1; then
                echo "   • RHEL/CentOS: sudo yum install python3 python3-tkinter"
            elif command -v dnf >/dev/null 2>&1; then
                echo "   • Fedora: sudo dnf install python3 python3-tkinter"
            elif command -v pacman >/dev/null 2>&1; then
                echo "   • Arch: sudo pacman -S python python-tk"
            else
                echo "   • Check your distribution's package manager"
            fi
            echo "   • Snap: snap install python3-tk"
            ;;
    esac
    
    echo
    echo "2. 🐍 CONDA/MINICONDA:"
    echo "   • Download: https://docs.conda.io/en/latest/miniconda.html"
    echo "   • Install: bash Miniconda3-latest-$PLATFORM-$ARCH.sh"
    echo "   • Includes tkinter by default"
    echo
    echo "3. 🏠 USER-SPACE INSTALLATION:"
    echo "   • Download Python source: https://www.python.org/downloads/"
    echo "   • Compile with: ./configure --prefix=\$HOME/python && make && make install"
    echo "   • No admin rights required"
    echo
    echo "4. 📧 IT SUPPORT REQUEST:"
    echo "   • Request Python 3.8+ with tkinter"
    echo "   • Mention development productivity needs"
    echo "   • Reference this error log"
    echo
    echo "5. 🌐 CLOUD ALTERNATIVES:"
    echo "   • GitHub Codespaces"
    echo "   • Google Colab"
    echo "   • Replit"
    echo "   • GitPod"
    echo
    
    # Create comprehensive help file
    print_color $CYAN "📄 Creating detailed troubleshooting guide..."
    
    cat > python_help.txt << EOF
PYTHON DETECTION TROUBLESHOOTING GUIDE
=====================================

Generated: $(date)
Platform: $PLATFORM $OS_VERSION ($ARCH)
User: $USER_NAME
Hostname: $(hostname)
Working Directory: $WORKING_DIR

DETECTION RESULTS:
- Best score: $best_score/150+ required
- Status: No suitable Python found
- Platform: $PLATFORM

REQUIREMENTS FOR DEVELOPMENT AUTOMATION SUITE:
- Python 3.8 or higher
- tkinter package (for GUI support)
- Accessible without admin rights
- Stable installation path

PLATFORM-SPECIFIC SOLUTIONS:

EOF

    case "$PLATFORM" in
        "Darwin")  # macOS
            cat >> python_help.txt << EOF
macOS SOLUTIONS:
1. HOMEBREW (Recommended):
   Step 1: Install Homebrew: /bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   Step 2: Install Python: brew install python-tk
   Step 3: Re-run this script

2. OFFICIAL INSTALLER:
   Step 1: Download from https://www.python.org/downloads/
   Step 2: Run the .pkg installer
   Step 3: Ensure "Install Python 3.x for all users" is checked

3. MACPORTS:
   Step 1: Install MacPorts from https://www.macports.org/
   Step 2: sudo port install python311 +universal
   Step 3: sudo port select --set python3 python311

EOF
            ;;
        "Linux")
            cat >> python_help.txt << EOF
LINUX SOLUTIONS:
1. PACKAGE MANAGER (Recommended):
   Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-tk
   RHEL/CentOS: sudo yum install python3 python3-tkinter
   Fedora: sudo dnf install python3 python3-tkinter
   Arch: sudo pacman -S python python-tk
   
2. SNAP PACKAGE:
   sudo snap install python3-tk
   
3. COMPILE FROM SOURCE (User space):
   wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz
   tar xzf Python-3.11.0.tgz
   cd Python-3.11.0
   ./configure --prefix=\$HOME/python --enable-shared
   make && make install

EOF
            ;;
    esac
    
    cat >> python_help.txt << EOF

GENERAL SOLUTIONS:
1. CONDA/MINICONDA:
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-$PLATFORM-$ARCH.sh
   bash Miniconda3-latest-$PLATFORM-$ARCH.sh
   
2. PYENV (Python Version Manager):
   curl https://pyenv.run | bash
   pyenv install 3.11.0
   pyenv global 3.11.0

VERIFICATION STEPS:
After installation, verify with:
- python3 --version (should show 3.8+)
- python3 -c "import tkinter" (should not error)

PATHS SEARCHED:
$(echo -e "$detection_log")

NEXT STEPS:
1. Try one of the platform-specific solutions above
2. Re-run: ./start_corporate.sh
3. Contact IT if needed with this report
4. Consider cloud alternatives for immediate use

EOF
    
    print_color $GREEN "✅ Created: python_help.txt"
    
    # Create JSON diagnostic report
    cat > python_diagnostic.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "platform": "$PLATFORM $OS_VERSION",
  "architecture": "$ARCH",
  "hostname": "$(hostname)",
  "user": "$USER_NAME",
  "directory": "$WORKING_DIR",
  "issue": "No suitable Python installation found",
  "detection_score": $best_score,
  "required_score": 150,
  "paths_checked": [
$(echo -e "$detection_log" | sed 's/Tested: /    "/' | sed 's/$/",/' | sed '$s/,$//')
  ],
  "recommendations": [
    "Install Python via system package manager",
    "Download and install Miniconda",
    "Contact IT for Python installation",
    "Use cloud development environment"
  ]
}
EOF
    
    print_color $GREEN "✅ Created: python_diagnostic.json"
    echo
    read -p "Press Enter to exit..."
    exit 1
}

start_application() {
    echo
    print_color $GREEN "🎉 SUCCESS! Python Installation Found"
    print_color $GREEN "======================================="
    echo "  Best Python: $best_python"
    echo "  Quality Score: $best_score/150+"
    echo "  Status: Ready for development"
    echo
    
    # Save enhanced configuration
    cat > python_config.json << EOF
{
  "python_path": "$best_python",
  "score": $best_score,
  "detected_by": "start_corporate.sh v2.0",
  "detection_date": "$(date -Iseconds)",
  "platform": "$PLATFORM $OS_VERSION",
  "architecture": "$ARCH",
  "user": "$USER_NAME",
  "hostname": "$(hostname)",
  "working_directory": "$WORKING_DIR"
}
EOF
    
    print_color $CYAN "💾 Configuration saved: python_config.json"
    echo
    
    # Create launcher scripts
    print_color $CYAN "🚀 Creating enhanced launcher scripts..."
    
    # Main launcher
    cat > python_launcher.sh << EOF
#!/bin/bash
# Auto-generated Python launcher
# Python: $best_python
# Score: $best_score
# Generated: $(date)

export PYTHONPATH="\$PYTHONPATH:$(pwd)"
"$best_python" "\$@"
exit_code=\$?

if [ \$exit_code -ne 0 ]; then
    echo "Error: Python execution failed (exit code: \$exit_code)"
    read -p "Press Enter to continue..."
fi

exit \$exit_code
EOF
    chmod +x python_launcher.sh
    
    # Simple python script
    cat > python.sh << EOF
#!/bin/bash
"$best_python" "\$@"
EOF
    chmod +x python.sh
    
    # Pip launcher
    cat > pip.sh << EOF
#!/bin/bash
"$best_python" -m pip "\$@"
EOF
    chmod +x pip.sh
    
    print_color $GREEN "✅ Created launcher scripts:"
    echo "   • python_launcher.sh (enhanced with error handling)"
    echo "   • python.sh (simple Python access)"
    echo "   • pip.sh (package manager)"
    echo
    
    # Verify application files
    local app_issues=""
    if [ ! -f "main.py" ] && [ ! -f "run.py" ]; then
        app_issues="No entry point found (main.py or run.py)"
    fi
    
    if [ -n "$app_issues" ]; then
        print_color $YELLOW "⚠️  Application Issue: $app_issues"
        echo "   Make sure you're in the correct directory"
        echo
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    # Install dependencies if needed
    if [ -f "requirements.txt" ]; then
        print_color $CYAN "📦 Installing/updating dependencies..."
        if "$best_python" -m pip install -r requirements.txt --user --quiet; then
            print_color $GREEN "✅ Dependencies updated successfully"
        else
            print_color $YELLOW "⚠️  Some dependencies may not have installed correctly"
            echo "   Continuing anyway..."
        fi
        echo
    fi
    
    print_color $BLUE "🎯 Launching Development Automation Suite..."
    print_color $BLUE "============================================================"
    echo
    
    # Determine entry point
    local entry_point="main.py"
    if [ ! -f "main.py" ] && [ -f "run.py" ]; then
        entry_point="run.py"
    fi
    
    # Launch application with enhanced error handling
    "$best_python" "$entry_point"
    local exit_code=$?
    
    echo
    if [ $exit_code -ne 0 ]; then
        print_color $RED "❌ Application exited with error code: $exit_code"
        echo
        print_color $YELLOW "🔧 Troubleshooting suggestions:"
        echo "   • Check if all dependencies are installed"
        echo "   • Verify Python installation is complete"
        echo "   • Try running: ./pip.sh install -r requirements.txt"
        echo "   • Check application logs for specific errors"
        echo
        echo "Exit code $exit_code" >> app_error.log
        echo "Timestamp: $(date)" >> app_error.log
        echo "Python: $best_python" >> app_error.log
        echo "Entry point: $entry_point" >> app_error.log
        echo "" >> app_error.log
        print_color $CYAN "📄 Error details saved to: app_error.log"
        read -p "Press Enter to exit..."
    else
        print_color $GREEN "✅ Application completed successfully"
    fi
    
    echo
    print_color $BLUE "👋 Session ended - $(date)"
    exit $exit_code
}

# Run main function
main "$@" 