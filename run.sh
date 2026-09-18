#!/usr/bin/env bash
# One-command start for the AP Tutor bot (Mac/Linux).
# First run: launches the setup wizard. After that: starts the bot.
# You can double-click this in most file managers, or run: ./run.sh

cd "$(dirname "$0")" || exit 1

# Find a Python 3.
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  echo "Python 3 isn't installed. Get it from https://www.python.org/downloads/ and rerun."
  read -r -p "Press Enter to close."
  exit 1
fi

# Use a local virtual environment so nothing else on the computer is touched.
if [ ! -d ".venv" ]; then
  echo "Setting up a private environment (first time only)..."
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Make sure dependencies are present.
pip install -q -r requirements.txt

# No .env yet? Run the friendly wizard. Otherwise just start the bot.
if [ ! -f ".env" ]; then
  python setup.py
else
  python bot.py
fi

# Keep the window open if it was double-clicked and the bot exited/errored.
echo
read -r -p "The bot stopped. Press Enter to close this window."
