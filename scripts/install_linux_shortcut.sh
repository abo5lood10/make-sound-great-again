#!/bin/bash
# ينشئ أيقونة على سطح المكتب وفي قائمة التطبيقات (Linux)
DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENTRY="[Desktop Entry]
Type=Application
Name=Make Sound Great Again
Comment=Improve the quality of any song
Exec=python3 $DIR/run.py
Path=$DIR
Icon=$DIR/assets/icon.png
Terminal=false
Categories=AudioVideo;Audio;"
mkdir -p "$HOME/.local/share/applications"
echo "$ENTRY" > "$HOME/.local/share/applications/make-sound-great-again.desktop"
DESK="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$DESK" ]; then
  echo "$ENTRY" > "$DESK/make-sound-great-again.desktop"
  chmod +x "$DESK/make-sound-great-again.desktop"
fi
echo "Shortcut created."
