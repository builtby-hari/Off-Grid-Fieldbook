"""Fetch Terrarium elevation tiles (AWS Open Data, Mapzen/USGS) for North Texas into z/x/y.png folders."""
import math, os, sys, urllib.request, concurrent.futures as cf
OUT = os.path.expanduser("~/Developer/Off-Grid/downloads/maps/terrain")
W, S, E, N = -98.6, 32.0, -95.8, 34.0
MAXZ = int(sys.argv[1]) if len(sys.argv) > 1 else 12
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
def xy(lon, lat, z):
    n = 2 ** z; r = math.radians(lat)
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(r)) / math.pi) / 2 * n)
jobs = []
for z in range(0, MAXZ + 1):
    x0, y0 = xy(W, N, z); x1, y1 = xy(E, S, z)
    jobs += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
def get(j):
    z, x, y = j; p = f"{OUT}/{z}/{x}/{y}.png"
    if os.path.exists(p) and os.path.getsize(p) > 0: return 0
    os.makedirs(os.path.dirname(p), exist_ok=True)
    for _ in range(4):
        try:
            d = urllib.request.urlopen(urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": "offgrid-terrain/1.0"}), timeout=30).read()
            if d[:8] != b"\x89PNG\r\n\x1a\n": raise ValueError("not png")
            open(p + ".part", "wb").write(d); os.replace(p + ".part", p); return len(d)
        except Exception as e: err = e
    print("FAIL", j, err, flush=True); return 0
print(len(jobs), "tiles", flush=True)
with cf.ThreadPoolExecutor(12) as ex: total = sum(ex.map(get, jobs))
print("done bytes", total, flush=True)
