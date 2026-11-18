@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Setup complete. Open the four notebooks or run mo_notebook.bat
pause
exit /b 0
:fail
echo Setup failed. Check Python and your internet connection.
pause
exit /b 1
