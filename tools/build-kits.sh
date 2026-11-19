#!/bin/bash
# Builds the two offline kits from downloads/.
#   Offline Kit - Mac     everything, ready to use on this Mac
#   Offline Kit - iPhone  the ~2 GB phone set
# Files are APFS clones (cp -c), so the kits take almost no extra disk space.
# Safe to rerun: each kit folder is rebuilt from scratch. Files still downloading are skipped.
set -u
OG="$(cd "$(dirname "$0")/.." && pwd)"
D="$OG/downloads"
MAC="$OG/Offline Kit - Mac"
IOS="$OG/Offline Kit - iPhone"
SKIPPED=()

BUSY=$(lsof -c curl -Fn 2>/dev/null)
busy(){ grep -qxF "n$1" <<<"$BUSY"; }
# A finished ZIM ends exactly 16 bytes after the checksum position stored at byte 72 of its header.
zim_ok(){ /usr/bin/python3 -I -c 'import os,struct,sys
f=open(sys.argv[1],"rb"); h=f.read(80)
sys.exit(0 if len(h)==80 and h[:4]==b"ZIM\x04" and struct.unpack("<Q",h[72:80])[0]+16==os.path.getsize(sys.argv[1]) else 1)' "$1"; }
put(){ # put <src file> <dest dir>
  [ -f "$1" ] || return 0
  if busy "$1"; then SKIPPED+=("$(basename "$1") (downloading)"); return 0; fi
  if [[ "$1" == *.zim ]] && ! zim_ok "$1"; then SKIPPED+=("$(basename "$1") (incomplete)"); return 0; fi
  mkdir -p "$2" && cp -c "$1" "$2/"
}
putdir(){ # putdir <src dir> <dest dir> [glob]
  [ -d "$1" ] || return 0
  for f in "$1"/${3:-*}; do [ -f "$f" ] && [ "$(basename "$f")" != .DS_Store ] && put "$f" "$2"; done
}

rm -rf "$MAC" "$IOS"

# ---------- Mac kit ----------
L="$MAC/Library (open with Kiwix)"
putdir "$D/zim/medicine"          "$L/Medicine"
putdir "$D/zim/survival"          "$L/Survival"
putdir "$D/zim/food"              "$L/Food and Gardening"
putdir "$D/zim/diy-repair"        "$L/DIY and Repair"
putdir "$D/zim/power-electronics" "$L/Power and Electronics"
putdir "$D/zim/comms"             "$L/Radio and Comms"
putdir "$D/zim/reference"         "$L/Wikipedia"
putdir "$D/zim/computing"         "$L/Coding Docs"
putdir "$D/zim/plan"              "$L/My Plan"
putdir "$D/zim/prepper"           "$L/Prepper Packs"

B="$MAC/Books (PDF)"
putdir "$D/pdf/medical"  "$B/Medical"
putdir "$D/pdf/food"     "$B/Food"
putdir "$D/pdf/survival" "$B/Survival"

M="$MAC/Maps"
mkdir -p "$M"
V="$OG/app/web/map"
cp -cR "$V/lib" "$V/fonts" "$V/sprites" "$M/"
cp -c "$V/index.html" "$V/serve.py" "$V/Open Maps.command" "$M/"
put "$D/maps/texas_2025-12.pmtiles" "$M"
[ -f "$M/texas_2025-12.pmtiles" ] && mv "$M/texas_2025-12.pmtiles" "$M/texas.pmtiles"
put "$D/maps/texas-latest.osm.pbf" "$M/Raw OSM data (for the mini PC)"

R="$MAC/For the Mini PC"
mkdir -p "$R"
for repo in "$D"/repos/*/; do cp -cR "${repo%/}" "$R/"; done

cat > "$MAC/01 Read Me First.md" <<'EOF'
# Offline Kit for the Mac

Everything here works with no internet. Built from `Off-Grid/downloads`.

## Do this now, while the internet works
1. Install **Kiwix** from the Mac App Store (free). It opens the Library files.
2. Install **Ollama** from ollama.com, then run `ollama pull qwen3:4b` in Terminal. That's your offline AI.
3. Double-click `Maps/Open Maps.command` once. If macOS blocks it, right-click it and pick Open.

## What's where
| Folder | What | How to open |
|---|---|---|
| Library (open with Kiwix) | Medical, survival, food, repair, radio, Wikipedia | Kiwix: File > Open, pick a `.zim` |
| Books (PDF) | Where There Is No Doctor, Dentist, Women's health, water and sanitation, USDA canning, Army survival manual | Preview |
| Maps | Your state, street level | Double-click `Open Maps.command`. Close the Terminal window to stop it |
| For the Mini PC | Project NOMAD, WROLPi, Offgridders code | Only for a future Linux mini PC |

## Medical first
Start with `Books (PDF)/Medical/Where There Is No Doctor`. For drug info, open `nhs.uk medicines` in Kiwix.
EOF

# ---------- iPhone kit (~2 GB) ----------
L="$IOS/Library (open with Kiwix)"
putdir "$D/zim/medicine"  "$L"
putdir "$D/zim/survival"  "$L"
putdir "$D/zim/food"      "$L" "*cooking*"
putdir "$D/zim/comms"     "$L"
putdir "$D/zim/plan"      "$L"
put "$D/zim/reference/wikipedia_en_top_mini_2026-06.zim" "$L"
putdir "$D/pdf/medical"  "$IOS/Books (PDF)"
putdir "$D/pdf/food"     "$IOS/Books (PDF)"
putdir "$D/pdf/survival" "$IOS/Books (PDF)"

cat > "$IOS/01 Read Me First.md" <<'EOF'
# Offline Kit for the iPhone

About 2 GB. Medical, survival, cooking, radio, a small Wikipedia, and the key books.

## Install these apps now, while the internet works
| App | Why | Setup |
|---|---|---|
| Kiwix | Reads the Library files | Nothing else needed |
| Organic Maps (or CoMaps) | Offline maps and directions | Open it, download **Texas** inside the app |
| Off Grid: Local AI | Offline AI chat | Download a small model inside the app |
| Meshtastic | Texting over radio, no cell service | Pair once you have a radio |

## Move this folder onto the phone
- **Cable:** plug the iPhone into the Mac, open Finder, click the iPhone, open the **Files** tab, drag this whole folder onto **Kiwix**. If Kiwix isn't in that list, use AirDrop.
- **AirDrop:** AirDrop the folder to the phone and save it to **On My iPhone**.
- Don't use iCloud Drive. It can offload files, and then they're gone when the internet is.

## Open things
- Kiwix: Library > Open, pick the `.zim` files. Your plan and checklists are the **Off-Grid Plan** book.
- Books: tap them in the Files app.
- Start with `Where There Is No Doctor` for any medical problem.
EOF

echo "Mac kit:    $(du -sh "$MAC" | cut -f1) (clones, near zero extra disk)"
echo "iPhone kit: $(du -sh "$IOS" | cut -f1)"
[ ${#SKIPPED[@]} -gt 0 ] && printf 'Skipped: %s\n' $(printf '%s\n' "${SKIPPED[@]}" | sort -u | tr ' ' '_')
exit 0
