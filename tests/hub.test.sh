#!/bin/bash
# Hub drives and launch links, tested against the real server code.
# Builds the app into a temp folder, fakes drives with OFFGRID_VOLUMES (no real drive is touched),
# runs the server on a free port (never 47321), and checks what the page would see.
#   bash tests/hub.test.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"; PID=""
cleanup() { [ -n "$PID" ] && { kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null; }; rm -rf "$T"; }
trap cleanup EXIT
fails=0
ok() { if [ "$1" = "$2" ]; then echo "PASS $3"; else echo "FAIL $3 (got '$1', want '$2')"; fails=$((fails+1)); fi; }
json() { python3 -I -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

echo "Compiling..."
swiftc -target "$(uname -m)-apple-macos13.0" "$ROOT"/app/macos/*.swift -o "$T/OffGrid" || { echo "FAIL compile"; exit 1; }

# Launch links: compile the launch code with a tiny test entry point instead of the app's main.swift.
mkdir -p "$T/lt"
cat > "$T/lt/main.swift" <<'SWIFT'
import Foundation
func p(_ s: String?) { print(s ?? "nil") }
p(launchRoute(url: URL(string: "offgrid://open?view=map&pack=texas")!))
p(launchRoute(url: URL(string: "offgrid://map?pack=texas")!))
p(launchRoute(url: URL(string: "OFFGRID://open")!))
p(launchRoute(url: URL(string: "offgrid://open?view=evil")!))
p(launchRoute(url: URL(string: "offgrid://map?pack=../../etc")!))
p(launchRoute(url: URL(string: "https://example.com/map?pack=texas")!))
p(launchRouteFromArgs(["OffGrid", "--open", "map", "--pack", "texas"]))
p(launchRouteFromArgs(["OffGrid", "--open", "learn"]))
p(launchRouteFromArgs(["OffGrid", "--pack", "texas"]))
SWIFT
swiftc -target "$(uname -m)-apple-macos13.0" $(ls "$ROOT"/app/macos/*.swift | grep -v '/main.swift$') "$T/lt/main.swift" -o "$T/lt/run" || { echo "FAIL compile launch test"; exit 1; }
got="$("$T/lt/run" | tr '\n' ' ')"
ok "$got" "map?pack=texas map?pack=texas home nil nil nil map?pack=texas learn nil " "launch links and --open/--pack become shell addresses, bad ones are dropped"

# Fake drives
V="$T/Volumes"; L="$T/local"
mk() { mkdir -p "$1"; printf '%s' "$2" > "$1/pack.json"; }
mkdir -p "$V/OFFGRID" "$V/FlipperZero/OffGrid-Hub" "$V/NotAHub/packs" "$V/BadMarker" "$V/Macintosh HD"
echo '{"name":"Starter","kind":"starter","version":1,"built":"2026-11-27"}' > "$V/OFFGRID/offgrid-hub.json"
echo '{"name":"Flipper full hub","kind":"full","version":1}' > "$V/FlipperZero/OffGrid-Hub/offgrid-hub.json"
echo '{"name":"x","kind":"evil"}' > "$V/BadMarker/offgrid-hub.json"
mk "$V/OFFGRID/packs/zz-hubtest" '{"slug":"zz-hubtest","name":"Texas starter"}'
mk "$V/FlipperZero/OffGrid-Hub/packs/zz-hubtest" '{"slug":"zz-hubtest","name":"Texas full"}'
mk "$V/NotAHub/packs/zz-hubtest" '{"slug":"zz-hubtest","name":"Texas no marker"}'
mk "$V/BadMarker/packs/zz-hubtest" '{"slug":"zz-hubtest","name":"Texas bad marker"}'
mkdir -p "$V/BadMarker/packs"
mk "$L/zz-hubtest" '{"slug":"zz-hubtest","name":"Texas local"}'
mk "$L/zz-local-only" '{"slug":"zz-local-only","name":"Local only"}'
printf 'full-hub-bytes' > "$V/FlipperZero/OffGrid-Hub/packs/zz-hubtest/basemap.pmtiles"
printf 'local-bytes!' > "$L/zz-hubtest/basemap.pmtiles"
mkdir -p "$T/content/hub" "$T/data"; echo '<p>shell</p>' > "$T/content/hub/index.html"

OFFGRID_PORT=0 OFFGRID_VOLUMES="$V" OFFGRID_PACKS="$L" OFFGRID_DATA="$T/data" OFFGRID_CONTENT="$T/content" OFFGRID_NO_KIWIX=1 \
  "$T/OffGrid" --serve-only > "$T/url.txt" 2>"$T/err.txt" & PID=$!
for _ in $(seq 50); do [ -s "$T/url.txt" ] && break; sleep 0.1; done
U="$(head -1 "$T/url.txt")"; U="${U%/}"
[ -n "$U" ] || { echo "FAIL server did not start"; cat "$T/err.txt"; exit 1; }
port="${U##*:}"; [ "$port" != 47321 ] && echo "PASS server on a free port ($port), not 47321" || { echo "FAIL used 47321"; fails=$((fails+1)); }

hub="$(curl -s -m 10 "$U/api/hub")"
ok "$(echo "$hub" | json "[h['id']+':'+h['kind'] for h in d['hubs']]")" "['FlipperZero/OffGrid-Hub:full', 'OFFGRID:starter']" "only drives with a valid marker count, full hub listed first"
ok "$(echo "$hub" | json "d['hubs'][1].get('built')")" "2026-11-27" "marker extras come through"
ok "$(echo "$hub" | json "[(p['origin'],p.get('hub'),p.get('also')) for p in d['packs'] if p['slug']=='zz-hubtest'][0]")" "('hub', 'FlipperZero/OffGrid-Hub', ['OFFGRID', 'local'])" "the pack comes from the full hub, starter and local copies listed as backups"
packs="$(curl -s -m 10 "$U/api/packs")"
ok "$(echo "$packs" | json "[(p['name'],p['origin']) for p in d if p['slug'] in ('zz-hubtest','zz-local-only')]")" "[('Texas full', 'hub'), ('Local only', 'local')]" "/api/packs carries origin"
ok "$(curl -s -m 10 "$U/packs/zz-hubtest/basemap.pmtiles")" "full-hub-bytes" "pack file served from the hub while plugged in"
etag1="$(curl -sI -m 10 "$U/packs/zz-hubtest/basemap.pmtiles" | tr -d '\r' | awk -F': ' 'tolower($1)=="etag"{print $2}')"
[ -n "$etag1" ] && echo "PASS pack files carry an ETag" || { echo "FAIL no ETag"; fails=$((fails+1)); }
ok "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "$U/packs/zz-hubtest/..%2F..%2F..%2FOFFGRID%2Foffgrid-hub.json")" "404" "path escape out of a hub pack is refused"
ok "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "$U/packs/zz-hubtest/../../offgrid-hub.json")" "404" "dot-dot escape is refused"

# Pull the full hub: the starter takes over, then pull that too: the Mac's own copy takes over.
mv "$V/FlipperZero" "$T/pulled-full"
ok "$(curl -s -m 10 "$U/api/hub" | json "[h['id'] for h in d['hubs']]")" "['OFFGRID']" "pulled hub disappears at once"
ok "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "$U/packs/zz-hubtest/basemap.pmtiles")" "404" "starter pack has no basemap here, so 404 (no stale bytes)"
mv "$V/OFFGRID" "$T/pulled-starter"
ok "$(curl -s -m 10 "$U/packs/zz-hubtest/basemap.pmtiles")" "local-bytes!" "with no hub, the local pack is served"
etag2="$(curl -sI -m 10 "$U/packs/zz-hubtest/basemap.pmtiles" | tr -d '\r' | awk -F': ' 'tolower($1)=="etag"{print $2}')"
[ "$etag1" != "$etag2" ] && echo "PASS ETag changes when the file behind a pack changes" || { echo "FAIL ETag did not change"; fails=$((fails+1)); }
ok "$(curl -s -m 10 "$U/api/hub" | json "(d['hubs'], [p['origin'] for p in d['packs'] if p['slug']=='zz-hubtest'])")" "([], ['local'])" "no hubs, the pack is local"
kill -0 "$PID" 2>/dev/null && echo "PASS server still running" || { echo "FAIL server died"; fails=$((fails+1)); }

# The auto-open helper (dry run: it says what it would open, opens nothing).
H="$ROOT/tools/flipper/offgrid-hub-helper.sh"
ok "$(OFFGRID_VOLUMES="$V" bash "$H" --dry-run)" "" "helper does nothing when only non-hub drives are mounted"
mv "$T/pulled-full" "$V/FlipperZero"
ok "$(OFFGRID_VOLUMES="$V" bash "$H" --dry-run | tail -1)" "would open: offgrid://open?view=map&pack=texas" "helper reacts to a full hub on a card"
ok "$(OFFGRID_VOLUMES="$V" bash "$H" --dry-run --pack ohio | tail -1)" "would open: offgrid://open?view=map&pack=ohio" "helper takes another pack"
ok "$(OFFGRID_VOLUMES="$V" bash "$H" --dry-run --pack 'a;b' 2>&1)" "bad pack name" "helper refuses odd pack names"
# Not a dry run, with a bundle id that does not exist: it opens nothing, then waits until the hub is pulled.
OFFGRID_VOLUMES="$V" bash "$H" --bundle com.example.not-installed > "$T/helper.log" 2>&1 & HP=$!
sleep 1; kill -0 "$HP" 2>/dev/null && echo "PASS helper waits while the hub stays plugged in" || { echo "FAIL helper exited early"; fails=$((fails+1)); }
mv "$V/FlipperZero" "$T/pulled-full"
for _ in $(seq 20); do kill -0 "$HP" 2>/dev/null || break; sleep 0.5; done
kill -0 "$HP" 2>/dev/null && { echo "FAIL helper still waiting after the hub was pulled"; kill "$HP"; fails=$((fails+1)); } || echo "PASS helper exits once the hub is pulled"
grep -q "not installed" "$T/helper.log" && echo "PASS helper logs a missing app instead of failing" || { echo "FAIL helper log"; cat "$T/helper.log"; fails=$((fails+1)); }

echo; [ "$fails" = 0 ] && echo "All hub tests passed." || { echo "$fails failed."; exit 1; }
