#!/bin/bash
# Builds the Off-Grid Mac app.
#   ./build-app.sh            personal: everything, including your own plan pages
#   ./build-app.sh share      everything except the personal plan (safe to give people)
#   ./build-app.sh share-lite small version to send: core medical/survival library + books + map, no plan
# Content files are APFS clones, so the app costs almost no extra disk on this Mac.
set -euo pipefail
EDITION="${1:-personal}"
OG="$(cd "$(dirname "$0")/.." && pwd)"   # the project folder, wherever it is cloned
APP_SRC="$OG/app"
BUILD="$APP_SRC/build"
OUT="$OG/Apps"
KIWIX="$OG/vendor-dl/kiwix-tools/kiwix-serve-universal"

case "$EDITION" in
  personal)   NAME="Off-Grid Fieldbook";            KIT="$OG/Offline Kit - Mac";    PLAN=yes ;;
  share)      NAME="Off-Grid Fieldbook (share)";    KIT="$OG/Offline Kit - Mac";    PLAN=no ;;
  share-lite) NAME="Off-Grid Fieldbook Lite";       KIT="$OG/Offline Kit - iPhone"; PLAN=no ;;
  *) echo "usage: $0 [personal|share|share-lite]"; exit 1 ;;
esac

# The kits are folders of library files and maps you downloaded. A fresh clone has none, and that is fine.
if [ -d "$OG/downloads" ]; then echo "Refreshing kits..."; "$OG/tools/build-kits.sh" >/dev/null; fi

echo "Compiling..."
mkdir -p "$BUILD"
# Rebuild when any Swift file is newer than the last build.
if [ ! -f "$BUILD/OffGrid" ] || [ -n "$(find "$APP_SRC/macos" -maxdepth 1 -name '*.swift' -newer "$BUILD/OffGrid")" ]; then
  for a in arm64 x86_64; do
    swiftc -O -target $a-apple-macos13.0 "$APP_SRC/macos/"*.swift -o "$BUILD/OffGrid-$a"
  done
  lipo -create "$BUILD/OffGrid-arm64" "$BUILD/OffGrid-x86_64" -output "$BUILD/OffGrid"
fi
if [ ! -f "$BUILD/AppIcon.icns" ]; then
  swiftc -O "$APP_SRC/macos/icon/make-icon.swift" -o "$BUILD/make-icon"
  "$BUILD/make-icon" "$BUILD/icon-1024.png"
  IS="$BUILD/AppIcon.iconset"; mkdir -p "$IS"
  for s in 16 32 128 256 512; do
    sips -z $s $s "$BUILD/icon-1024.png" --out "$IS/icon_${s}x${s}.png" >/dev/null
    sips -z $((s*2)) $((s*2)) "$BUILD/icon-1024.png" --out "$IS/icon_${s}x${s}@2x.png" >/dev/null
  done
  iconutil -c icns "$IS" -o "$BUILD/AppIcon.icns"
fi

echo "Packing $NAME.app..."
APP="$OUT/$NAME.app"
rm -rf "$APP"
C="$APP/Contents"; R="$C/Resources/Content"
mkdir -p "$C/MacOS" "$R/hub" "$R/maps" "$R/library" "$R/books" "$R/docs"
cp "$APP_SRC/macos/Info.plist" "$C/"
if [ "$EDITION" != personal ]; then
  plutil -replace CFBundleIdentifier -string "com.builtbyhari.offgrid.$EDITION" "$C/Info.plist"
  plutil -replace CFBundleName -string "$NAME" "$C/Info.plist"
  plutil -replace CFBundleDisplayName -string "$NAME" "$C/Info.plist"
fi
cp "$BUILD/OffGrid" "$C/MacOS/OffGrid"
# The map pack tool, so the Setup screen can download a state without Terminal.
mkdir -p "$C/Resources/Tools"
cp "$OG/tools/packs/offgrid-pack.py" "$OG/tools/packs/pmtiles_extract.py" "$OG/tools/packs/regions.json" "$OG/tools/build-survival-layers.py" "$C/Resources/Tools/"
# The drawn icon in app/macos/icon wins over the generated placeholder.
if [ -f "$APP_SRC/macos/icon/AppIcon.icns" ]; then cp "$APP_SRC/macos/icon/AppIcon.icns" "$C/Resources/AppIcon.icns"; else cp "$BUILD/AppIcon.icns" "$C/Resources/"; fi
[ -f "$KIWIX" ] && cp "$KIWIX" "$C/MacOS/kiwix-serve" && chmod +x "$C/MacOS/kiwix-serve"
# Screens and shared code. The old emergency, visual and shelf pages are replaced by now, guides and learn.
cp "$APP_SRC/web/"{index,home,learn,place,plants,guides,setup,check}.html "$APP_SRC/web/"{og,ui,md}.js "$APP_SRC/web/ui.css" "$R/hub/"
mkdir -p "$R/hub/data" && cp "$APP_SRC/web/data/"*.json "$R/hub/data/"
cp "$OG/tools/packs/regions.json" "$R/hub/data/regions.json"   # the state list for the Setup screen

# Maps: the viewer plus the map files
V="$OG/app/web/map"
cp -cR "$V/lib" "$V/fonts" "$V/sprites" "$R/maps/"
cp "$V/index.html" "$R/maps/"
# Built-in map files are your own downloads. A copy for someone else carries no map data:
# they pick their own state on the Get maps screen.
if [ "$PLAN" = yes ]; then
for f in "$OG/Offline Kit - Mac/Maps/"*.pmtiles; do [ -f "$f" ] && cp -c "$f" "$R/maps/"; done
# Survival layers (GeoJSON overlays built from OpenStreetMap)
if [ -f "$OG/downloads/maps/overlays/index.json" ]; then
  mkdir -p "$R/maps/overlays"
  cp -c "$OG/downloads/maps/overlays/"*.json "$OG/downloads/maps/overlays/"*.geojson "$R/maps/overlays/" 2>/dev/null || true
fi

# Terrain (elevation tiles for hill shading and elevation lines)
[ -d "$OG/downloads/maps/terrain" ] && cp -cR "$OG/downloads/maps/terrain" "$R/maps/"
fi
cp "$V/lib/maplibre-contour.min.js" "$R/maps/lib/" 2>/dev/null || true

# Library and books from the kit
LIB="$KIT/Library (open with Kiwix)"
[ -d "$LIB" ] && find "$LIB" -name '*.zim' -exec cp -c {} "$R/library/" \;
if [ "$PLAN" = no ]; then rm -f "$R/library/"offgrid-plan*.zim "$R/library/"zimgit-*.zim; fi   # mixed-rights packs: personal only   # personal plan never goes in share editions
if [ -d "$KIT/Books (PDF)" ]; then
  ( cd "$KIT/Books (PDF)" && find . -name '*.pdf' | while read -r f; do
      d="$R/books/$(dirname "$f")"; [ "$(dirname "$f")" = "." ] && d="$R/books/Books"
      mkdir -p "$d"; cp -c "$f" "$d/"; done )
fi
# The Shelf: manuals, hazard sheets, old trade books (PDFs), plus the Appropedia wiki
SH="$R/shelf"; mkdir -p "$SH"
for d in "$OG/downloads/extra/library/"*/ "$OG/downloads/extra/research/canning" "$OG/downloads/extra/research/agrilife" "$OG/downloads/extra/research/ready"; do
  [ -d "$d" ] || continue; n=$(basename "$d"); mkdir -p "$SH/$n"; cp -c "$d"/*.pdf "$SH/$n/" 2>/dev/null || true
done
for z in "$OG/downloads/zim/library-extra/"*.zim; do [ -f "$z" ] && cp -c "$z" "$R/library/"; done
if [ "$PLAN" = no ]; then   # unclear or personal-use-only terms stay out of copies sent to others
  rm -rf "$SH/hesperian-water-sanitation" "$SH/texas-rainwater-manual" "$SH/agrilife"
fi

# Learn: manuals converted to Markdown, the library catalog and the search index.
# Share editions list and carry only items whose license allows sharing.
LEARN="$R/learn"; mkdir -p "$LEARN"
# The search index reads every PDF page with a small tool. Build it the first time.
[ -x "$OG/tools/library/pdf_text" ] || swiftc -O "$OG/tools/library/pdf_text.swift" -o "$OG/tools/library/pdf_text"
if [ "$PLAN" = no ]; then python3 -I "$OG/tools/library/build_index.py" --share --out "$LEARN" >/dev/null
else python3 -I "$OG/tools/library/build_index.py" --out "$LEARN" >/dev/null; fi
python3 -I - "$LEARN/catalog.json" <<'PY' | while read -r slug; do
import json, sys
for e in json.load(open(sys.argv[1])):
    if e.get("md"): print(e["slug"])
PY
  mkdir -p "$LEARN/$slug"; cp "$OG/content/library/$slug/index.md" "$LEARN/$slug/"
  [ -d "$OG/content/library/$slug/img" ] && cp -cR "$OG/content/library/$slug/img" "$LEARN/$slug/"
done

# Share rule: a copy for someone else is built from one approved list, then checked against it.
# Approved PDFs are the catalog entries marked shareable. Approved wiki collections are listed in
# content/library/share-zims.txt. Anything else is removed, and the build fails if a stray file is left.
if [ "$PLAN" = no ]; then
  python3 -I - "$R" "$LEARN/catalog.json" "$OG/content/library/share-zims.txt" <<'PY'
import json, os, sys
root, catalog, zim_list = sys.argv[1:4]
ok_pdf = {e["pdf"] for e in json.load(open(catalog)) if e.get("share") is True and e.get("pdf")}
ok_zim = {l.strip() for l in open(zim_list) if l.strip() and not l.startswith("#")} if os.path.exists(zim_list) else set()
removed = 0
def allowed(rel, name):
    low = name.lower()
    if low.endswith(".pdf"): return rel in ok_pdf
    if low.endswith(".zim"): return name in ok_zim
    return True
for pass_no in (1, 2):                      # pass 1 removes, pass 2 proves nothing is left
    for d, _, files in os.walk(root):
        for f in files:
            full = os.path.join(d, f); rel = "/" + os.path.relpath(full, root).replace(os.sep, "/")
            if allowed(rel, f): continue
            if pass_no == 1: os.remove(full); removed += 1
            else: sys.exit("share build stopped: a file that is not on the approved list is in the bundle: " + rel)
for sub in ("plants", "docs"):               # personal-use plant data and plan pages never ship
    for d, _, files in os.walk(os.path.join(root, sub)):
        if files: sys.exit("share build stopped: personal content found in " + sub)
print("  share check passed: %d files not on the approved list were left out" % removed)
PY
  find "$R/shelf" "$R/books" -type d -empty -delete 2>/dev/null || true; mkdir -p "$R/books"
fi

# Your own plan pages (personal edition only)
if [ "$PLAN" = yes ]; then
  # PFAF plant data: personal use only under its license
  [ -f "$OG/downloads/extra/plants/plants.json" ] && mkdir -p "$R/plants" && cp -c "$OG/downloads/extra/plants/plants.json" "$R/plants/"
  [ -f "$OG/90-day-outage-plan.html" ] && cp "$OG/90-day-outage-plan.html" "$R/docs/00-90 Day Outage Plan.html"
  for f in "$OG/plans/"*.md; do [ -f "$f" ] && cp "$f" "$R/docs/"; done
fi

codesign --force -s - "$C/MacOS/kiwix-serve" 2>/dev/null || true
codesign --force -s - "$C/MacOS/OffGrid"
xattr -cr "$APP" 2>/dev/null || true

echo "Done: $APP"
echo "  library: $(ls "$R/library" | wc -l | tr -d ' ') collections, books: $(find "$R/books" -name '*.pdf' | wc -l | tr -d ' '), maps: $(ls "$R/maps"/*.pmtiles 2>/dev/null | wc -l | tr -d ' '), plan pages: $(ls "$R/docs" | wc -l | tr -d ' ')"
echo "  size if sent to someone: $(du -sh "$APP" | cut -f1)"
