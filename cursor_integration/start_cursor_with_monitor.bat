@echo off
echo 🚀 Starting Cursor with Shell Monitor...

REM Activate shell monitor
call "C:\Projects\Cursor\Cursor\cursor_integration\setup_cursor_path.bat"

REM Start Cursor
echo [OK] Shell Monitor activated
echo [INFO] Opening Cursor...
start "" "C:\Users\%USERNAME%\AppData\Local\Programs\cursor\Cursor.exe" .

echo [INFO] Cursor is starting with shell monitoring enabled!
pause
