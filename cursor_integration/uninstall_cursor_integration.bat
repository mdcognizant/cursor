@echo off
echo [UNINSTALL] Removing Cursor Shell Monitor Integration...
rmdir /s /q "C:\Projects\Cursor\Cursor\cursor_integration\bin"
rmdir /s /q "C:\Users\2419544\.cursor_monitor"
del /q "C:\Users\2419544\.cursor_monitor_config.json"
del /q "C:\Users\2419544\.cursor_monitor_commands.log"
del /q "C:\Users\2419544\.cursor_monitor_service.log"
echo [OK] Uninstallation complete
pause
