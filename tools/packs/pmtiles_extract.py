"""Cut a region out of a PMTiles v3 map (local file or URL) without the pmtiles CLI.

Reads only the directories and tiles that touch the box, using HTTP Range requests for URLs,
and writes a new, clustered PMTiles file. Standard library only.

  python3 -I pmtiles_extract.py SOURCE OUT.pmtiles --bbox W,S,E,N [--maxzoom 15]
SOURCE is a path or https URL (for example https://build.protomaps.com/20261118.pmtiles).
"""
import argparse, bisect, concurrent.futures as cf, gzip, io, json, math, os, struct, sys, time, urllib.request

UA = {"User-Agent": "OffGrid-pack-builder/1.0"}


# ---------- tile ids (Hilbert curve, per the PMTiles v3 spec) ----------
def zxy_to_id(z, x, y):
    acc = ((1 << (2 * z)) - 1) // 3
    n, d, s = 1 << z, 0, (1 << z) >> 1
    while s > 0:
        rx = 1 if x & s else 0
        ry = 1 if y & s else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x, y = s - 1 - x, s - 1 - y  # spec rotates within the current quadrant size
            x, y = y, x
        s >>= 1
    return acc + d


def lonlat_to_xy(lon, lat, z):
    n = 1 << z
    lat = max(min(lat, 85.0511), -85.0511)
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return min(max(x, 0), n - 1), min(max(y, 0), n - 1)


def wanted_ids(bbox, minz, maxz):
    W, S, E, N = bbox
    ids = []
    for z in range(minz, maxz + 1):
        x0, y0 = lonlat_to_xy(W, N, z)
        x1, y1 = lonlat_to_xy(E, S, z)
        ids.extend(zxy_to_id(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))
    ids.sort()
    return ids


# ---------- reading ----------
class Source:
    def __init__(self, src):
        self.src, self.url = src, src.startswith("http")
        self.f = None if self.url else open(src, "rb")
        self.fetched = 0

    def read(self, off, length):
        if length <= 0:
            return b""
        self.fetched += length
        if not self.url:
            self.f.seek(off)
            return self.f.read(length)
        req = urllib.request.Request(self.src, headers={**UA, "Range": f"bytes={off}-{off + length - 1}"})
        for i in range(6):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = r.read()
                if len(data) != length:
                    raise IOError(f"short read {len(data)}/{length}")
                return data
            except Exception as e:
                err = e
                time.sleep(1.5 * (i + 1))
        raise IOError(f"range {off}+{length}: {err}")


def read_varint(b, pos):
    shift = result = 0
    while True:
        c = b[pos]; pos += 1
        result |= (c & 0x7F) << shift
        if not c & 0x80:
            return result, pos
        shift += 7


def decompress(data, kind):
    if kind in (0, 1):
        return data
    if kind == 2:
        return gzip.decompress(data)
    raise ValueError(f"compression {kind} not supported")


def parse_dir(raw):
    n, p = read_varint(raw, 0)
    ids, runs, lens, offs = [0] * n, [0] * n, [0] * n, [0] * n
    last = 0
    for i in range(n):
        v, p = read_varint(raw, p); last += v; ids[i] = last
    for i in range(n):
        runs[i], p = read_varint(raw, p)
    for i in range(n):
        lens[i], p = read_varint(raw, p)
    for i in range(n):
        v, p = read_varint(raw, p)
        offs[i] = offs[i - 1] + lens[i - 1] if (v == 0 and i > 0) else v - 1
    return list(zip(ids, offs, lens, runs))


def parse_header(b):
    if b[:7] != b"PMTiles" or b[7] != 3:
        raise ValueError("not a PMTiles v3 file")
    q = struct.unpack_from("<QQQQQQQQQQQ", b, 8)
    h = dict(zip(["root_off", "root_len", "meta_off", "meta_len", "leaf_off", "leaf_len", "data_off", "data_len",
                  "addressed", "entries", "contents"], q))
    h["clustered"], h["icomp"], h["tcomp"], h["ttype"], h["minz"], h["maxz"] = struct.unpack_from("<BBBBBB", b, 96)
    h["bounds"] = [v / 1e7 for v in struct.unpack_from("<iiii", b, 102)]
    h["center_z"] = b[118]
    h["center"] = [v / 1e7 for v in struct.unpack_from("<ii", b, 119)]
    return h


def has_any(ids, lo, hi):  # any wanted id in [lo, hi)
    i = bisect.bisect_left(ids, lo)
    return i < len(ids) and ids[i] < hi


def collect(src, h, ids):
    """Walk only the directory branches that can hold wanted tiles. Returns [(tile_id, src_off, len, run)]."""
    out = []
    def walk(raw, depth):
        ents = parse_dir(decompress(raw, h["icomp"]))
        for i, (tid, off, ln, run) in enumerate(ents):
            nxt = ents[i + 1][0] if i + 1 < len(ents) else 1 << 62
            if run == 0:  # leaf directory covering [tid, nxt)
                if has_any(ids, tid, nxt):
                    walk(src.read(h["leaf_off"] + off, ln), depth + 1)
            elif has_any(ids, tid, tid + run):
                # keep only the wanted ids inside this run (runs repeat one tile, e.g. ocean)
                j = bisect.bisect_left(ids, tid)
                while j < len(ids) and ids[j] < tid + run:
                    out.append((ids[j], off, ln))
                    j += 1
    walk(src.read(h["root_off"], h["root_len"]), 0)
    return out


# ---------- writing ----------
def write_varint(buf, v):
    while v >= 0x80:
        buf.append((v & 0x7F) | 0x80); v >>= 7
    buf.append(v)


def build_dir(ents):
    b = bytearray()
    write_varint(b, len(ents))
    last = 0
    for e in ents:
        write_varint(b, e[0] - last); last = e[0]
    for e in ents: write_varint(b, e[3])
    for e in ents: write_varint(b, e[2])
    for i, e in enumerate(ents):
        if i > 0 and e[1] == ents[i - 1][1] + ents[i - 1][2]:
            write_varint(b, 0)
        else:
            write_varint(b, e[1] + 1)
    return gzip.compress(bytes(b), mtime=0)


def build_dirs(ents):
    root = build_dir(ents)
    if len(root) <= 16384 - 127:
        return root, b""
    size = 4096
    while True:
        leaves, roots = bytearray(), []
        for i in range(0, len(ents), size):
            chunk = ents[i:i + size]
            d = build_dir(chunk)
            roots.append((chunk[0][0], len(leaves), len(d), 0))
            leaves += d
        root = build_dir(roots)
        if len(root) <= 16384 - 127:
            return root, bytes(leaves)
        size *= 2


def extract(source, out, bbox, maxzoom=None, minzoom=0, workers=16, log=print):
    src = Source(source)
    h = parse_header(src.read(0, 127))
    maxz = min(h["maxz"], maxzoom if maxzoom is not None else h["maxz"])
    ids = wanted_ids(bbox, max(minzoom, h["minz"]), maxz)
    log(f"  looking for {len(ids):,} tile slots, zoom {minzoom}-{maxz}")
    found = collect(src, h, ids)
    meta_raw = src.read(h["meta_off"], h["meta_len"])
    # unique source tiles, in source order (keeps the file clustered and fetches contiguous)
    uniq = sorted({(off, ln) for _, off, ln in found})
    total = sum(ln for _, ln in uniq)
    log(f"  {len(found):,} tiles, {len(uniq):,} unique, {total / 1e6:,.0f} MB to fetch")
    # merge nearby ranges into big reads (gap up to 256 KB, read up to 32 MB)
    groups, cur = [], None
    for off, ln in uniq:
        if cur and off - (cur[0] + cur[1]) <= 262144 and (off + ln - cur[0]) <= 32 << 20:
            cur[1] = off + ln - cur[0]; cur[2].append((off, ln))
        else:
            cur = [off, ln, [(off, ln)]]; groups.append(cur)
    tmp = out + ".part"
    newoff, pos = {}, 0
    done = [0]
    t0 = time.time()
    def fetch(g):
        return g, src.read(h["data_off"] + g[0], g[1])
    with open(tmp, "wb") as f, cf.ThreadPoolExecutor(workers if src.url else 1) as ex:
        step = max(1, len(groups) // 20)
        for gi, (g, data) in enumerate(ex.map(fetch, groups), 1):
            for off, ln in g[2]:
                f.write(data[off - g[0]: off - g[0] + ln])
                newoff[(off, ln)] = pos; pos += ln
            done[0] += sum(ln for _, ln in g[2])
            if log and len(groups) > 20 and (gi % step == 0 or gi == len(groups)):
                log(f"    {done[0] / max(total, 1) * 100:5.1f}%  {done[0] / 1e6:,.0f} of {total / 1e6:,.0f} MB  {done[0] / 1e6 / max(time.time() - t0, 0.1):.1f} MB/s")
    # entries in tile-id order, merging identical consecutive tiles into runs
    ents = []
    for tid, off, ln in sorted(found):
        o = newoff[(off, ln)]
        if ents and ents[-1][1] == o and ents[-1][0] + ents[-1][3] == tid:
            e = ents[-1]; ents[-1] = (e[0], e[1], e[2], e[3] + 1)
        else:
            ents.append((tid, o, ln, 1))
    root, leaves = build_dirs(ents)
    meta = decompress(meta_raw, h["icomp"])
    try:
        mj = json.loads(meta); mj["offgrid_extract"] = {"bbox": bbox, "maxzoom": maxz, "source": os.path.basename(source)}
        meta = json.dumps(mj).encode()
    except Exception:
        pass
    meta = gzip.compress(meta, mtime=0)
    root_off = 127; meta_off = root_off + len(root); leaf_off = meta_off + len(meta); data_off = leaf_off + len(leaves)
    W, S, E, N = bbox
    hdr = bytearray(b"PMTiles\x03")
    hdr += struct.pack("<QQQQQQQQQQQ", root_off, len(root), meta_off, len(meta), leaf_off, len(leaves), data_off, pos,
                       len(found), len(ents), len(uniq))
    hdr += struct.pack("<BBBBBB", 1, 2, h["tcomp"], h["ttype"], max(minzoom, h["minz"]), maxz)
    hdr += struct.pack("<iiii", *[round(v * 1e7) for v in (W, S, E, N)])
    hdr += struct.pack("<B", min(maxz, max(0, 10)))
    hdr += struct.pack("<ii", round((W + E) / 2 * 1e7), round((S + N) / 2 * 1e7))
    assert len(hdr) == 127
    final = out + ".assemble"
    with open(final, "wb") as f:
        f.write(hdr); f.write(root); f.write(meta); f.write(leaves)
        with open(tmp, "rb") as t:
            while True:
                c = t.read(8 << 20)
                if not c: break
                f.write(c)
    os.remove(tmp); os.replace(final, out)
    log(f"  wrote {out} ({os.path.getsize(out) / 1e6:,.0f} MB, read {src.fetched / 1e6:,.0f} MB)")
    return {"tiles": len(found), "bytes": os.path.getsize(out), "maxzoom": maxz}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source"); ap.add_argument("out")
    ap.add_argument("--bbox", required=True, help="W,S,E,N in degrees")
    ap.add_argument("--maxzoom", type=int); ap.add_argument("--minzoom", type=int, default=0)
    a = ap.parse_args()
    extract(a.source, a.out, [float(v) for v in a.bbox.split(",")], a.maxzoom, a.minzoom)
