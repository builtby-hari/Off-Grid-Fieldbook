#!/usr/bin/env python3
"""Off-Grid region packs: pick a state (or several), see the size, download it. Resumable.

  offgrid-pack regions                         list every region you can get
  offgrid-pack plan  oklahoma louisiana        exact sizes before downloading
  offgrid-pack get   oklahoma --to /Volumes/SSD/Off-Grid Packs
  offgrid-pack get   all-states --level lite   every state, smaller maps
  offgrid-pack list                            what's installed and where
  offgrid-pack setup                           one-time: install the OSM reader for survival layers

Levels:  lite      streets to zoom 12, terrain to zoom 10       (good for "where is it")
         standard  every street and building, terrain zoom 11  (default)
         full      every street and building, terrain zoom 12  (best hills and contour lines)

A pack folder holds pack.json, basemap.pmtiles, terrain/{z}/{x}/{y}.png and layers/*.geojson.
The Off-Grid app finds packs in every folder listed in its packs.json (this tool keeps that list).
Standard library only. Nothing downloaded is ever run.
"""
import argparse, concurrent.futures as cf, datetime as dt, json, math, os, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OG = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import pmtiles_extract as PX  # noqa: E402

UA = {"User-Agent": "OffGrid-pack-builder/1.0"}
REGIONS_FILE = os.path.join(HERE, "regions.json")
CONFIG = os.path.expanduser("~/Library/Application Support/Off-Grid/packs.json")
DEFAULT_ROOT = os.path.join(OG, "packs")
# The app runs this tool from inside its bundle, which must stay read-only. It passes these two
# so the private Python environment and the layer builder live where the app can use them.
VENV_DIR = os.environ.get("OFFGRID_VENV") or os.path.join(OG, ".venv")
VENV_PY = os.path.join(VENV_DIR, "bin", "python")
LAYERS_SCRIPT = os.environ.get("OFFGRID_LAYERS_SCRIPT") or os.path.join(OG, "tools", "build-survival-layers.py")
LEVELS = {"lite": {"basemap": 12, "terrain": 10}, "standard": {"basemap": 15, "terrain": 11}, "full": {"basemap": 15, "terrain": 12}}
OVERVIEW = {"slug": "usa-overview", "name": "USA overview (whole country, low detail)", "bbox": [-179.2, 18.9, -66.9, 71.4],
            "overview": True, "levels": {"lite": {"basemap": 6, "terrain": 6}, "standard": {"basemap": 7, "terrain": 7}, "full": {"basemap": 8, "terrain": 8}}}
TERRAIN_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def say(*a): print(*a, flush=True)
def human(n): return f"{n / 1e9:.1f} GB" if n >= 1e9 else f"{n / 1e6:.0f} MB"
def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


# ---------- regions ----------
def refresh_regions():
    say("Getting the region list from Geofabrik…")
    idx = json.loads(get("https://download.geofabrik.de/index-v1.json"))
    out = []
    for f in idx["features"]:
        p = f["properties"]
        pid = p["id"]
        if pid.startswith("us/"): pid = pid[3:]
        elif p.get("parent") != "us": continue
        if "/" in pid or not f.get("geometry"):
            continue
        iso = (p.get("iso3166-2") or [""])[0]
        name = pid.replace("-", " ").title().replace("Of ", "of ")
        xs, ys = [], []
        def walk(c):
            if isinstance(c[0], (int, float)): xs.append(c[0]); ys.append(c[1])
            else: [walk(k) for k in c]
        walk(f["geometry"]["coordinates"])
        W, E = min(xs), max(xs)
        if pid == "alaska": W, E = -179.2, -129.9
        if pid == "hawaii": W, S0, E, N0 = -160.6, 18.8, -154.6, 22.4; xs, ys = [W, E], [S0, N0]  # main islands only  # skip the bits across the date line
        out.append({"slug": pid, "name": name, "iso": iso, "bbox": [round(W, 3), round(min(ys), 3), round(E, 3), round(max(ys), 3)],
                    "osm": p["urls"]["pbf"]})
    out.sort(key=lambda r: r["name"])
    json.dump({"updated": dt.date.today().isoformat(), "source": "Geofabrik index-v1", "regions": out}, open(REGIONS_FILE, "w"), indent=1)
    say(f"Saved {len(out)} regions to {REGIONS_FILE}")
    return out


def regions():
    if not os.path.exists(REGIONS_FILE):
        refresh_regions()
    return json.load(open(REGIONS_FILE))["regions"]


def find_regions(names):
    regs = {r["slug"]: r for r in regions()}
    out = []
    for n in names:
        n = n.lower().replace(" ", "-")
        if n in ("all-states", "all"):
            out += [r for s, r in regs.items() if s not in ("puerto-rico", "us-virgin-islands")]
        elif n in ("usa-overview", "usa", "us-overview"):
            out.append(OVERVIEW)
        elif n in regs:
            out.append(regs[n])
        else:
            close = [s for s in regs if s.startswith(n[:4])]
            sys.exit(f"Don't know the region '{n}'." + (f" Did you mean: {', '.join(close)}?" if close else " Run: offgrid-pack regions"))
    return out


# ---------- where packs live ----------
def config():
    try: return json.load(open(CONFIG))
    except Exception: return {"roots": []}


def remember_root(root):
    c = config(); root = os.path.abspath(root)
    if root not in c["roots"]:
        c["roots"].append(root)
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        json.dump(c, open(CONFIG, "w"), indent=1)


def installed():
    found = {}
    for root in config()["roots"] + [DEFAULT_ROOT]:
        if not os.path.isdir(root): continue
        for slug in sorted(os.listdir(root)):
            pj = os.path.join(root, slug, "pack.json")
            if os.path.exists(pj) and slug not in found:
                found[slug] = (os.path.join(root, slug), json.load(open(pj)))
    return found


# ---------- sizes ----------
_latest = None
def latest_basemap():
    global _latest
    if _latest: return _latest
    day = dt.date.today()
    for i in range(8):
        url = f"https://build.protomaps.com/{(day - dt.timedelta(days=i)).strftime('%Y%m%d')}.pmtiles"
        try:
            urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=20)
            _latest = url; return url
        except Exception:
            continue
    sys.exit("Couldn't reach build.protomaps.com for the base map. Are you online?")


def terrain_tiles(bbox, maxz):
    W, S, E, N = bbox
    out = []
    for z in range(0, maxz + 1):
        x0, y0 = PX.lonlat_to_xy(W, N, z); x1, y1 = PX.lonlat_to_xy(E, S, z)
        out += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    return out


def basemap_bytes(bbox, maxz):
    src = PX.Source(latest_basemap()); h = PX.parse_header(src.read(0, 127))
    found = PX.collect(src, h, PX.wanted_ids(bbox, 0, min(maxz, h["maxz"])))
    return sum(ln for off, ln in {(o, l) for _, o, l in found})


def osm_bytes(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=20) as r:
            return int(r.headers.get("Content-Length", 0))
    except Exception:
        return 0


def plan_one(r, level):
    lv = (r.get("levels") or LEVELS)[level]
    b = basemap_bytes(r["bbox"], lv["basemap"])
    t = terrain_tiles(r["bbox"], lv["terrain"])
    tb = sum(97e3 if z >= 11 else 60e3 for z, _, _ in t)
    o = 0 if r.get("overview") else osm_bytes(r["osm"])
    return {"basemap": b, "terrain": int(tb), "layers": int(o * 0.06), "osm_download": o, "terrain_tiles": len(t), "zoom": lv}


def free_bytes(path):
    p = path
    while not os.path.exists(p): p = os.path.dirname(p)
    return shutil.disk_usage(p).free


# ---------- commands ----------
def cmd_regions(a):
    if a.refresh: refresh_regions()
    have = installed()
    say("Regions (use the short name):\n")
    say(f"  {'usa-overview':24} USA overview, whole country at low detail")
    for r in regions():
        say(f"  {r['slug']:24} {r['name']}{'   ✓ installed' if r['slug'] in have else ''}")
    say("\nAlso: all-states (every state). Next: offgrid-pack plan <name>")


def cmd_plan(a):
    regs = find_regions(a.regions); to = os.path.abspath(a.to)
    if getattr(a, "json", False):   # for the app's setup screen
        rows, tot = [], 0
        for r in regs:
            p = plan_one(r, a.level); t = p["basemap"] + p["terrain"] + p["layers"]; tot += t
            rows.append({"slug": r["slug"], "name": r["name"], "basemap": p["basemap"], "terrain": p["terrain"], "layers": p["layers"], "total": t, "osm_download": p["osm_download"]})
        fb = free_bytes(to)
        print(json.dumps({"level": a.level, "regions": rows, "total": tot, "free": fb, "ok": fb > tot * 1.1 + 2e9, "to": to}), flush=True)
        return
    say(f"Level: {a.level}.  Base map: {os.path.basename(latest_basemap())} (Protomaps, OpenStreetMap data)\n")
    say(f"  {'region':22} {'base map':>10} {'terrain':>10} {'layers':>9} {'total':>10}   one-time OSM download")
    tot = 0
    for r in regs:
        p = plan_one(r, a.level); t = p["basemap"] + p["terrain"] + p["layers"]; tot += t
        say(f"  {r['slug']:22} {human(p['basemap']):>10} {human(p['terrain']):>10} {human(p['layers']):>9} {human(t):>10}   {human(p['osm_download']) if p['osm_download'] else '-'} (deleted after)")
    fb = free_bytes(to)
    say(f"\n  Total about {human(tot)}. Free at {to}: {human(fb)}.  {'OK ✓' if fb > tot * 1.1 + 2e9 else 'NOT ENOUGH SPACE ✕'}")
    say(f"\nTo get it: offgrid-pack get {' '.join(a.regions)} --level {a.level} --to \"{to}\"")


def fetch_terrain(dirn, bbox, maxz, log):
    jobs = terrain_tiles(bbox, maxz)
    def one(j):
        z, x, y = j; p = f"{dirn}/{z}/{x}/{y}.png"
        if os.path.exists(p) and os.path.getsize(p) > 0: return 0
        os.makedirs(os.path.dirname(p), exist_ok=True)
        for i in range(5):
            try:
                d = get(TERRAIN_URL.format(z=z, x=x, y=y), 30)
                if d[:8] != b"\x89PNG\r\n\x1a\n": raise ValueError("not a png")
                open(p + ".part", "wb").write(d); os.replace(p + ".part", p); return len(d)
            except Exception as e:
                err = e; time.sleep(1 + i)
        log(f"    tile {j} failed: {err}"); return -1
    n = bad = 0; step = max(1, len(jobs) // 10)
    with cf.ThreadPoolExecutor(12) as ex:
        for i, r in enumerate(ex.map(one, jobs), 1):
            bad += r < 0
            if i % step == 0: log(f"    terrain {i * 100 // len(jobs)}%  ({i:,} of {len(jobs):,} tiles)")
    return len(jobs), bad


def build_layers(r, pdir, log, keep_osm):
    if not os.path.exists(VENV_PY) or subprocess.run([VENV_PY, "-I", "-c", "import osmium"], capture_output=True).returncode:
        log("    survival layers were skipped: the map layer builder is not set up. In the app, download again with survival layers ticked. In Terminal, run: offgrid-pack setup")
        return None
    src = os.path.join(pdir, "_osm"); os.makedirs(src, exist_ok=True)
    pbf = os.path.join(src, os.path.basename(r["osm"]))
    if not os.path.exists(pbf):
        log(f"    downloading OpenStreetMap data ({human(osm_bytes(r['osm']))})…")
        with urllib.request.urlopen(urllib.request.Request(r["osm"], headers=UA), timeout=120) as resp, open(pbf + ".part", "wb") as f:
            shutil.copyfileobj(resp, f, 8 << 20)
        os.replace(pbf + ".part", pbf)
    log("    building survival layers (water, food, shelter, medical, power…)")
    out = os.path.join(pdir, "layers")
    res = subprocess.run([VENV_PY, "-I", LAYERS_SCRIPT, "--pbf", pbf, "--out", out])
    if res.returncode: log("    layer build failed; re-run get to retry"); return None
    if not keep_osm: shutil.rmtree(src, ignore_errors=True)
    idx = json.load(open(os.path.join(out, "index.json")))
    return {"count": sum(o.get("count", 0) for o in idx), "layers": len(idx)}


def cmd_get(a):
    regs = find_regions(a.regions); to = os.path.abspath(a.to)
    parts = set(a.parts.split(","))
    os.makedirs(to, exist_ok=True); remember_root(to)
    say(f"Saving to {to} (the app will find it there).")
    for r in regs:
        lv = (r.get("levels") or LEVELS)[a.level]
        pdir = os.path.join(to, r["slug"]); os.makedirs(pdir, exist_ok=True)
        pj = os.path.join(pdir, "pack.json")
        pack = json.load(open(pj)) if os.path.exists(pj) else {"slug": r["slug"], "name": r["name"], "bbox": r["bbox"], "parts": {}}
        pack.update(level=a.level, bbox=r["bbox"])
        save = lambda: json.dump(pack, open(pj, "w"), indent=1)
        say(f"\n== {r['name']} ({a.level}) ==")
        bm = pack["parts"].get("basemap")
        if "basemap" in parts and not (bm and bm.get("maxzoom", 0) >= lv["basemap"] and os.path.exists(os.path.join(pdir, "basemap.pmtiles"))):
            say("  base map (streets, places, water, land use)")
            res = PX.extract(latest_basemap(), os.path.join(pdir, "basemap.pmtiles"), r["bbox"], lv["basemap"], log=say)
            pack["parts"]["basemap"] = {"file": "basemap.pmtiles", "maxzoom": res["maxzoom"], "bytes": res["bytes"],
                                        "source": latest_basemap(), "date": dt.date.today().isoformat(), "license": "ODbL (OpenStreetMap contributors), Protomaps"}
            save()
        elif "basemap" in parts: say("  base map ✓ already here")
        tm = pack["parts"].get("terrain")
        if "terrain" in parts and not (tm and tm.get("maxzoom", 0) >= lv["terrain"] and not tm.get("failed")):
            say(f"  terrain (hills and contour lines, zoom {lv['terrain']})")
            n, bad = fetch_terrain(os.path.join(pdir, "terrain"), r["bbox"], lv["terrain"], say)
            pack["parts"]["terrain"] = {"dir": "terrain", "maxzoom": lv["terrain"], "tiles": n, "failed": bad, "encoding": "terrarium",
                                        "date": dt.date.today().isoformat(), "source": "AWS Terrain Tiles (USGS and others)"}
            save()
            if bad: say(f"  {bad} terrain tiles failed; run the same command again to retry them")
        elif "terrain" in parts: say("  terrain ✓ already here")
        if "layers" in parts and not r.get("overview") and not pack["parts"].get("layers"):
            say("  survival layers")
            res = build_layers(r, pdir, say, a.keep_osm)
            if res:
                pack["parts"]["layers"] = {"dir": "layers", **res, "date": dt.date.today().isoformat(), "source": "OpenStreetMap (ODbL)"}
                save()
        elif "layers" in parts and pack["parts"].get("layers"): say("  survival layers ✓ already here")
        pack["updated"] = dt.datetime.now().isoformat(timespec="seconds"); save()
        size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(pdir) for f in fs)
        say(f"  done: {human(size)} in {pdir}")
    say("\nDone. Open the Map and pick this region under Map file.")


def cmd_list(a):
    have = installed()
    if not have: return say("No region packs yet. Try: offgrid-pack plan oklahoma")
    for slug, (path, p) in have.items():
        size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(path) for f in fs)
        parts = ", ".join(k for k in ("basemap", "terrain", "layers") if k in p.get("parts", {}))
        say(f"  {slug:22} {p.get('level', ''):9} {human(size):>8}  {parts:28} {path}")


def cmd_setup(a):
    if not os.path.exists(VENV_PY):
        say("Making a private Python environment for the map layer builder …")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    subprocess.run([VENV_PY, "-m", "pip", "install", "--quiet", "osmium"], check=True)
    say("Ready. Survival layers can be built now.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="offgrid-pack", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("regions"); p.add_argument("--refresh", action="store_true"); p.set_defaults(f=cmd_regions)
    for name, f in (("plan", cmd_plan), ("get", cmd_get)):
        p = sp.add_parser(name); p.add_argument("regions", nargs="+")
        p.add_argument("--level", choices=list(LEVELS), default="standard")
        p.add_argument("--to", default=(config()["roots"] or [DEFAULT_ROOT])[-1], help="folder for the packs (an external drive works)")
        if name == "plan": p.add_argument("--json", action="store_true", help="print the sizes as JSON")
        if name == "get":
            p.add_argument("--parts", default="basemap,terrain,layers")
            p.add_argument("--keep-osm", action="store_true", help="keep the raw OSM file (needed later for offline routing)")
        p.set_defaults(f=f)
    sp.add_parser("list").set_defaults(f=cmd_list)
    sp.add_parser("setup").set_defaults(f=cmd_setup)
    a = ap.parse_args(); a.f(a)
