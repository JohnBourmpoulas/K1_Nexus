#!/bin/zsh
# K1 Nexus launcher for macOS.
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  exec python3 k1_touch.py
fi
osascript -e 'display alert "K1 Nexus" message "Python 3 was not found. Install Python 3, then run K1 Nexus again."' 2>/dev/null || true
exit 1
