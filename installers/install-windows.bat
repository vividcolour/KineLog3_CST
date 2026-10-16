@echo off
setlocal EnableExtensions
title Color Space Transform mk2 - installer
rem Double-click to install. Windows will ask for administrator permission.

rem Already elevated (or relaunched once)? Then continue - never loop.
if /I "%~1"=="--elevated" goto install
fltmc >nul 2>&1
if not errorlevel 1 goto install
goto elevate

:elevate
echo Requesting administrator permission...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '--elevated' -Verb RunAs"
exit /b

:install
cd /d "%~dp0"
if exist "Color Space Transform mk2.dctl" goto havefiles
echo Can't find the .dctl files next to this installer.
echo Unzip the download first, then run the installer from the unzipped folder.
pause
exit /b 1

:havefiles
set "LUTROOT=%ProgramData%\Blackmagic Design\DaVinci Resolve\Support\LUT"
if exist "%LUTROOT%\" goto haveroot
echo DaVinci Resolve's LUT folder was not found:
echo   %LUTROOT%
echo Install/open DaVinci Resolve once, or copy the .dctl files manually - see READ ME FIRST.txt
pause
exit /b 1

:haveroot
set "DEST=%LUTROOT%\Color Space Transform mk2"
if not exist "%DEST%\Extras\" mkdir "%DEST%\Extras"
copy /Y "Color Space Transform mk2.dctl" "%DEST%\" >nul || goto fail
copy /Y "Color Remap mk2.dctl" "%DEST%\" >nul || goto fail
copy /Y "Extras\*.*" "%DEST%\Extras\" >nul || goto fail
echo.
echo Installed to: %DEST%
echo In Resolve: Project Settings ^> Color Management ^> Lookup Tables ^> Update Lists, or restart Resolve.
echo Then add a ResolveFX DCTL effect to a node and pick "Color Space Transform mk2\..." from the list.
echo.
pause
exit /b 0

:fail
echo.
echo Install failed - could not copy files to %DEST%
pause
exit /b 1
