#!/bin/bash
# Installs the Off-Grid hub helper for the current user: plug in an Off-Grid hub drive and
# Off-Grid Fieldbook opens on the map. Other drives are ignored. Undo with uninstall-helper.sh.
#   tools/flipper/install-helper.sh [pack]     (pack defaults to texas)
# For your own Mac only. Nothing is installed system-wide and no admin password is needed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.builtbyhari.offgrid.hubhelper"
PACK="${1:-texas}"
case "$PACK" in *[!A-Za-z0-9_-]*|"") echo "Pack name can only have letters, numbers, - and _." >&2; exit 1 ;; esac
DIR="$HOME/Library/Application Support/Off-Grid/hub-helper"
AGENT="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/Off-Grid-hub-helper.log"

mkdir -p "$DIR" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cp "$HERE/offgrid-hub-helper.sh" "$DIR/offgrid-hub-helper.sh"
chmod 755 "$DIR/offgrid-hub-helper.sh"

# Fill in the template with plutil, so paths with spaces or odd characters stay valid.
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
cp "$HERE/$LABEL.plist" "$TMP"
plutil -replace ProgramArguments -array "$TMP"
i=0; for a in /bin/bash "$DIR/offgrid-hub-helper.sh" --pack "$PACK"; do plutil -insert "ProgramArguments.$i" -string "$a" "$TMP"; i=$((i+1)); done
plutil -replace StandardOutPath -string "$LOG" "$TMP"
plutil -replace StandardErrorPath -string "$LOG" "$TMP"
plutil -lint "$TMP" >/dev/null
[ "$(plutil -extract ProgramArguments.1 raw -o - "$TMP")" = "$DIR/offgrid-hub-helper.sh" ] || { echo "Could not write the helper settings." >&2; exit 1; }

# Replace an older copy cleanly, then load it.
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
cp "$TMP" "$AGENT"; chmod 644 "$AGENT"
launchctl bootstrap "gui/$(id -u)" "$AGENT"
echo "Installed. Plug in an Off-Grid hub and Off-Grid Fieldbook opens on the $PACK map."
echo "  helper: $DIR/offgrid-hub-helper.sh"
echo "  log:    $LOG"
echo "macOS may say a background item was added, and the first time a hub is plugged in it may ask"
echo "whether bash can read files on a removable volume. Allow it, or the helper can't see the hub."
