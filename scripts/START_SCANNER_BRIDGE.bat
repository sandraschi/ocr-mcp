@echo off
echo Starting Scanner Bridge Server...
echo This must be run on the Windows Host to enable scanner access from Docker.
echo.

cd /d "%~dp0"
cd ..

python -m uvicorn scripts.scanner_bridge_server:app --port 15002 --host 0.0.0.0 --reload

pause
