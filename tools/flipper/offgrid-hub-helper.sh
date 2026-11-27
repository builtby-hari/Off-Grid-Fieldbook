#!/bin/bash
# Off-Grid hub helper: launchd runs this every time any drive mounts (StartOnMount).
# If a mounted drive is an Off-Grid hub (it has offgrid-hub.json), it opens Off-Grid Fieldbook on the map.
# Any other drive: it does nothing and exits.
#
# It never writes to any drive. After opening the app it stays asleep until the hub is unplugged, so other
# drives mounting meanwhile can't open the app again (launchd never runs a second copy of a running job).
# Pull the hub and plug it back in, and it opens the app again.
#
#   offgrid-hub-helper.sh [--pack texas] [--bundle com.builtbyhari.offgrid] [--dry-run]
set -u
PACK="texas"
BUNDLES="com.builtbyhari.offgrid com.builtbyhari.offgrid.share"
DRY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pack) PACK="$2"; shift 2 ;;
    --bundle) BUNDLES="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
case "$PACK" in *[!A-Za-z0-9_-]*|"") echo "bad pack name" >&2; exit 2 ;; esac
VOLUMES="${OFFGRID_VOLUMES:-/Volumes}"   # tests point this at a folder of fake drives
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*"; }

# Local drives only, read from the mount table. A dead network share can hang a file check for minutes.
local_volumes() {
  if [ "$VOLUMES" != /Volumes ]; then
    for v in "$VOLUMES"/*; do [ -d "$v" ] && echo "$v"; done
    return
  fi
  /sbin/mount | while IFS= read -r line; do
    [[ "$line" =~ \ on\ (/Volumes/[^/]+)\ \((.*)\)$ ]] || continue
    case ", ${BASH_REMATCH[2]}," in *", local,"*) echo "${BASH_REMATCH[1]}" ;; esac
  done
}

# A marker counts only if it is JSON with kind "starter" or "full".
is_marker() {
  [ -f "$1" ] || return 1
  local kind
  kind="$(/usr/bin/plutil -extract kind raw -o - "$1" 2>/dev/null)" || return 1
  [ "$kind" = starter ] || [ "$kind" = full ]
}

# Prints every hub marker on a mounted drive, one per line.
find_hubs() {
  local v
  while IFS= read -r v; do
    is_marker "$v/offgrid-hub.json" && echo "$v/offgrid-hub.json"
    is_marker "$v/OffGrid-Hub/offgrid-hub.json" && echo "$v/OffGrid-Hub/offgrid-hub.json"
  done < <(local_volumes)
}

hubs="$(find_hubs)"
if [ -z "$hubs" ]; then exit 0; fi   # not a hub: do nothing
log "hub found: $(echo "$hubs" | tr '\n' ' ')"

URL="offgrid://open?view=map&pack=$PACK"
if [ -n "$DRY" ]; then echo "would open: $URL"; exit 0; fi
opened=""
for b in $BUNDLES; do
  if /usr/bin/open -b "$b" "$URL" 2>/dev/null; then opened="$b"; break; fi
done
[ -n "$opened" ] && log "opened $opened on $URL" || log "Off-Grid Fieldbook is not installed, nothing opened"

# Sleep until every hub seen above is gone, then exit, ready for the next plug-in.
while :; do
  still=""
  while IFS= read -r m; do [ -f "$m" ] && still=1; done <<< "$hubs"
  [ -z "$still" ] && break
  sleep 5
done
log "hub unplugged"
exit 0
