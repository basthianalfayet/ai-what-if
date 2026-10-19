@echo off
rem Pemakaian: run_daily.bat pagi | siang | sore | malam | larut
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set SLOT=%1
if "%SLOT%"=="" set SLOT=auto
if not exist logs mkdir logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TGL=%%i
echo ===== %date% %time% slot %SLOT% ===== >> "logs\%TGL%.log"
if /I not "%SLOT%"=="batch" goto satuvideo
".venv\Scripts\python.exe" main.py --batch >> "logs\%TGL%.log" 2>&1
exit /b %ERRORLEVEL%
:satuvideo
".venv\Scripts\python.exe" main.py --slot %SLOT% >> "logs\%TGL%.log" 2>&1
