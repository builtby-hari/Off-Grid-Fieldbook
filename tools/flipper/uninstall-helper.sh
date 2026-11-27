#!/bin/bash
# Removes the Off-Grid hub helper that install-helper.sh set up for the current user.
#   tools/flipper/uninstall-helper.sh
set -uo pipefail
LABEL="com.builtbyhari.offgrid.hubhelper"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
rm -rf "$HOME/Library/Application Support/Off-Grid/hub-helper"
echo "Removed. Plugging in a hub no longer opens Off-Grid Fieldbook."
echo "The log at ~/Library/Logs/Off-Grid-hub-helper.log was kept; delete it if you like."
