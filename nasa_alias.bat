@echo off
REM NASA Server Command Aliases for Windows

if /i "%1"=="run" if /i "%2"=="nasa" if /i "%3"=="server" (
    if /i "%4"=="with" if /i "%5"=="mcp" (
        python cursor_commands.py "run nasa server with mcp and grpc"
    ) else (
        python cursor_commands.py "run nasa server"
    )
    goto :eof
)

if /i "%1"=="nasa" (
    python cursor_commands.py "run nasa server"
    goto :eof
)

if /i "%1"=="open" if /i "%2"=="nasa" (
    python cursor_commands.py "open nasa server"
    goto :eof
)

if /i "%1"=="start" if /i "%2"=="nasa" (
    python cursor_commands.py "start nasa server"
    goto :eof
)

if /i "%1"=="stop" if /i "%2"=="nasa" (
    python cursor_commands.py "stop nasa server"
    goto :eof
)

echo Unknown command: %*
echo Available commands:
echo   run nasa server
echo   run nasa server with mcp and grpc
echo   open nasa server
echo   start nasa server
echo   stop nasa server
echo   nasa
