@echo off
setlocal
set REPO_URL=https://github.com/iltuoconsulenteit/DocCropper
set TARGET_DIR=%USERPROFILE%\Desktop\DocCropper

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
  echo Cloning repository...
  git clone "%REPO_URL%" "%TARGET_DIR%"
)

echo Done.
endlocal

