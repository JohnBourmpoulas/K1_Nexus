@echo off
REM K1 Nexus launcher for Windows.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 k1_touch.py
    goto :eof
)
where python >nul 2>nul
if %errorlevel%==0 (
    python k1_touch.py
    goto :eof
)
echo K1 Nexus requires Python 3.
echo Install Python 3 and enable "Add Python to PATH", then try again.
pause
