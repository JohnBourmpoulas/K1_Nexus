#!/usr/bin/env sh
# K1 Nexus launcher for Linux.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
    exec python3 k1_touch.py
elif command -v python >/dev/null 2>&1; then
    exec python k1_touch.py
else
    printf '%s\n' 'K1 Nexus requires Python 3 with Tkinter.' >&2
    exit 1
fi
