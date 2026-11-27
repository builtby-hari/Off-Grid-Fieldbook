"""Tests for the pack tools in tools/packs (terrain-pack, sat-pack, hub-pack).

Run from the repo root (standard library only, no network):
  python3 -I -m unittest discover -s tests -p 'test_*.py' -v

Every archive a test writes is read back with pmtiles_extract, so the files are proven readable.
The places used here are made-up boxes, not anyone's location.
"""
import argparse, contextlib, gzip, hashlib, importlib.util, io, json, os, random, shutil, struct, subprocess, sys, tempfile, unittest, zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACKS = os.path.join(ROOT, "tools", "packs")
sys.path.insert(0, PACKS)
import pmtiles_extract as PX  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), os.path.join(PACKS, name + ".py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


TP, SP, HP = load("terrain-pack"), load("sat-pack"), load("hub-pack")
quiet = lambda *a, **k: None
BOX = [10.0, 10.0, 12.0, 12.0]


# ---------- helpers ----------
def wtext(path, text):
    with open(path, "w") as f: f.write(text)


def rbytes(path):
    with open(path, "rb") as f: return f.read()


def rjson(path):
    with open(path) as f: return json.load(f)


def make_png(w, h, seed):
    """Small RGB PNG with random pixels. Returns (png bytes, raw RGB bytes)."""
    rnd = random.Random(seed)
    rows = [bytes(rnd.randrange(256) for _ in range(w * 3)) for _ in range(h)]
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(b"".join(b"\0" + r for r in rows))) + chunk(b"IEND", b""))
    return png, b"".join(rows)


def read_all(path):
    """Every tile in a PMTiles file as {tile_id: bytes}, using pmtiles_extract's parsers."""
    with open(path, "rb") as f:
        h = PX.parse_header(f.read(127))
        out = {}
        def walk(raw):
            for tid, off, ln, run in PX.parse_dir(PX.decompress(raw, h["icomp"])):
                if run == 0:
                    f.seek(h["leaf_off"] + off); walk(f.read(ln))
                else:
                    f.seek(h["data_off"] + off); data = f.read(ln)
                    for k in range(run): out[tid + k] = data
        f.seek(h["root_off"]); walk(f.read(h["root_len"]))
        f.seek(h["meta_off"]); meta = json.loads(PX.decompress(f.read(h["meta_len"]), h["icomp"]))
    return h, out, meta


def make_terrain(dirn, tiles, size=8):
    """Write z/x/y.png tiles. Returns {tile_id: (png, raw)}."""
    out = {}
    for i, (z, x, y) in enumerate(tiles):
        png, raw = make_png(size, size, i)
        os.makedirs(os.path.join(dirn, str(z), str(x)), exist_ok=True)
        with open(os.path.join(dirn, str(z), str(x), f"{y}.png"), "wb") as f: f.write(png)
        out[PX.zxy_to_id(z, x, y)] = (png, raw)
    return out


def fake_jpeg(z, x, y):
    if (x + y) % 7 == 0: return None  # like a 404 outside the coverage
    return b"\xff\xd8" + struct.pack("<BII", z, x, y) + bytes((x * 31 + y) % 251 for _ in range(20 + (x + y) % 50))


@contextlib.contextmanager
def small_leaves(size=100):
    """Force leaf directories (normally only thousands of tiles need them) so the leaf layout is tested."""
    real = PX.build_dirs
    def forced(ents):
        leaves, roots = bytearray(), []
        for i in range(0, len(ents), size):
            d = PX.build_dir(ents[i:i + size]); roots.append((ents[i][0], len(leaves), len(d), 0)); leaves += d
        return PX.build_dir(roots), bytes(leaves)
    PX.build_dirs = forced
    try: yield
    finally: PX.build_dirs = real


def args(**kw):
    d = dict(png=False, clone_only=False, skip_satellite=False, no_check=False)
    d.update(kw); return argparse.Namespace(**d)


TERRAIN_TILES = [(0, 0, 0), (1, 1, 0), (1, 1, 1), (2, 2, 1), (2, 2, 2), (2, 3, 1), (3, 4, 3)]


class TerrainPackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.tmp)
        self.src = os.path.join(self.tmp, "terrain")
        self.tiles = make_terrain(self.src, TERRAIN_TILES)

    def test_png_pack_round_trips(self):
        out = os.path.join(self.tmp, "t.pmtiles")
        res = TP.pack(self.src, out, BOX, webp=False, log=quiet)
        h, got, meta = read_all(out)
        self.assertEqual(res, {"file": "t.pmtiles", "tiles": 7, "bytes": os.path.getsize(out), "maxzoom": 3, "format": "png"})
        self.assertEqual((h["ttype"], h["tcomp"], h["clustered"], h["minz"], h["maxz"]), (2, 1, 1, 0, 3))
        self.assertEqual(h["addressed"], 7)
        self.assertEqual(got, {tid: png for tid, (png, _) in self.tiles.items()})
        self.assertEqual(meta["encoding"], "terrarium")
        self.assertLessEqual(h["root_off"] + h["root_len"], 16384)
        self.assertEqual(h["data_off"], TP.DATA_OFF)
        # clustered: tile data is laid out in tile id order
        with open(out, "rb") as f:
            f.seek(h["data_off"]); data = f.read(h["data_len"])
        self.assertEqual(data, b"".join(self.tiles[t][0] for t in sorted(self.tiles)))
        self.assertEqual(os.path.getsize(out), max(h["meta_off"] + h["meta_len"], h["leaf_off"] + h["leaf_len"], h["data_off"] + h["data_len"]))
        self.assertFalse(os.path.exists(out + ".part"))

    def test_leaf_directories_round_trip(self):
        src = os.path.join(self.tmp, "many")
        rnd = random.Random(7)
        tiles = [(5, x, y) for x in range(32) for y in range(20)] + [(6, x, y) for x in range(20) for y in range(30)]
        body = {}
        for z, x, y in tiles:
            os.makedirs(os.path.join(src, str(z), str(x)), exist_ok=True)
            b = body[PX.zxy_to_id(z, x, y)] = b"\x89PNG" + bytes(rnd.randrange(256) for _ in range(rnd.randrange(1, 300)))
            with open(os.path.join(src, str(z), str(x), f"{y}.png"), "wb") as f: f.write(b)
        out = os.path.join(self.tmp, "many.pmtiles")
        with small_leaves():
            TP.pack(src, out, BOX, webp=False, log=quiet)
        h, got, _ = read_all(out)
        self.assertGreater(h["leaf_len"], 0)
        self.assertEqual(h["leaf_off"], h["data_off"] + h["data_len"])
        self.assertEqual(got, body)

    @unittest.skipUnless(shutil.which("cwebp") and shutil.which("dwebp"), "needs cwebp and dwebp")
    def test_webp_is_pixel_identical(self):
        out = os.path.join(self.tmp, "w.pmtiles")
        res = TP.pack(self.src, out, BOX, webp=True, log=quiet)
        self.assertEqual(res["format"], "webp")
        h, got, meta = read_all(out)
        self.assertEqual(h["ttype"], 4); self.assertEqual(meta["format"], "webp")
        for tid, (_, raw) in self.tiles.items():
            wp, pam = os.path.join(self.tmp, "x.webp"), os.path.join(self.tmp, "x.pam")
            with open(wp, "wb") as f: f.write(got[tid])
            subprocess.run(["dwebp", "-quiet", "-pam", wp, "-o", pam], check=True)
            with open(pam, "rb") as f: data = f.read()
            px = data[data.index(b"ENDHDR\n") + 7:]
            rgb = b"".join(px[i:i + 3] for i in range(0, len(px), 4))
            self.assertEqual(rgb, raw, f"tile {tid} changed")


class SatPackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.tmp)
        self.out = os.path.join(self.tmp, "satellite.pmtiles")
        self.detail = ["10.5,10.5,10.8,10.8:13"]

    def expected(self, maxzoom=12):
        return {PX.zxy_to_id(*t): fake_jpeg(*t) for t in SP.plan_jobs(BOX, maxzoom, self.detail) if fake_jpeg(*t)}

    def test_no_default_area(self):
        r = subprocess.run([sys.executable, "-I", os.path.join(PACKS, "sat-pack.py"), os.path.join(self.tmp, "x.pmtiles")], capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b"--bbox", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "x.pmtiles")))

    def test_file_layout(self):
        with small_leaves():
            res = SP.build(self.out, BOX, 12, self.detail, workers=4, fetch=fake_jpeg, log=quiet, chunk=100)
        h, got, meta = read_all(self.out)
        exp = self.expected()
        self.assertEqual(got, exp)
        self.assertEqual(res["tiles"], len(exp))
        self.assertEqual((h["ttype"], h["tcomp"], h["clustered"], h["icomp"]), (3, 1, 0, 2))
        self.assertEqual(h["data_off"], SP.DATA_OFF)
        self.assertEqual((h["minz"], h["maxz"]), (min(z for z, x, y in SP.plan_jobs(BOX, 12, self.detail) if fake_jpeg(z, x, y)), 13))
        self.assertGreater(h["leaf_len"], 0)
        self.assertEqual(h["addressed"], len(exp))
        # tile data first, then leaf directories, then metadata, which ends the file
        self.assertEqual(h["leaf_off"], h["data_off"] + h["data_len"])
        self.assertEqual(h["meta_off"], h["leaf_off"] + h["leaf_len"])
        self.assertEqual(os.path.getsize(self.out), h["meta_off"] + h["meta_len"])
        self.assertLessEqual(h["root_off"] + h["root_len"], SP.DATA_OFF)
        self.assertEqual(meta["offgrid_sat"]["maxzoom"], 12)
        self.assertEqual(meta["offgrid_sat"]["detail"], self.detail)

    def test_overlapping_detail_boxes_fetch_each_tile_once(self):
        calls = []
        def fetch(z, x, y): calls.append((z, x, y)); return fake_jpeg(z, x, y)
        detail = ["10.5,10.5,10.8,10.8:10", "10.6,10.6,10.9,10.9:10"]
        SP.build(self.out, BOX, 6, detail, workers=4, fetch=fetch, log=quiet)
        self.assertEqual(len(calls), len(set(calls)))

    def test_resume_after_interrupted_run(self):
        clean = os.path.join(self.tmp, "clean.pmtiles")
        SP.build(clean, BOX, 12, self.detail, workers=1, fetch=fake_jpeg, log=quiet, chunk=50)
        n = [0]
        def flaky(z, x, y):
            n[0] += 1
            if n[0] > 230: raise IOError("network went away")
            return fake_jpeg(z, x, y)
        with self.assertRaises(IOError):
            SP.build(self.out, BOX, 12, self.detail, workers=1, fetch=flaky, log=quiet, chunk=50)
        # mid-download the header is zeros, so nothing treats the file as finished
        self.assertEqual(HP.header_state(self.out), "zeros")
        done_before = len(SP.read_idx(self.out + ".idx"))
        self.assertEqual(done_before, 200)  # four whole chunks were logged
        # a hard stop can also leave junk after the last logged tile and a cut-off index line
        with open(self.out, "ab") as f: f.write(b"junk" * 1000)
        with open(self.out + ".idx", "a") as f: f.write("12345 99")
        calls = []
        def fetch(z, x, y): calls.append((z, x, y)); return fake_jpeg(z, x, y)
        SP.build(self.out, BOX, 12, self.detail, workers=2, fetch=fetch, log=quiet, chunk=50)
        total = len(SP.plan_jobs(BOX, 12, self.detail))
        self.assertEqual(len(calls), total - done_before)
        _, got, _ = read_all(self.out)
        _, want, _ = read_all(clean)
        self.assertEqual(got, want)

    def test_rerun_after_finish_fetches_nothing(self):
        SP.build(self.out, BOX, 7, (), workers=2, fetch=fake_jpeg, log=quiet)
        _, first, _ = read_all(self.out)
        calls = []
        def fetch(z, x, y): calls.append(1); return fake_jpeg(z, x, y)
        SP.build(self.out, BOX, 7, (), workers=2, fetch=fetch, log=quiet)
        self.assertEqual(calls, [])
        _, second, _ = read_all(self.out)
        self.assertEqual(first, second)


class HubPackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.tmp)
        self.src = os.path.join(self.tmp, "src", "testland"); self.out = os.path.join(self.tmp, "hub", "testland")
        os.makedirs(self.src)
        self.tiles = make_terrain(os.path.join(self.src, "terrain"), TERRAIN_TILES)
        # a stand-in base map: any valid PMTiles file will do
        bm_src = os.path.join(self.tmp, "bm"); make_terrain(bm_src, [(0, 0, 0), (1, 0, 1)], size=4)
        TP.pack(bm_src, os.path.join(self.src, "basemap.pmtiles"), BOX, webp=False, log=quiet)
        os.makedirs(os.path.join(self.src, "layers"))
        idx = [{"id": "springs", "count": 3}, {"id": "shelters", "count": 2}]
        wtext(os.path.join(self.src, "layers", "index.json"), json.dumps(idx))
        for o in idx: wtext(os.path.join(self.src, "layers", o["id"] + ".geojson"), '{"type":"FeatureCollection","features":[]}')
        self.pack = {"slug": "testland", "name": "Testland", "bbox": BOX, "level": "full", "parts": {
            "basemap": {"file": "basemap.pmtiles", "maxzoom": 1, "bytes": os.path.getsize(os.path.join(self.src, "basemap.pmtiles")),
                        "source": "test", "date": "2026-01-01", "license": "test"},
            "terrain": {"dir": "terrain", "maxzoom": 3, "tiles": 7, "failed": 0, "encoding": "terrarium", "date": "2026-01-02", "source": "test terrain"},
            "layers": {"dir": "layers", "count": 5, "layers": 2, "date": "2026-01-03", "source": "test layers"}}}
        wtext(os.path.join(self.src, "pack.json"), json.dumps(self.pack))
        self.log = []
        self.say = lambda *a: self.log.append(" ".join(str(x) for x in a))

    def build(self, **kw):
        return HP.build(self.src, self.out, args(**kw), log=self.say)

    def test_builds_contract_shape_and_check_passes(self):
        pack = self.build(png=True)
        t = pack["parts"]["terrain"]
        self.assertEqual(set(t), {"file", "format", "maxzoom", "tiles", "bytes", "encoding", "date", "source"})
        self.assertEqual((t["file"], t["format"], t["maxzoom"], t["tiles"], t["encoding"]), ("terrain.pmtiles", "png", 3, 7, "terrarium"))
        self.assertEqual((t["date"], t["source"]), ("2026-01-02", "test terrain"))
        self.assertEqual(t["bytes"], os.path.getsize(os.path.join(self.out, "terrain.pmtiles")))
        _, got, _ = read_all(os.path.join(self.out, "terrain.pmtiles"))
        self.assertEqual(got, {tid: png for tid, (png, _) in self.tiles.items()})
        b = pack["parts"]["basemap"]
        self.assertEqual((b["file"], b["tiles"], b["maxzoom"], b["source"]), ("basemap.pmtiles", 2, 1, "test"))
        self.assertEqual(rbytes(os.path.join(self.out, "basemap.pmtiles")), rbytes(os.path.join(self.src, "basemap.pmtiles")))
        self.assertEqual(pack["parts"]["layers"]["dir"], "layers")
        self.assertTrue(os.path.exists(os.path.join(self.out, "layers", "springs.geojson")))
        self.assertNotIn("satellite", pack["parts"])
        self.assertEqual(rjson(os.path.join(self.out, "pack.json")), pack)
        self.assertTrue(HP.check(self.out, log=self.say))
        sums = dict(l.split("  ", 1)[::-1] for l in rbytes(os.path.join(self.out, "checksums.txt")).decode().splitlines())
        self.assertEqual(set(sums), {"basemap.pmtiles", "terrain.pmtiles", "layers/index.json", "layers/springs.geojson", "layers/shelters.geojson"})
        for rel, s in sums.items():
            self.assertEqual(s, hashlib.sha256(rbytes(os.path.join(self.out, rel))).hexdigest())
        # no absolute paths leak into what gets shared
        self.assertNotIn(self.tmp, rbytes(os.path.join(self.out, "pack.json")).decode())

    def test_rerun_keeps_packed_terrain(self):
        self.build(png=True)
        tp = os.path.join(self.out, "terrain.pmtiles")
        st = os.stat(tp)
        self.build(png=True)
        self.assertEqual((os.stat(tp).st_ino, os.stat(tp).st_mtime_ns), (st.st_ino, st.st_mtime_ns))
        self.assertTrue(any("already holds the same" in m for m in self.log))
        # a new tile in the source means the terrain is packed again
        make_terrain(os.path.join(self.src, "terrain"), [(3, 5, 3)])
        pack = self.build(png=True)
        self.assertEqual(pack["parts"]["terrain"]["tiles"], 8)

    def test_satellite_is_skipped_while_downloading_then_picked_up(self):
        os.makedirs(self.out)
        sat = os.path.join(self.out, "satellite.pmtiles")
        with open(sat, "wb") as f: f.write(b"\0" * 20000)  # what sat-pack leaves while it runs
        pack = self.build(png=True)
        self.assertNotIn("satellite", pack["parts"])
        self.assertTrue(any("still being downloaded" in m for m in self.log))
        os.remove(sat)
        SP.build(sat, BOX, 7, ["10.5,10.5,10.8,10.8:9"], workers=2, fetch=fake_jpeg, log=quiet)
        pack = self.build(png=True)
        s = pack["parts"]["satellite"]
        self.assertEqual(set(s), {"file", "maxzoom", "detail_maxzoom", "tiles", "bytes", "attribution", "license", "date"})
        self.assertEqual((s["maxzoom"], s["detail_maxzoom"], s["attribution"], s["license"]), (7, 9, "USGS The National Map: Imagery", "Public domain"))
        self.assertEqual(s["tiles"], len(read_all(sat)[1]))
        self.assertEqual(s["bytes"], os.path.getsize(sat))
        self.assertTrue(HP.check(self.out, log=self.say))
        # data past the directories means a resumed download is running: skipped again
        with open(sat, "ab") as f: f.write(b"\xff\xd8more")
        pack = self.build(png=True)
        self.assertNotIn("satellite", pack["parts"])

    def test_skip_satellite_never_opens_it(self):
        os.makedirs(self.out)
        with open(os.path.join(self.out, "satellite.pmtiles"), "wb") as f: f.write(b"\0" * 100)
        real = HP.header_state
        def guard(path):
            if path.endswith("satellite.pmtiles"): raise AssertionError("satellite was opened")
            return real(path)
        HP.header_state = guard
        try:
            pack = self.build(png=True, skip_satellite=True)
        finally:
            HP.header_state = real
        self.assertNotIn("satellite", pack["parts"])

    def test_check_catches_wrong_counts(self):
        self.build(png=True)
        self.assertTrue(HP.check(self.out, log=self.say))
        os.remove(os.path.join(self.out, "checksums.txt"))
        pj = os.path.join(self.out, "pack.json"); p = rjson(pj)
        p["parts"]["terrain"]["tiles"] = 99; wtext(pj, json.dumps(p))
        self.assertFalse(HP.check(self.out, log=self.say))
        self.assertFalse(os.path.exists(os.path.join(self.out, "checksums.txt")))
        p["parts"]["terrain"]["tiles"] = 7; wtext(pj, json.dumps(p))
        os.remove(os.path.join(self.out, "layers", "springs.geojson"))
        self.assertFalse(HP.check(self.out, log=self.say))

    def test_check_catches_a_damaged_file(self):
        self.build(png=True)
        tp = os.path.join(self.out, "terrain.pmtiles")
        with open(tp, "r+b") as f: f.truncate(os.path.getsize(tp) - 10)
        self.assertFalse(HP.check(self.out, log=self.say))

    def test_old_pack_with_terrain_dir_is_still_valid(self):
        self.assertTrue(HP.check(self.src, log=self.say, write=False))

    def test_already_packed_source_is_cloned(self):
        self.build(png=True)
        second = os.path.join(self.tmp, "hub2", "testland")
        HP.build(self.out, second, args(), log=self.say)
        self.assertEqual(rbytes(os.path.join(second, "terrain.pmtiles")), rbytes(os.path.join(self.out, "terrain.pmtiles")))
        self.assertTrue(HP.check(second, log=self.say))


if __name__ == "__main__":
    unittest.main()
