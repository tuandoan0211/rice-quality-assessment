@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Setup complete. Run run_app.bat
pause
exit /b 0
:fail
echo Setup failed. Check Python and your internet connection.
pause
exit /b 1
