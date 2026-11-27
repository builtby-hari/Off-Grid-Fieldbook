"""Download satellite photos for a region into one PMTiles file. Standard library only. Resumable.

Source: USGS National Map imagery (public domain, US only). Tiles outside the US come back
404 and are skipped, so a state's box is trimmed to land on its own.

  python3 -I sat-pack.py OUT.pmtiles --bbox W,S,E,N --maxzoom 14 [--detail W,S,E,N:17 ...]

--detail adds a sharper area (for example a town you know well) up to its own zoom.
Run it again with the same arguments to resume after a stop.

The file is written in place (tile data first, directories at the end), so it never needs
twice its size on disk.
"""
import argparse, concurrent.futures as cf, gzip, json, os, struct, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmtiles_extract as PX

URL = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
UA = {"User-Agent": "OffGrid-pack-builder/1.0"}
DATA_OFF = 16384  # header + root directory live in the first 16 KB, tile data starts here


def tiles_for(bbox, minz, maxz):
    W, S, E, N = bbox
    for z in range(minz, maxz + 1):
        x0, y0 = PX.lonlat_to_xy(W, N, z)
        x1, y1 = PX.lonlat_to_xy(E, S, z)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                yield z, x, y


def fetch(z, x, y):
    req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers=UA)
    for i in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            return data if data[:2] == b"\xff\xd8" else None  # JPEG only
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except Exception as e:
            err = e
        time.sleep(2 * (i + 1))
    raise IOError(f"{z}/{x}/{y}: {err}")


def plan_jobs(bbox, maxzoom, detail=()):
    """Every tile slot to fetch, in download order, each one once (detail boxes may overlap)."""
    jobs, seen = [], set()
    for t in tiles_for(bbox, 0, maxzoom):
        if t not in seen: seen.add(t); jobs.append(t)
    for d in detail:
        box, z = d.split(":")
        for t in tiles_for([float(v) for v in box.split(",")], maxzoom + 1, int(z)):
            if t not in seen: seen.add(t); jobs.append(t)
    return jobs


def read_idx(idx_path):
    """Tiles already saved: {tile_id: (offset, length)}, offset -1 for a tile the server does not have.
    A last line without its newline was cut off by a stop, so it is ignored (the tile is fetched again)."""
    done = {}
    with open(idx_path) as fh:
        for line in fh:
            if not line.endswith("\n"): break
            p = line.split()
            if len(p) == 3:
                done[int(p[0])] = (int(p[1]), int(p[2]))
    return done


def build(out, bbox, maxzoom=14, detail=(), workers=8, fetch=fetch, log=print, chunk=2000):
    """Download (or resume) the tiles into OUT and write the PMTiles directories. `fetch(z, x, y)`
    returns JPEG bytes or None; it is a parameter so tests can run without the network."""
    jobs = plan_jobs(bbox, maxzoom, detail)
    ids = {t: PX.zxy_to_id(*t) for t in jobs}

    idx_path = out + ".idx"
    done, pos = {}, DATA_OFF
    if os.path.exists(idx_path) and os.path.exists(out):
        done = read_idx(idx_path)
        for off, ln in done.values():
            if off >= 0: pos = max(pos, off + ln)
    f = open(out, "r+b" if os.path.exists(out) else "w+b")
    idx = None
    try:
        f.truncate(pos)  # drop anything written after the last logged tile (and old directories)
        # Zero the header while tiles are being added, so nothing mistakes a half-done file for a
        # finished one. It is written again at the end.
        f.seek(0); f.write(b"\0" * DATA_OFF if pos == DATA_OFF else b"\0" * 127); f.flush()
        idx = open(idx_path, "a")
        todo = [t for t in jobs if ids[t] not in done]
        total = len(jobs)
        log(f"{total:,} tile slots, {len(done):,} already done, {len(todo):,} to go")

        t0, n = time.time(), 0
        def work(t):
            return t, fetch(*t)
        with cf.ThreadPoolExecutor(workers) as ex:
            for i in range(0, len(todo), chunk):
                lines = []
                for t, data in ex.map(work, todo[i:i + chunk]):
                    tid = ids[t]
                    if data:
                        f.seek(pos); f.write(data)
                        done[tid] = (pos, len(data)); lines.append(f"{tid} {pos} {len(data)}\n"); pos += len(data)
                    else:
                        done[tid] = (-1, 0); lines.append(f"{tid} -1 0\n")
                    n += 1
                # tile bytes reach the file before the index says they are there
                f.flush(); os.fsync(f.fileno())
                idx.write("".join(lines)); idx.flush()
                el = time.time() - t0
                rate = n / max(el, 1)
                left = (len(todo) - n) / max(rate, 0.01)
                log(f"  {len(done):,}/{total:,} slots  {(pos - DATA_OFF) / 1e9:.2f} GB  {rate:.0f}/s  about {left / 3600:.1f} h left")

        # directories: entries sorted by tile id, offsets relative to the data section
        ents = sorted((tid, off - DATA_OFF, ln, 1) for tid, (off, ln) in done.items() if off >= 0)
        zooms = [z for (z, _, _), tid in ids.items() if done.get(tid, (-1, 0))[0] >= 0]
        if not ents:
            raise SystemExit("no tiles were found for this area (USGS covers the US only)")
        root, leaves = PX.build_dirs(ents)
        meta = gzip.compress(json.dumps({"name": "Satellite", "attribution": "USGS The National Map: Imagery (public domain)",
                                         "format": "jpg", "offgrid_sat": {"bbox": bbox, "maxzoom": maxzoom, "detail": list(detail)}}).encode(), mtime=0)
        data_len = pos - DATA_OFF
        leaf_off = pos; meta_off = leaf_off + len(leaves)
        f.seek(leaf_off); f.write(leaves); f.write(meta); f.truncate(meta_off + len(meta))
        W, S, E, N = bbox
        hdr = bytearray(b"PMTiles\x03")
        hdr += struct.pack("<QQQQQQQQQQQ", 127, len(root), meta_off, len(meta), leaf_off, len(leaves), DATA_OFF, data_len,
                           len(ents), len(ents), len(ents))
        hdr += struct.pack("<BBBBBB", 0, 2, 1, 3, min(zooms), max(zooms))  # not clustered, gzip dirs, raw JPEG tiles
        hdr += struct.pack("<iiii", *[round(v * 1e7) for v in (W, S, E, N)])
        hdr += struct.pack("<B", 8)
        hdr += struct.pack("<ii", round((W + E) / 2 * 1e7), round((S + N) / 2 * 1e7))
        assert len(hdr) == 127 and 127 + len(root) <= DATA_OFF
        f.flush(); os.fsync(f.fileno())  # directories first, header last
        f.seek(0); f.write(hdr); f.write(root)
        log(f"done: {out} ({os.path.getsize(out) / 1e9:.2f} GB, {len(ents):,} tiles, zoom {min(zooms)}-{max(zooms)})")
        return {"tiles": len(ents), "bytes": os.path.getsize(out), "minzoom": min(zooms), "maxzoom": max(zooms)}
    finally:  # a stop or a network failure must not leave half-flushed handles behind
        f.close()
        if idx: idx.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--bbox", required=True, help="W,S,E,N in degrees")
    ap.add_argument("--maxzoom", type=int, default=14)
    ap.add_argument("--detail", action="append", default=[], help="W,S,E,N:ZOOM, a sharper area")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    build(a.out, [float(v) for v in a.bbox.split(",")], a.maxzoom, a.detail, a.workers,
          log=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
