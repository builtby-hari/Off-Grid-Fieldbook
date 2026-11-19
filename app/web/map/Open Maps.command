#!/bin/bash
# Double-click to open the offline maps. Close this window to stop.
cd "$(dirname "$0")" && exec /usr/bin/python3 -I serve.py
