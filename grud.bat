@echo off
cd /d "%~dp0"
if exist .venv (
	echo Activating venv
	call .venv/scripts/activate.bat
)
start "" "pythonw" "%~dp0/main.py" %*
