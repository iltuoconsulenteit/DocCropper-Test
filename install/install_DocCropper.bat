@echo off
setlocal
set REPO_URL=https://github.com/iltuoconsulenteit/DocCropper
set SCRIPT_DIR=%~dp0
set PARENT_DIR=%~dp0..\
rem If the script sits inside the repo's install folder we update the parent
rem otherwise we create a DocCropper folder alongside the script
if exist "%SCRIPT_DIR%\.git" (
  set TARGET_DIR=%SCRIPT_DIR%
) else if exist "%PARENT_DIR%\.git" (
  set TARGET_DIR=%PARENT_DIR%
) else (
  set TARGET_DIR=%SCRIPT_DIR%DocCropper
)

echo Checking required tools...
for %%C in (git python pip) do (
  where %%C >nul 2>&1
  if errorlevel 1 (
    echo %%C not found. Please install it first.
    exit /b 1
  )
)

if exist "%TARGET_DIR%\.git" (
  echo Repository already present at %TARGET_DIR%
  set /p UPD=Update the repository from GitHub? [s/N]
  if /I "%UPD%"=="s" (
    echo Updating repository...
    git -C "%TARGET_DIR%" pull --rebase --autostash
  )
) else (
  echo Cloning repository in %TARGET_DIR%...
  git clone "%REPO_URL%" "%TARGET_DIR%"
)

echo Done.
set SETTINGS_FILE=%TARGET_DIR%\settings.json
if not exist "%SETTINGS_FILE%" (
  echo { "language": "en", "layout": 1, "orientation": "portrait", "arrangement": "auto", "scale_mode": "fit", "scale_percent": 100, "license_key": "", "license_name": "" } > "%SETTINGS_FILE%"
)

set /p LIC_KEY=Enter license key (leave blank for demo):
if not "%LIC_KEY%"=="" (
  set /p LIC_NAME=Licensed to:
  set "SF=%SETTINGS_FILE%"
  set "KY=%LIC_KEY%"
  set "NM=%LIC_NAME%"
  >"%TEMP%\updlic.py" echo import json, os
  >>"%TEMP%\updlic.py" echo f=os.environ['SF']
  >>"%TEMP%\updlic.py" echo data=json.load(open(f))
  >>"%TEMP%\updlic.py" echo data['license_key']=os.environ['KY']
  >>"%TEMP%\updlic.py" echo data['license_name']=os.environ['NM']
  >>"%TEMP%\updlic.py" echo json.dump(data,open(f,'w'))
  python "%TEMP%\updlic.py"
  del "%TEMP%\updlic.py"
  echo License saved
) else (
  echo Demo mode enabled
)
endlocal

