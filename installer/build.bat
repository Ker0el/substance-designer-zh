@echo off
setlocal
cd /d "%~dp0"
if "%ISCC%"=="" set "ISCC=D:\Other\Inno Setup Compiler\ISCC.exe"
"%ISCC%" build.iss
if errorlevel 1 (
  echo.
  echo Build failed.
  pause
  exit /b 1
)
echo.
echo Installer written to %~dp0..\dist
pause
