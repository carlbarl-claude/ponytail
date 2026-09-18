@echo off
REM ============================================================
REM  Build NFS_Run_Trainer.exe  (run this ON your Windows PC)
REM  Just double-click this file. It needs Python installed:
REM  https://www.python.org/downloads/  (tick "Add to PATH")
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo === Checking Python ===
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Python is not installed or not on PATH.
    echo   Install it from https://www.python.org/downloads/
    echo   and tick "Add python.exe to PATH" during setup, then run this again.
    echo.
    pause
    exit /b 1
)

echo.
echo === Installing dependencies (pymem, pyinstaller) ===
python -m pip install --upgrade pip
python -m pip install pymem pyinstaller
if errorlevel 1 (
    echo.
    echo   Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo === Building NFS_Run_Trainer.exe ===
python -m PyInstaller --onefile --noconsole --name "NFS_Run_Trainer" nfs_trainer.py
if errorlevel 1 (
    echo.
    echo   Build failed. Scroll up for the error.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   DONE!  Your app is here:
echo       dist\NFS_Run_Trainer.exe
echo   Right-click it -^> "Run as administrator" to use it.
echo ============================================================
echo.
pause
