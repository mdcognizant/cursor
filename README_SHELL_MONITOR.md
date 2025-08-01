# Shell Monitor - Cursor Command Execution Monitor

> **A Python utility to monitor shell commands and diagnose performance issues that cause Cursor to get stuck.**

## 🎯 **Problem Solved**

Cursor IDE sometimes gets stuck when executing shell commands, especially:
- Git operations that hang indefinitely
- Package installations that freeze
- Build processes that timeout
- PowerShell profile loading issues
- PATH configuration problems

This utility provides **real-time monitoring**, **timeout detection**, and **comprehensive diagnostics** to identify and resolve these issues.

## ✨ **Features**

### **Core Monitoring**
- ⏱️ **Live Timer**: Real-time display of command execution time
- ⚠️ **Timeout Detection**: Configurable timeout with user interaction
- 🔄 **Retry Mechanism**: Intelligent retry with clean shell environment
- 🔪 **Process Control**: Safe process termination across platforms

### **Interactive Options on Timeout**
1. **Retry**: Run the command again
2. **Kill**: Terminate the current process
3. **Diagnose**: Run comprehensive performance diagnostics
4. **Continue**: Keep waiting for the command
5. **Quit**: Exit the monitor

### **Comprehensive Diagnostics**
- 🐚 **Shell Detection**: Identifies PowerShell, Git Bash, CMD
- 📊 **Profile Analysis**: Checks PowerShell startup scripts
- 🛣️ **PATH Validation**: Validates all PATH entries
- 🔗 **Git Hooks**: Examines Git hooks in `.git/hooks/`
- ⚡ **Performance Testing**: Measures Git command latency
- 💾 **System Resources**: Checks memory and disk space

### **Bonus Features**
- 📝 **Verbose Logging**: Detailed logs with file output
- 📜 **Command History**: Track of last 5 slow commands
- 🧹 **Clean Shell**: Execute with minimal environment
- 🎛️ **Configuration**: Persistent settings management
- 🔍 **Interactive Mode**: Ongoing command monitoring

## 🚀 **Quick Start**

### **1. Direct Usage (No Installation)**
```bash
# Navigate to your project directory
cd /path/to/your/project

# Monitor a command
python shell_monitor.py run "git status"

# Monitor with custom timeout
python shell_monitor.py run "npm install" --timeout 300

# Run diagnostics
python shell_monitor.py diagnose

# Interactive mode
python shell_monitor.py interactive
```

### **2. Get Help**
```bash
python shell_monitor.py --help
python shell_monitor.py run --help
python shell_monitor.py diagnose --help
```

## 📋 **Usage Examples**

### **Monitor Single Commands**
```bash
# Basic monitoring
python shell_monitor.py run "git log --oneline -10"

# With clean environment
python shell_monitor.py run "git status" --clean

# With verbose output
python shell_monitor.py run "npm test" --verbose --timeout 180

# Force specific shell
python shell_monitor.py run "Get-Process" --shell powershell
```

### **Diagnostic Testing**
```bash
# Run all diagnostics
python shell_monitor.py diagnose

# Verbose diagnostics with report
python shell_monitor.py diagnose --verbose --save-report
```

### **Interactive Mode**
```bash
# Start interactive session
python shell_monitor.py interactive

# With auto-diagnostics on timeout
python shell_monitor.py interactive --auto-diagnose
```

### **History and Statistics**
```bash
# Show command history
python shell_monitor.py history

# Show only slow commands
python shell_monitor.py history --slow-only

# Show execution statistics
python shell_monitor.py stats
```

### **Configuration**
```bash
# Show current settings
python shell_monitor.py config --show

# Set default timeout
python shell_monitor.py config --set-timeout 120

# Enable auto-diagnostics
python shell_monitor.py config --enable-auto-diagnose

# Reset to defaults
python shell_monitor.py config --reset
```

## 🔧 **Installation**

### **Option 1: Standalone (Recommended)**
No installation needed! Just download and run:

```bash
# Clone or download the files
# Required structure:
project/
├── shell_monitor.py          # Main script
├── src/shell_monitor/
│   ├── __init__.py
│   ├── monitor.py            # Core monitoring
│   ├── diagnostics.py        # Diagnostic engine
│   └── cli.py               # Command line interface
```

### **Option 2: Add to Existing Project**
Copy the shell monitor files to your existing project:

```bash
# Copy to your project
cp -r src/shell_monitor /path/to/your/project/src/
cp shell_monitor.py /path/to/your/project/
```

### **Option 3: System-wide Installation**
```bash
# Add to your PATH or create an alias
alias shell-monitor='python /path/to/shell_monitor.py'

# Or create a batch file (Windows)
echo @python C:\path\to\shell_monitor.py %* > shell-monitor.bat
```

## 📊 **Diagnostic Categories**

### **1. Shell Environment**
- Shell type detection (PowerShell, Bash, CMD)
- Environment variable analysis
- Startup script examination

### **2. PowerShell Profile (Windows)**
- Profile location detection
- Load time measurement
- Module import analysis

### **3. PATH Configuration**
- PATH length and entry count
- Invalid path detection
- Duplicate entry identification

### **4. Git Environment**
- Git installation verification
- Hook performance analysis
- Repository status checking

### **5. Command Performance**
- Git command latency testing
- Shell startup time measurement
- Process execution profiling

### **6. System Resources**
- Memory usage analysis
- Disk space verification
- Resource constraint detection

## 🎛️ **Configuration Options**

### **Persistent Settings**
Settings are stored in `~/.shell_monitor_config.json`:

```json
{
  "timeout": 60,
  "verbose": false,
  "log_file": null,
  "auto_diagnose": false,
  "max_history": 100
}
```

### **Command Line Options**
```
Global Options:
  --timeout, -t      Command timeout in seconds (default: 60)
  --verbose, -v      Enable verbose output
  --log-file, -l     Log file path for detailed logging
  --shell, -s        Force specific shell (powershell, bash, cmd)
  --cwd, -d          Working directory for command execution

Run Command Options:
  --clean           Run with clean shell environment
  --no-diagnostics  Disable auto-diagnostics on timeout

Interactive Mode Options:
  --auto-diagnose   Automatically run diagnostics on timeouts

History Options:
  --slow-only       Show only slow commands (>5s)
  --count, -n       Number of commands to show

Config Options:
  --show            Show current configuration
  --reset           Reset to default configuration
  --set-timeout     Set default timeout
  --set-log-file    Set default log file
```

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **"Module not found" errors**
```bash
# Make sure you're in the correct directory
pwd
ls -la src/shell_monitor/

# Check Python path
python -c "import sys; print(sys.path)"
```

#### **Permission denied on process termination**
```bash
# Run with elevated privileges if needed (Windows)
# Right-click Command Prompt -> "Run as administrator"

# On Unix/Linux, check process permissions
ps aux | grep python
```

#### **PowerShell execution policy errors**
```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy (if allowed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Git commands hang in diagnostics**
```bash
# Check if you're in a Git repository
git status

# Check for large repositories
du -sh .git/

# Check for network issues
git config --get remote.origin.url
```

### **Diagnostic Interpretation**

#### **Status Icons**
- ✅ **Pass**: No issues detected
- ⚠️ **Warning**: Potential performance impact
- ❌ **Fail**: Critical issue requiring attention

#### **Common Warnings**
- **Large PATH**: Too many PATH entries (>50)
- **Slow Git**: Git commands taking >3 seconds
- **Heavy Profile**: PowerShell profile loading >5 seconds
- **Invalid Paths**: Non-existent directories in PATH

#### **Recommended Actions**
- Clean up PATH environment variable
- Optimize PowerShell profile scripts
- Remove unused Git hooks
- Check for repository corruption
- Verify network connectivity

## 📈 **Performance Tips**

### **Optimize Shell Startup**
1. **PowerShell Profile**:
   - Remove unnecessary module imports
   - Use lazy loading for heavy operations
   - Move complex logic to separate scripts

2. **Bash Profile**:
   - Minimize `.bashrc` and `.bash_profile`
   - Use conditional loading
   - Avoid heavy network operations

### **Optimize PATH**
1. **Remove Duplicates**:
   ```bash
   # Windows PowerShell
   $env:PATH = ($env:PATH.Split(';') | Select-Object -Unique) -join ';'
   
   # Unix/Linux Bash
   export PATH=$(echo $PATH | tr ':' '\n' | sort -u | tr '\n' ':')
   ```

2. **Remove Invalid Entries**:
   - Delete non-existent directories
   - Remove obsolete software paths
   - Keep only essential tools

### **Optimize Git Performance**
1. **Repository Maintenance**:
   ```bash
   git gc --aggressive
   git repack -ad
   git prune
   ```

2. **Configuration Tweaks**:
   ```bash
   git config core.preloadindex true
   git config core.fscache true
   git config gc.auto 256
   ```

## 🔍 **Advanced Usage**

### **Custom Timeouts for Different Commands**
```bash
# Quick commands
python shell_monitor.py run "git status" --timeout 10

# Build processes
python shell_monitor.py run "npm run build" --timeout 600

# Package installations
python shell_monitor.py run "pip install -r requirements.txt" --timeout 300
```

### **Integration with CI/CD**
```bash
#!/bin/bash
# ci-with-monitoring.sh

# Monitor critical CI commands
python shell_monitor.py run "npm ci" --timeout 300 --log-file ci.log
if [ $? -ne 0 ]; then
    echo "npm ci failed or timed out"
    python shell_monitor.py diagnose --save-report
    exit 1
fi

python shell_monitor.py run "npm test" --timeout 600 --log-file ci.log
```

### **Automated Diagnostics**
```bash
# Run diagnostics and save report
python shell_monitor.py diagnose --save-report

# Check for issues in the report
if grep -q '"status": "fail"' ~/.shell_diagnostic_report_*.json; then
    echo "Critical issues found in shell environment"
    # Send alert or take corrective action
fi
```

## 📞 **Support**

### **Getting Help**
1. **Built-in Help**: `python shell_monitor.py --help`
2. **Verbose Mode**: Add `--verbose` to any command
3. **Diagnostic Reports**: Check `~/.shell_diagnostic_report_*.json`
4. **Log Files**: Enable with `--log-file monitor.log`

### **Common Command Reference**
```bash
# Essential commands
python shell_monitor.py run "command"      # Monitor command
python shell_monitor.py diagnose           # Run diagnostics
python shell_monitor.py interactive        # Interactive mode
python shell_monitor.py history            # Show history
python shell_monitor.py config --show      # Show config

# Advanced usage
python shell_monitor.py run "cmd" --clean  # Clean environment
python shell_monitor.py run "cmd" -v -t 120 --log-file debug.log
python shell_monitor.py interactive --auto-diagnose
```

---

## 🎉 **Success!**

You now have a powerful tool to monitor and diagnose shell command execution issues in Cursor. The utility will help you:

- **Identify stuck commands** before they cause problems
- **Diagnose performance bottlenecks** in your development environment
- **Optimize shell configuration** for better performance
- **Maintain command history** for analysis
- **Retry failed commands** with different environments

**Happy coding!** 🚀 