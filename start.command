#!/bin/bash
# ماك: اضغط مرتين على هذا الملف (أول مرة: chmod +x start.command)
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Python 3.8+ is required: https://www.python.org/downloads/"; read -p "Press Enter"; exit 1; }
python3 -m pip install --quiet --disable-pip-version-check --user -r requirements.txt || { echo "Could not install the requirements."; read -p "Press Enter"; exit 1; }
exec python3 run.py "$@"
