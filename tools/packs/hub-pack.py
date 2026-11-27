"""Assemble a hub pack: a region folder where every big part is one file, ready to copy to a drive.

  python3 -I hub-pack.py SOURCE_PACK OUT_DIR             build or update OUT_DIR, then check it
  python3 -I hub-pack.py --check OUT_DIR                 check a hub pack and write checksums.txt

SOURCE_PACK is a normal region pack (pack.json, basemap.pmtiles, terrain/, layers/).
What it does, safe to run again at any time:
  - terrain: loose terrain/z/x/y.png tiles are packed into terrain.pmtiles (lossless WebP when
    the cwebp tool is installed, else PNG). A terrain.pmtiles that already holds the same tiles
    is kept as it is.
  - basemap.pmtiles and layers/ are cloned (APFS copy-on-write, no extra disk space). If the
    two folders are on different drives a normal copy is made, unless --clone-only is given.
  - satellite.pmtiles is picked up if it is already in OUT_DIR and finished. While sat-pack is
    still downloading its header is all zeros, so it is skipped with a message; run this again
    when the download is done.
  - pack.json is written with real byte and tile counts read from the files.

--check makes sure every part file is there, every PMTiles header and directory reads,
the counts match pack.json, and writes sha256 sums to checksums.txt (format of `shasum -a 256`,
so `shasum -a 256 -c checksums.txt` works inside the folder).
Standard library only.
"""
import argparse, datetime as dt, hashlib, importlib.util, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pmtiles_extract as PX  # noqa: E402

TYPES = {1: "mvt", 2: "png", 3: "jpg", 4: "webp", 5: "avif"}
SAT_ATTRIBUTION = "USGS The National Map: Imagery"


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def say(*a): print(*a, flush=True)
def human(n): return f"{n / 1e9:.2f} GB" if n >= 1e9 else f"{n / 1e6:.1f} MB"
def free(path): return shutil.disk_usage(path).free


# ---------- reading PMTiles ----------
def header_state(path):
    """'missing', 'zeros' (sat-pack still writing), 'invalid' or 'valid'."""
    if not os.path.exists(path): return "missing"
    with open(path, "rb") as f: b = f.read(127)
    if len(b) < 127 or not any(b): return "zeros"
    try:
        PX.parse_header(b); return "valid"
    except ValueError:
        return "invalid"


def inspect(path):
    """Read the header, metadata and every directory. Returns a dict with the header fields plus
    file_size, ids (sorted tile ids), addressed (tiles counting runs), metadata, problems."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        h = PX.parse_header(f.read(127))
        probs = []
        for name, off, ln in (("root directory", h["root_off"], h["root_len"]), ("metadata", h["meta_off"], h["meta_len"]),
                              ("leaf directories", h["leaf_off"], h["leaf_len"]), ("tile data", h["data_off"], h["data_len"])):
            if off + ln > size: probs.append(f"{name} runs past the end of the file ({off}+{ln} > {size})")
        if h["root_off"] + h["root_len"] > 16384: probs.append("root directory is not inside the first 16 KB")
        h["file_size"], h["problems"] = size, probs
        h["end"] = max(h["root_off"] + h["root_len"], h["meta_off"] + h["meta_len"], h["leaf_off"] + h["leaf_len"], h["data_off"] + h["data_len"])
        if probs: return h
        f.seek(h["meta_off"])
        try: h["metadata"] = json.loads(PX.decompress(f.read(h["meta_len"]), h["icomp"]) or b"{}")
        except Exception as e: h["metadata"] = {}; probs.append(f"metadata does not read: {e}")
        ids, addressed, entries = [], 0, 0
        def walk(raw, depth):
            nonlocal addressed, entries
            if depth > 3: raise ValueError("directories nested too deep")
            for tid, off, ln, run in PX.parse_dir(PX.decompress(raw, h["icomp"])):
                if run == 0:
                    if off + ln > h["leaf_len"]: raise ValueError(f"leaf directory at {off}+{ln} is outside the leaf section")
                    f.seek(h["leaf_off"] + off); walk(f.read(ln), depth + 1)
                else:
                    if off + ln > h["data_len"]: raise ValueError(f"tile {tid} at {off}+{ln} is outside the tile data")
                    ids.append(tid); addressed += run; entries += 1
        try:
            f.seek(h["root_off"]); walk(f.read(h["root_len"]), 0)
        except Exception as e:
            probs.append(f"directories do not read: {e}")
        h["ids"], h["addressed_walked"], h["entries_walked"] = ids, addressed, entries
        if not probs:
            if addressed != h["addressed"]: probs.append(f"header says {h['addressed']} tiles, directories hold {addressed}")
            if ids != sorted(ids): probs.append("directory entries are not in tile id order")
    return h


# ---------- copying ----------
def same_file(a, b):
    """Cheap sameness test for re-runs: same size and same first and last MB."""
    if not (os.path.exists(a) and os.path.exists(b)): return False
    n = os.path.getsize(a)
    if n != os.path.getsize(b): return False
    with open(a, "rb") as fa, open(b, "rb") as fb:
        if fa.read(1 << 20) != fb.read(1 << 20): return False
        fa.seek(max(0, n - (1 << 20))); fb.seek(max(0, n - (1 << 20)))
        return fa.read() == fb.read()


def clone(src, dst, clone_only=False, log=say):
    """APFS clone (cp -c) if possible, else a normal copy. Writes to .part then renames."""
    tmp = dst + ".part"
    if os.path.exists(tmp): os.remove(tmp)
    r = subprocess.run(["cp", "-c", src, tmp], capture_output=True)
    if r.returncode == 0 and os.path.getsize(tmp) == os.path.getsize(src):
        os.replace(tmp, dst); return "cloned"
    if os.path.exists(tmp): os.remove(tmp)
    if clone_only:
        raise SystemExit(f"could not clone {os.path.basename(src)} (different drive?) and --clone-only is set: "
                         f"{r.stderr.decode(errors='replace').strip()}")
    need = os.path.getsize(src)
    if free(os.path.dirname(dst)) < need + (512 << 20):
        raise SystemExit(f"not enough free space to copy {os.path.basename(src)} ({human(need)})")
    shutil.copyfile(src, tmp); os.replace(tmp, dst)
    return "copied"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            c = f.read(8 << 20)
            if not c: break
            h.update(c)
    return h.hexdigest()


def write_json(path, obj):
    tmp = path + ".part"
    with open(tmp, "w") as f: json.dump(obj, f, indent=1); f.write("\n")
    os.replace(tmp, path)


# ---------- parts ----------
def part_basemap(src, out, sp, a, log):
    s, d = os.path.join(src, sp.get("file", "basemap.pmtiles")), os.path.join(out, "basemap.pmtiles")
    if same_file(s, d): log("  base map: already here")
    else: log(f"  base map: {clone(s, d, a.clone_only, log)} ({human(os.path.getsize(s))})")
    h = inspect(d)
    if h["problems"]: raise SystemExit(f"basemap.pmtiles does not read: {'; '.join(h['problems'])}")
    p = dict(sp); p.update(file="basemap.pmtiles", maxzoom=h["maxz"], tiles=h["addressed"], bytes=h["file_size"])
    return p


def part_terrain(src, out, sp, bbox, a, log):
    d = os.path.join(out, "terrain.pmtiles")
    if sp.get("file"):  # source is already packed
        s = os.path.join(src, sp["file"])
        if same_file(s, d): log("  terrain: already here")
        else: log(f"  terrain: {clone(s, d, a.clone_only, log)} ({human(os.path.getsize(s))})")
    else:
        tdir = os.path.join(src, sp.get("dir", "terrain"))
        TP = load_tool("terrain-pack")
        tiles = TP.find_tiles(tdir)
        if not tiles: raise SystemExit(f"no terrain tiles under {tdir}")
        want_ids = [t[0] for t in tiles]
        reuse = False
        if header_state(d) == "valid":
            h = inspect(d)
            fmt = TYPES.get(h["ttype"])
            reuse = (not h["problems"] and h["ids"] == want_ids and h["maxz"] == max(t[1] for t in tiles)
                     and not (a.png and fmt != "png"))
        if reuse:
            log(f"  terrain: terrain.pmtiles already holds the same {len(tiles):,} tiles, kept")
        else:
            log(f"  terrain: packing {len(tiles):,} tiles {'as PNG' if a.png else '(lossless WebP if cwebp is installed)'}")
            before = free(out)
            if before < sum(os.path.getsize(t[2]) for t in tiles) + (512 << 20):
                raise SystemExit("not enough free space to pack the terrain")
            TP.pack(tdir, d, bbox, webp=not a.png, log=log)
    h = inspect(d)
    if h["problems"]: raise SystemExit(f"terrain.pmtiles does not read: {'; '.join(h['problems'])}")
    if sp.get("failed"): log(f"  note: the source pack lists {sp['failed']} terrain tiles that never downloaded")
    p = {"file": "terrain.pmtiles", "format": TYPES.get(h["ttype"], "png"), "maxzoom": h["maxz"], "tiles": h["addressed"],
         "bytes": h["file_size"], "encoding": sp.get("encoding", "terrarium")}
    for k in ("date", "source"):
        if k in sp: p[k] = sp[k]
    return p


def part_layers(src, out, sp, a, log):
    sdir, ddir = os.path.join(src, sp.get("dir", "layers")), os.path.join(out, "layers")
    n = same = total = 0
    for root, _, files in os.walk(sdir):
        for fn in sorted(files):
            if fn.startswith(".") or fn.endswith(".part"): continue
            s = os.path.join(root, fn); d = os.path.join(ddir, os.path.relpath(s, sdir))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            if same_file(s, d) and sha256(s) == sha256(d): same += 1
            else: clone(s, d, a.clone_only, log)
            n += 1; total += os.path.getsize(s)
    extra = [f for f in os.listdir(ddir) if not f.startswith(".") and not os.path.exists(os.path.join(sdir, f))] if os.path.isdir(ddir) else []
    log(f"  layers: {n} files ({human(total)}), {n - same} cloned, {same} already here"
        + (f"; {len(extra)} extra files in the hub not in the source: {', '.join(extra[:5])}" if extra else ""))
    p = dict(sp); p.update(dir="layers", bytes=total)
    return p


def part_satellite(out, old, a, log):
    d = os.path.join(out, "satellite.pmtiles")
    if a.skip_satellite:
        if old and os.path.exists(d): log("  satellite: not looked at (--skip-satellite), keeping the entry already in pack.json")
        else: log("  satellite: not looked at (--skip-satellite)")
        return old if (old and os.path.exists(d)) else None
    st = header_state(d)
    if st == "missing":
        log("  satellite: none in the hub folder (add one with sat-pack.py, then run this again)"); return None
    if st == "zeros":
        log("  satellite: satellite.pmtiles is still being downloaded (its header is not written yet). "
            "Skipped for now; run hub-pack again when sat-pack says done."); return None
    if st == "invalid":
        log("  satellite: satellite.pmtiles is not a PMTiles file, skipped"); return None
    h = inspect(d)
    if h["problems"]:
        log(f"  satellite: does not read ({'; '.join(h['problems'])}), skipped"); return None
    if h["file_size"] != h["end"]:
        log("  satellite: there is data past the end of its directories, so a download is running or was stopped. "
            "Skipped; run sat-pack again to finish it, then this."); return None
    sat = (h.get("metadata") or {}).get("offgrid_sat") or {}
    base = sat.get("maxzoom", h["maxz"])
    log(f"  satellite: {h['addressed']:,} tiles, zoom {h['minz']}-{h['maxz']}, {human(h['file_size'])}")
    return {"file": "satellite.pmtiles", "maxzoom": min(base, h["maxz"]), "detail_maxzoom": h["maxz"], "tiles": h["addressed"],
            "bytes": h["file_size"], "attribution": SAT_ATTRIBUTION, "license": "Public domain",
            "date": dt.date.fromtimestamp(os.path.getmtime(d)).isoformat()}


def build(src, out, a, log=say):
    src, out = os.path.abspath(src), os.path.abspath(out)
    if src == out: raise SystemExit("the source pack and the hub folder must be different folders")
    spj = os.path.join(src, "pack.json")
    if not os.path.exists(spj): raise SystemExit(f"no pack.json in {src}")
    with open(spj) as f: spack = json.load(f)
    os.makedirs(out, exist_ok=True)
    opj = os.path.join(out, "pack.json")
    old = {}
    if os.path.exists(opj):
        with open(opj) as f: old = json.load(f)
    f0 = free(out)
    log(f"Hub pack for {spack.get('name', spack.get('slug', '?'))} ({spack.get('level', '?')}). Free space: {human(f0)}")
    sparts, parts = spack.get("parts", {}), {}
    if "basemap" in sparts: parts["basemap"] = part_basemap(src, out, sparts["basemap"], a, log)
    if "terrain" in sparts: parts["terrain"] = part_terrain(src, out, sparts["terrain"], spack["bbox"], a, log)
    if "layers" in sparts: parts["layers"] = part_layers(src, out, sparts["layers"], a, log)
    for k in sparts:
        if k not in parts and k != "satellite": log(f"  note: part '{k}' is not handled by hub-pack and was left out")
    sat = part_satellite(out, old.get("parts", {}).get("satellite"), a, log)
    if sat: parts["satellite"] = sat
    pack = {k: v for k, v in spack.items() if k not in ("parts", "updated", "hub")}
    pack["parts"] = parts
    now = dt.datetime.now().isoformat(timespec="seconds")
    pack["hub"] = {"version": 1, "built": now}
    pack["updated"] = now
    write_json(opj, pack)
    f1 = free(out)
    log(f"  wrote pack.json. Free space now {human(f1)} (change {(f1 - f0) / 1e6:+,.0f} MB)")
    return pack


# ---------- check ----------
def check(out, log=say, write=True):
    out = os.path.abspath(out)
    with open(os.path.join(out, "pack.json")) as f: pack = json.load(f)
    probs, files = [], []
    for name, p in pack.get("parts", {}).items():
        if "file" in p:
            path = os.path.join(out, p["file"])
            if not os.path.exists(path): probs.append(f"{name}: {p['file']} is missing"); continue
            st = header_state(path)
            if st != "valid": probs.append(f"{name}: {p['file']} header is {st}"); continue
            h = inspect(path)
            probs += [f"{name}: {m}" for m in h["problems"]]
            if h["problems"]: continue
            if p.get("bytes") is not None and p["bytes"] != h["file_size"]: probs.append(f"{name}: pack.json says {p['bytes']} bytes, file is {h['file_size']}")
            if p.get("tiles") is not None and p["tiles"] != h["addressed"]: probs.append(f"{name}: pack.json says {p['tiles']} tiles, file holds {h['addressed']}")
            top = p.get("detail_maxzoom", p.get("maxzoom"))
            if top is not None and top != h["maxz"]: probs.append(f"{name}: pack.json says max zoom {top}, file goes to {h['maxz']}")
            if p.get("format") and p["format"] != TYPES.get(h["ttype"]): probs.append(f"{name}: pack.json says {p['format']}, file holds {TYPES.get(h['ttype'])}")
            files.append(p["file"])
            log(f"  {name:10} ok  {h['addressed']:>10,} tiles  zoom {h['minz']}-{h['maxz']}  {human(h['file_size'])}")
        elif "dir" in p:
            dpath = os.path.join(out, p["dir"])
            if not os.path.isdir(dpath): probs.append(f"{name}: folder {p['dir']} is missing"); continue
            got = sorted(os.path.relpath(os.path.join(r, fn), out) for r, _, fs in os.walk(dpath) for fn in fs
                         if not fn.startswith(".") and not fn.endswith(".part"))
            if name == "layers":
                ip = os.path.join(dpath, "index.json")
                if not os.path.exists(ip): probs.append("layers: index.json is missing"); continue
                with open(ip) as f: idx = json.load(f)
                if p.get("layers") is not None and len(idx) != p["layers"]: probs.append(f"layers: pack.json says {p['layers']} layers, index.json lists {len(idx)}")
                if p.get("count") is not None and sum(o.get("count", 0) for o in idx) != p["count"]: probs.append("layers: feature count in pack.json does not match index.json")
                for o in idx:
                    if "id" in o and not os.path.exists(os.path.join(dpath, o["id"] + ".geojson")): probs.append(f"layers: {o['id']}.geojson is missing")
                if p.get("bytes") is not None and p["bytes"] != sum(os.path.getsize(os.path.join(out, g)) for g in got):
                    probs.append("layers: byte total in pack.json does not match the files")
            elif name == "terrain":
                pngs = sum(1 for g in got if g.endswith(".png"))
                if p.get("tiles") is not None and pngs != p["tiles"] - p.get("failed", 0): probs.append(f"terrain: {pngs} tiles on disk, pack.json expects {p['tiles'] - p.get('failed', 0)}")
            files += got
            log(f"  {name:10} ok  {len(got):>10,} files  {human(sum(os.path.getsize(os.path.join(out, g)) for g in got))}")
        else:
            probs.append(f"{name}: has neither file nor dir")
    if probs:
        for m in probs: log("  PROBLEM " + m)
        log(f"Check failed: {len(probs)} problem(s). checksums.txt was not written.")
        return False
    if write:
        log("  sha256 sums (this reads every byte, a few seconds per GB)…")
        lines = []
        for rel in sorted(files):
            s = sha256(os.path.join(out, rel)); lines.append(f"{s}  {rel}\n")
            if "/" not in rel: log(f"    {s}  {rel}")
        tmp = os.path.join(out, "checksums.txt.part")
        with open(tmp, "w") as f: f.writelines(lines)
        os.replace(tmp, os.path.join(out, "checksums.txt"))
        log(f"  wrote checksums.txt ({len(lines)} files)")
    log("Check passed.")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="SOURCE_PACK OUT_DIR, or just OUT_DIR with --check")
    ap.add_argument("--check", action="store_true", help="only check OUT_DIR and write checksums.txt")
    ap.add_argument("--png", action="store_true", help="pack terrain as PNG even when cwebp is installed")
    ap.add_argument("--clone-only", action="store_true", help="fail instead of making a full copy when a clone is not possible")
    ap.add_argument("--skip-satellite", action="store_true", help="do not open satellite.pmtiles at all (keeps any entry already in pack.json)")
    ap.add_argument("--no-check", action="store_true", help="skip the check (and checksums) after building")
    a = ap.parse_args(argv)
    if a.check:
        if len(a.paths) != 1: ap.error("--check takes one folder")
        return 0 if check(a.paths[0]) else 1
    if len(a.paths) != 2: ap.error("give SOURCE_PACK and OUT_DIR")
    build(a.paths[0], a.paths[1], a)
    if a.no_check: return 0
    say("Checking the hub pack:")
    return 0 if check(a.paths[1]) else 1


if __name__ == "__main__":
    sys.exit(main())
