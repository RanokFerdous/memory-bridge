@echo off
title Memory Bridge — Build to EXE
color 0A

echo ================================================
echo   Memory Bridge — PyInstaller Build Script
echo ================================================
echo.

REM Check if pyinstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [*] PyInstaller not found. Installing...
    pip install pyinstaller
    echo.
)

REM Clean previous build
echo [1/3] Cleaning previous build...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist
echo     Done.
echo.

REM Build the exe
echo [2/3] Building MemoryBridge.exe (this takes 1-3 minutes)...
pyinstaller memory_bridge.spec
echo.

REM Check success
if exist "dist\MemoryBridge.exe" (
    echo [3/3] SUCCESS!
    echo.
    echo     Your app is ready at:
    echo     dist\MemoryBridge.exe
    echo.
    echo     Share that single file with anyone on Windows.
    echo     No Python installation needed on their computer!
    echo.
    explorer dist
) else (
    echo [3/3] BUILD FAILED — check the output above for errors.
)

pause
