@echo off
REM Enhanced Corporate-Friendly Launcher for Development Automation Suite
REM Handles restricted environments and various Python installation scenarios
REM Version 2.0 - Enhanced compatibility and error handling

setlocal enabledelayedexpansion

REM Enable color output if supported
for /f "tokens=2 delims=[]" %%A in ('ver') do set "winver=%%A"
set "use_color=true"

echo.
echo ============================================================
echo   Development Automation Suite - Corporate Environment
echo   Enhanced Version 2.0 - Maximum Compatibility
echo ============================================================
echo   Platform: Windows %winver%
echo   Directory: %CD%
echo   User: %USERNAME%
echo   Computer: %COMPUTERNAME%
echo ============================================================
echo.

REM Initialize variables
set "working_python="
set "best_python="
set "best_score=0"
set "detection_log="

REM Function to log detection attempts
:log_attempt
set "detection_log=%detection_log%%~1%~n"
goto :eof

REM Enhanced function to test Python command with scoring
:test_python_with_score
set "python_cmd=%~1"
set "current_score=0"

echo Testing: %python_cmd%
call :log_attempt "Tested: %python_cmd%"

REM Test basic functionality
%python_cmd% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ❌ %python_cmd% - Version check failed
    goto :eof
)

REM Get version info for scoring
for /f "tokens=*" %%v in ('%python_cmd% --version 2^>^&1') do set "version_info=%%v"
echo   ✅ %python_cmd% - %version_info%

REM Score based on version (Python 3.8+ gets base score)
echo %version_info% | findstr /i "Python 3." >nul
if %errorlevel% equ 0 (
    set /a current_score+=50
    
    REM Bonus for newer versions
    echo %version_info% | findstr /i "Python 3.1" >nul
    if %errorlevel% equ 0 set /a current_score+=20
    
    echo %version_info% | findstr /i "Python 3.11" >nul
    if %errorlevel% equ 0 set /a current_score+=10
) else (
    echo   ❌ Version not suitable (need Python 3.8+)
    goto :eof
)

REM Test GUI support (critical)
echo   🧪 Testing GUI support...
%python_cmd% -c "import tkinter; print('GUI OK')" >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ GUI support available
    set /a current_score+=100
) else (
    echo   ❌ No GUI support (tkinter missing)
    goto :eof
)

REM Score based on installation type
echo %python_cmd% | findstr /i "py" >nul
if %errorlevel% equ 0 set /a current_score+=30

echo %python_cmd% | findstr /i "Program Files" >nul
if %errorlevel% equ 0 set /a current_score+=20

echo %python_cmd% | findstr /i "AppData" >nul
if %errorlevel% equ 0 set /a current_score+=15

echo   📊 Score: %current_score%

REM Update best Python if this one is better
if %current_score% gtr %best_score% (
    set "best_python=%python_cmd%"
    set "best_score=%current_score%"
    echo   🎯 New best candidate! (Score: %current_score%)
)

goto :eof

REM Main detection logic with enhanced methods
echo 🔍 Comprehensive Python Detection Starting...
echo.

REM Method 1: Python Launcher (most reliable in corporate environments)
echo 📍 Method 1: Python Launcher for Windows
call :test_python_with_score "py"
call :test_python_with_score "py -3.11"
call :test_python_with_score "py -3.10"
call :test_python_with_score "py -3.9"
call :test_python_with_score "py -3.8"
echo.

REM Method 2: Check for existing configuration
if exist python_config.json (
    echo 📍 Method 2: Saved Configuration
    for /f "usebackq tokens=2 delims=:" %%a in (`findstr "python_path" python_config.json 2^>nul`) do (
        set "config_path=%%a"
        REM Clean up the path (remove quotes, spaces, commas)
        set "config_path=!config_path: =!"
        set "config_path=!config_path:"=!"
        set "config_path=!config_path:,=!"
        if defined config_path (
            call :test_python_with_score "!config_path!"
        )
    )
    echo.
)

REM Method 3: Standard commands
echo 📍 Method 3: Standard Commands
call :test_python_with_score "python"
call :test_python_with_score "python3"
echo.

REM Method 4: Common installation paths (enhanced)
echo 📍 Method 4: Common Installation Paths
set "version_list=39 38 310 311 312 37"
set "base_paths=C:\Python{} "C:\Program Files\Python{}" "C:\Program Files (x86)\Python{}" "%USERPROFILE%\AppData\Local\Programs\Python\Python{}""

for %%v in (%version_list%) do (
    for %%p in (%base_paths%) do (
        set "test_path=%%~p"
        set "test_path=!test_path:{}=%%v!"
        set "python_exe=!test_path!\python.exe"
        if exist "!python_exe!" (
            call :test_python_with_score "!python_exe!"
        )
    )
)

REM Additional corporate paths
set "corp_paths=C:\Tools\Python\python.exe C:\Dev\Python\python.exe D:\Python\python.exe"
for %%p in (%corp_paths%) do (
    if exist "%%p" (
        call :test_python_with_score "%%p"
    )
)
echo.

REM Method 5: Microsoft Store and user installations
echo 📍 Method 5: Microsoft Store and User Installations
set "store_python=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\python.exe"
if exist "%store_python%" (
    call :test_python_with_score "%store_python%"
)

REM Conda installations
set "conda_paths=%USERPROFILE%\Anaconda3\python.exe %USERPROFILE%\Miniconda3\python.exe C:\Anaconda3\python.exe C:\Miniconda3\python.exe C:\ProgramData\Anaconda3\python.exe C:\ProgramData\Miniconda3\python.exe"
for %%p in (%conda_paths%) do (
    if exist "%%p" (
        call :test_python_with_score "%%p"
    )
)
echo.

REM Method 6: Try comprehensive detection script
echo 📍 Method 6: Running Enhanced Detection Script
if exist detect_python.py (
    echo Attempting to run Python detection script...
    
    REM Try different Python commands to run the script
    set "script_runners=py python"
    for %%r in (%script_runners%) do (
        %%r detect_python.py >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ Detection script completed successfully
            if exist python_config.json (
                echo 🔄 Reloading configuration...
                REM Re-read the config file
                for /f "usebackq tokens=2 delims=:" %%a in (`findstr "python_path" python_config.json 2^>nul`) do (
                    set "new_config_path=%%a"
                    set "new_config_path=!new_config_path: =!"
                    set "new_config_path=!new_config_path:"=!"
                    set "new_config_path=!new_config_path:,=!"
                    if defined new_config_path (
                        call :test_python_with_score "!new_config_path!"
                    )
                )
            )
            goto :detection_complete
        )
    )
    echo ⚠️  Could not run detection script automatically
) else (
    echo ⚠️  detect_python.py not found
)
echo.

:detection_complete
REM Evaluate results
if defined best_python (
    goto :start_app
) else (
    goto :no_python_found
)

:no_python_found
echo.
echo ❌ NO SUITABLE PYTHON INSTALLATION FOUND
echo.
echo 🔍 Detection Summary:
echo    Paths checked: %detection_log: =, %
echo    Best score achieved: %best_score%
echo    Minimum required score: 150 (50 version + 100 GUI)
echo.
echo 🔧 COMPREHENSIVE SOLUTIONS FOR CORPORATE ENVIRONMENTS:
echo.
echo 1. 📦 PORTABLE PYTHON (Recommended - No Admin Required):
echo    • Download: https://www.python.org/downloads/
echo    • Choose: "Windows embeddable zip file"
echo    • Extract to: Desktop, Documents, or any writable folder
echo    • Requirements: Python 3.8+ with tkinter
echo.
echo 2. 🪟 MICROSOFT STORE PYTHON:
echo    • Often pre-approved in corporate environments
echo    • Search "Python" in Microsoft Store
echo    • Automatic PATH setup
echo    • Includes tkinter by default
echo.
echo 3. 🏢 COMPANY SOFTWARE CATALOG:
echo    • Check internal software portal
echo    • Look for Python, Anaconda, or Miniconda
echo    • Submit IT request if available
echo.
echo 4. 📧 IT SUPPORT REQUEST:
echo    • Request Python 3.8+ installation
echo    • Specify need for tkinter package
echo    • Mention development productivity tools
echo    • Reference this error log
echo.
echo 5. 🔧 MANUAL DETECTION STEPS:
echo    • Check Programs and Features for Python
echo    • Look in Downloads folder for installers
echo    • Search C:\ for python.exe files
echo    • Try: where python /r c:\
echo.
echo 6. 🌐 CLOUD ALTERNATIVES:
echo    • GitHub Codespaces (VS Code in browser)
echo    • Google Colab (Jupyter notebooks)
echo    • Replit (online IDE)
echo    • GitPod (cloud development)
echo.

REM Create comprehensive help file
echo 📄 Creating detailed troubleshooting guide...
(
echo PYTHON DETECTION TROUBLESHOOTING GUIDE
echo =====================================
echo.
echo Generated: %DATE% %TIME%
echo Computer: %COMPUTERNAME%
echo User: %USERNAME%
echo Windows Version: %winver%
echo Working Directory: %CD%
echo.
echo DETECTION RESULTS:
echo - Paths checked: %detection_log: =, %
echo - Best score: %best_score%/150+ required
echo - Status: No suitable Python found
echo.
echo REQUIREMENTS FOR DEVELOPMENT AUTOMATION SUITE:
echo - Python 3.8 or higher
echo - tkinter package ^(for GUI support^)
echo - Accessible without admin rights
echo - Stable installation path
echo.
echo RECOMMENDED SOLUTIONS:
echo.
echo 1. PORTABLE PYTHON ^(Best for corporate environments^):
echo    Step 1: Visit https://www.python.org/downloads/
echo    Step 2: Download "Windows embeddable zip file"
echo    Step 3: Extract to user folder ^(e.g., C:\Users\%USERNAME%\Python^)
echo    Step 4: Re-run this script
echo.
echo 2. MICROSOFT STORE PYTHON:
echo    Step 1: Open Microsoft Store
echo    Step 2: Search for "Python"
echo    Step 3: Install ^(usually pre-approved^)
echo    Step 4: Re-run this script
echo.
echo 3. IT SUPPORT REQUEST:
echo    Subject: Python Development Environment Request
echo    Body: I need Python 3.8+ with tkinter for development automation.
echo          This will improve my productivity and code quality.
echo          Please install from python.org or enable Microsoft Store access.
echo.
echo TECHNICAL DETAILS FOR IT:
echo - Required: Python 3.8+ with tkinter
echo - Download: https://www.python.org/downloads/
echo - Installation: Standard or portable
echo - Purpose: Development automation and productivity tools
echo.
echo ALTERNATIVE APPROACHES:
echo - Portable Python ^(no installation required^)
echo - Anaconda/Miniconda ^(scientific Python distribution^)
echo - Python via Windows Subsystem for Linux ^(WSL^)
echo - Cloud-based development environments
echo.
echo PATHS SEARCHED:
%detection_log:~1%
echo.
echo NEXT STEPS:
echo 1. Try one of the recommended solutions above
echo 2. Re-run: start_corporate.bat
echo 3. Contact IT if needed with this report
echo 4. Consider cloud alternatives for immediate use
echo.
echo For immediate help, try: py --list ^(if py launcher exists^)
) > python_help.txt

echo ✅ Created: python_help.txt
echo.

REM Create JSON diagnostic report
(
echo {
echo   "timestamp": "%DATE% %TIME%",
echo   "platform": "Windows %winver%",
echo   "computer": "%COMPUTERNAME%",
echo   "user": "%USERNAME%",
echo   "directory": "%CD%",
echo   "issue": "No suitable Python installation found",
echo   "detection_score": %best_score%,
echo   "required_score": 150,
echo   "paths_checked": [
for %%p in (%detection_log:~1%) do echo     "%%p",
echo   ],
echo   "recommendations": [
echo     "Download portable Python from python.org",
echo     "Install Python from Microsoft Store",
echo     "Contact IT for Python installation",
echo     "Use cloud development environment"
echo   ]
echo }
) > python_diagnostic.json

echo ✅ Created: python_diagnostic.json
echo.
pause
goto :end

:start_app
echo.
echo 🎉 SUCCESS! Python Installation Found
echo =======================================
echo   Best Python: %best_python%
echo   Quality Score: %best_score%/150+
echo   Status: Ready for development
echo.

REM Save enhanced configuration
(
echo {
echo   "python_path": "%best_python%",
echo   "score": %best_score%,
echo   "detected_by": "start_corporate.bat v2.0",
echo   "detection_date": "%DATE% %TIME%",
echo   "platform": "Windows %winver%",
echo   "user": "%USERNAME%",
echo   "computer": "%COMPUTERNAME%",
echo   "working_directory": "%CD%"
echo }
) > python_config.json

echo 💾 Configuration saved: python_config.json
echo.

REM Create launcher scripts
echo 🚀 Creating enhanced launcher scripts...

REM Main launcher
(
echo @echo off
echo REM Auto-generated Python launcher
echo REM Python: %best_python%
echo REM Score: %best_score%
echo REM Generated: %DATE% %TIME%
echo.
echo setlocal
echo set "PYTHONPATH=%%PYTHONPATH%%;%CD%"
echo "%best_python%" %%*
echo if %%errorlevel%% neq 0 ^(
echo     echo Error: Python execution failed
echo     pause
echo ^)
echo endlocal
) > python_launcher.bat

REM Simple python.bat
(
echo @echo off
echo "%best_python%" %%*
) > python.bat

REM Pip launcher
(
echo @echo off
echo "%best_python%" -m pip %%*
) > pip.bat

echo ✅ Created launcher scripts:
echo    • python_launcher.bat ^(enhanced with error handling^)
echo    • python.bat ^(simple Python access^)
echo    • pip.bat ^(package manager^)
echo.

REM Verify application files
set "app_issues="
if not exist main.py (
    if not exist run.py (
        set "app_issues=No entry point found (main.py or run.py)"
    )
)

if defined app_issues (
    echo ⚠️  Application Issue: %app_issues%
    echo    Make sure you're in the correct directory
    echo.
    pause
    goto :end
)

REM Install dependencies if needed
if exist requirements.txt (
    echo 📦 Installing/updating dependencies...
    "%best_python%" -m pip install -r requirements.txt --user --quiet
    if %errorlevel% equ 0 (
        echo ✅ Dependencies updated successfully
    ) else (
        echo ⚠️  Some dependencies may not have installed correctly
        echo    Continuing anyway...
    )
    echo.
)

echo 🎯 Launching Development Automation Suite...
echo ============================================================
echo.

REM Determine entry point
set "entry_point=main.py"
if not exist main.py (
    if exist run.py (
        set "entry_point=run.py"
    )
)

REM Launch application with enhanced error handling
if "%best_python%"=="py" (
    py "%entry_point%"
) else if "%best_python%"=="py -3.11" (
    py -3.11 "%entry_point%"
) else if "%best_python%"=="py -3.10" (
    py -3.10 "%entry_point%"
) else if "%best_python%"=="py -3.9" (
    py -3.9 "%entry_point%"
) else if "%best_python%"=="py -3.8" (
    py -3.8 "%entry_point%"
) else (
    "%best_python%" "%entry_point%"
)

set "exit_code=%errorlevel%"

echo.
if %exit_code% neq 0 (
    echo ❌ Application exited with error code: %exit_code%
    echo.
    echo 🔧 Troubleshooting suggestions:
    echo    • Check if all dependencies are installed
    echo    • Verify Python installation is complete
    echo    • Try running: pip.bat install -r requirements.txt
    echo    • Check application logs for specific errors
    echo.
    echo 📄 Error details saved to: app_error.log
    echo Exit code %exit_code% >> app_error.log
    echo Timestamp: %DATE% %TIME% >> app_error.log
    echo Python: %best_python% >> app_error.log
    echo Entry point: %entry_point% >> app_error.log
    echo. >> app_error.log
    pause
) else (
    echo ✅ Application completed successfully
)

goto :end

:end
echo.
echo 👋 Session ended - %DATE% %TIME%
endlocal 