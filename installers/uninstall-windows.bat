@echo off
setlocal EnableExtensions
title Color Space Transform mk2 - uninstaller
rem Already elevated (or relaunched once)? Then continue - never loop.
if /I "%~1"=="--elevated" goto run
fltmc >nul 2>&1
if not errorlevel 1 goto run
goto elevate
:elevate
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '--elevated' -Verb RunAs"
exit /b
:run
set "DEST=%ProgramData%\Blackmagic Design\DaVinci Resolve\Support\LUT\Color Space Transform mk2"
if not exist "%DEST%\" goto none
rmdir /S /Q "%DEST%"
echo Removed: %DEST%
pause
exit /b 0
:none
echo Nothing to remove (not installed).
pause
exit /b 0
