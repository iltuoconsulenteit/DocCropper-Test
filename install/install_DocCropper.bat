@echo off
setlocal
set REPO_URL=https://github.com/iltuoconsulenteit/DocCropper
if not defined DOCROPPER_DEV_LICENSE set DOCROPPER_DEV_LICENSE=ILTUOCONSULENTEIT-DEV
if not defined DOCROPPER_BRANCH set DOCROPPER_BRANCH=dgwo4q-codex/add-features-from-doccropper-project

set TARGET_DIR=
set /p TARGET_DIR=Installation directory [%%ProgramFiles%%\DocCropper]:
if "%TARGET_DIR%"=="" set TARGET_DIR=%ProgramFiles%\DocCropper
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
echo Installing to: %TARGET_DIR%

set DEFAULT_KEY=
if exist "%TARGET_DIR%\settings.json" (
  for /f "usebackq" %%K in (`python - <<PY
import json,sys
try:
    print(json.load(open(sys.argv[1])).get('license_key',''))
except Exception:
    pass
PY
 "%TARGET_DIR%\settings.json"`) do set DEFAULT_KEY=%%K
)
set /p LIC_KEY=Enter license key (leave blank for demo) [%DEFAULT_KEY%]:
if "%LIC_KEY%"=="" set LIC_KEY=%DEFAULT_KEY%
set BRANCH=main
if /I "%LIC_KEY%"=="%DOCROPPER_DEV_LICENSE%" set BRANCH=%DOCROPPER_BRANCH%



echo Checking required tools...
for %%C in (git python pip) do (
  where %%C >nul 2>&1
  if errorlevel 1 (
    echo %%C not found. Please install it first.
    pause
    exit /b 1
  )
)

if exist "%TARGET_DIR%\.git" (
  echo Repository already present at %TARGET_DIR%
  set /p UPD=Update the repository from GitHub? [s/N]
  if /I "%UPD%"=="s" (
    echo Updating repository...
    git -C "%TARGET_DIR%" pull --rebase --autostash origin %BRANCH%
  )
) else (
  echo Cloning repository in %TARGET_DIR%...
  git clone --branch %BRANCH% "%REPO_URL%" "%TARGET_DIR%"
)

echo Done.
set SETTINGS_FILE=%TARGET_DIR%\settings.json
if not exist "%SETTINGS_FILE%" (
  echo { "language": "en", "layout": 1, "orientation": "portrait", "arrangement": "auto", "scale_mode": "fit", "scale_percent": 100, "port": 8000, "license_key": "", "license_name": "" } > "%SETTINGS_FILE%"
)

rem License key already read above
if not "%LIC_KEY%"=="" (
  >"%TEMP%\checklic.py" echo import os,sys
  >>"%TEMP%\checklic.py" echo key=sys.argv[1].strip().upper()
  >>"%TEMP%\checklic.py" echo dev=os.environ.get('DOCROPPER_DEV_LICENSE','ILTUOCONSULENTEIT-DEV').upper()
  >>"%TEMP%\checklic.py" echo print('OK' if key in ('VALID',dev) else 'NO')
  for /f %%r in ('python "%TEMP%\checklic.py" "%LIC_KEY%"') do set VALID=%%r
  del "%TEMP%\checklic.py"
  if /I "%VALID%"=="OK" (
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
    if /I "%LIC_KEY%"=="%DOCROPPER_DEV_LICENSE%" (
      echo Switching to developer branch %DOCROPPER_BRANCH%
      git -C "%TARGET_DIR%" fetch origin %DOCROPPER_BRANCH%
      git -C "%TARGET_DIR%" checkout %DOCROPPER_BRANCH%
      git -C "%TARGET_DIR%" pull --rebase --autostash origin %DOCROPPER_BRANCH%
    )
  ) else (
    echo License key invalid. Continuing in demo mode.
  )
) else (
  echo Demo mode enabled
)
set /p RUN_APP=Launch DocCropper with tray icon now? [Y/n]
if /I "%RUN_APP%" NEQ "n" if /I "%RUN_APP%" NEQ "N" (
  pushd "%TARGET_DIR%"
  where pythonw >nul 2>&1 && (
    start "" pythonw doccropper_tray.py
  ) || (
    start "" python doccropper_tray.py
  )
  popd
)
endlocal
pause

