# Shell Monitor - Correct Working Syntax Reference

## Purpose
Shell Monitor is a Python utility to monitor and diagnose shell command execution issues in Cursor, especially for commands that hang or timeout.

## Available Shell Monitor Scripts

### 1. Root Level Shell Monitor
**File:** `shell_monitor.py` (in project root)
**Imports from:** `src.shell_monitor.cli`

### 2. Shellmonitor Directory Shell Monitor  
**File:** `shellmonitor/shell_monitor.py`
**Imports from:** `shellmonitor.cli`

## Correct Command Syntax

### Basic Command Execution with Monitoring
```bash
# Using root level shell monitor
python shell_monitor.py run "your_command_here"

# Using shellmonitor directory version
python shellmonitor/shell_monitor.py run "your_command_here"
```

### Examples
```bash
# Open HTML file in browser with monitoring
python shell_monitor.py run "start universal-api-bridge/monerium_standalone.html"

# Run git commands with monitoring
python shell_monitor.py run "git status"

# Execute Python scripts with monitoring
python shell_monitor.py run "python some_script.py"

# Run network tests with monitoring
python shell_monitor.py run "curl -X GET http://localhost:8003/health"
```

### Diagnostic Commands
```bash
# Run system diagnostics
python shell_monitor.py diagnose

# Interactive shell monitor mode
python shell_monitor.py interactive
```

## Key Benefits
- **Timeout Management:** Prevents commands from hanging indefinitely
- **Performance Monitoring:** Tracks command execution time
- **Error Diagnosis:** Provides detailed error reporting
- **Corporate Environment:** Handles network restrictions and firewall issues

## When to Use Shell Monitor
1. **Commands that might hang** (network calls, file operations)
2. **Corporate network environments** (with firewalls like Zscaler)
3. **Opening files in browser** (when `start` command might hang)
4. **Running servers or long-running processes**
5. **Debugging command execution issues**

## Memory Note
Always use shell monitor for command execution when there's a risk of hanging, especially in corporate environments or when dealing with network operations. 