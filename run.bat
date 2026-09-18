@echo off
REM One-command start for the AP Tutor bot (Windows).
REM First run: launches the setup wizard. After that: starts the bot.
REM Double-click this file, or run it from Command Prompt.

cd /d "%~dp0"

REM Find Python.
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo Python isn't installed. Get it from https://www.python.org/downloads/
  echo During install, tick "Add Python to PATH", then rerun this file.
  pause
  exit /b 1
)

REM Use a local virtual environment so nothing else on the computer is touched.
if not exist ".venv" (
  echo Setting up a private environment ^(first time only^)...
  %PY% -m venv .venv
)
call .venv\Scripts\activate.bat

REM Make sure dependencies are present.
pip install -q -r requirements.txt

REM No .env yet? Run the friendly wizard. Otherwise just start the bot.
if not exist ".env" (
  python setup.py
) else (
  python bot.py
)

echo.
echo The bot stopped.
pause
