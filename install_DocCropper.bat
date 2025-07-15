@echo off
setlocal
set REPO_URL=https://github.com/iltuoconsulenteit/DocCropper
set SCRIPT_DIR=%~dp0
rem If the script sits inside a clone we update that, otherwise we create a
rem DocCropper folder alongside the script
if exist "%SCRIPT_DIR%\.git" (
  set TARGET_DIR=%SCRIPT_DIR%
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
    git -C "%TARGET_DIR%" pull --rebase
  )
) else (
  echo Cloning repository in %TARGET_DIR%...
  git clone "%REPO_URL%" "%TARGET_DIR%"
)

echo Done.
endlocal

