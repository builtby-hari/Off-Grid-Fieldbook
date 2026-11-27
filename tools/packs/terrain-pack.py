"""Pack a folder of terrain tiles (z/x/y.png) into one PMTiles file. Standard library only.

One file copies faster, wastes no space on big SD cards (thousands of small files each
take a whole storage block), and reads faster over slow USB.

  python3 terrain-pack.py PACK_DIR/terrain OUT/terrain.pmtiles --bbox W,S,E,N [--webp]

--webp re-saves each tile as lossless WebP (about 28% smaller, pixel-identical) when the
`cwebp` tool is installed. Without it the PNG tiles are packed as they are.
"""
import argparse, concurrent.futures as cf, gzip, json, os, shutil, struct, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmtiles_extract as PX

DATA_OFF = 16384  # header + root directory live in the first 16 KB, tile data starts here


def find_tiles(root):
    out = []
    for z in os.listdir(root):
        if not z.isdigit(): continue
        for x in os.listdir(os.path.join(root, z)):
            if not x.isdigit(): continue
            for f in os.listdir(os.path.join(root, z, x)):
                y, ext = os.path.splitext(f)
                if y.isdigit() and ext == ".png":
                    out.append((PX.zxy_to_id(int(z), int(x), int(y)), int(z), os.path.join(root, z, x, f)))
    out.sort()
    return out


def to_webp(path):
    fd, tmp = tempfile.mkstemp(suffix=".webp"); os.close(fd)
    try:
        subprocess.run(["cwebp", "-quiet", "-lossless", "-exact", "-z", "4", path, "-o", tmp], check=True)
        with open(tmp, "rb") as f: return f.read()
    finally:
        os.remove(tmp)


def read_png(path):
    with open(path, "rb") as f: return f.read()


def pack(src, out, bbox, webp=False, workers=8, log=print):
    tiles = find_tiles(src)
    if not tiles: raise SystemExit(f"no z/x/y.png tiles under {src}")
    if webp and not shutil.which("cwebp"):
        log("  cwebp not found, packing the PNG tiles as they are"); webp = False
    conv = to_webp if webp else read_png
    # Tile data goes straight into the final file after a 16 KB slot for the header and root
    # directory; leaf directories and metadata are appended after the data. That needs only the
    # file's own size on disk (no second copy while assembling), which matters on a tight drive.
    ents, pos, tmp = [], DATA_OFF, out + ".part"
    with open(tmp, "wb") as f, cf.ThreadPoolExecutor(workers) as ex:
        f.write(b"\0" * DATA_OFF)
        for i, ((tid, _, _), data) in enumerate(zip(tiles, ex.map(conv, [t[2] for t in tiles])), 1):
            f.write(data); ents.append((tid, pos - DATA_OFF, len(data), 1)); pos += len(data)
            if log and i % 5000 == 0: log(f"    {i:,}/{len(tiles):,} tiles  {pos / 1e6:,.0f} MB")
        root, leaves = PX.build_dirs(ents)
        zs = [t[1] for t in tiles]
        meta = gzip.compress(json.dumps({"name": "Terrain", "encoding": "terrarium", "format": "webp" if webp else "png"}).encode(), mtime=0)
        leaf_off = pos; meta_off = leaf_off + len(leaves)
        f.write(leaves); f.write(meta)
        W, S, E, N = bbox
        hdr = bytearray(b"PMTiles\x03")
        hdr += struct.pack("<QQQQQQQQQQQ", 127, len(root), meta_off, len(meta), leaf_off, len(leaves), DATA_OFF, pos - DATA_OFF,
                           len(ents), len(ents), len(ents))
        hdr += struct.pack("<BBBBBB", 1, 2, 1, 4 if webp else 2, min(zs), max(zs))  # clustered, gzip dirs, raw tiles, webp/png
        hdr += struct.pack("<iiii", *[round(v * 1e7) for v in (W, S, E, N)])
        hdr += struct.pack("<B", min(max(zs), 8))
        hdr += struct.pack("<ii", round((W + E) / 2 * 1e7), round((S + N) / 2 * 1e7))
        assert len(hdr) == 127 and 127 + len(root) <= DATA_OFF
        f.seek(0); f.write(hdr); f.write(root)
    os.replace(tmp, out)
    log(f"  wrote {out}: {len(ents):,} tiles, {os.path.getsize(out) / 1e6:,.0f} MB, zoom {min(zs)}-{max(zs)}, {'webp' if webp else 'png'}")
    return {"file": os.path.basename(out), "tiles": len(ents), "bytes": os.path.getsize(out), "maxzoom": max(zs),
            "format": "webp" if webp else "png"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--bbox", required=True, help="W,S,E,N in degrees")
    ap.add_argument("--webp", action="store_true")
    a = ap.parse_args()
    pack(a.src, a.out, [float(v) for v in a.bbox.split(",")], a.webp)
