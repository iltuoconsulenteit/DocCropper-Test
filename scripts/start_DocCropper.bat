@echo off
setlocal
set SCRIPT_DIR=%~dp0
set APP_DIR=%SCRIPT_DIR%..\
cd /d %APP_DIR%

for /f "delims=" %%p in ('python -c "import json,sys;\
try: d=json.load(open('settings.json')); print(d.get('port',8000))\
except Exception: print(8000)"') do set PORT=%%p

if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install --upgrade pip >nul
pip install -r requirements.txt >nul

echo Starting DocCropper on port %PORT%...
python main.py --host 0.0.0.0 --port %PORT%
endlocal
pause
