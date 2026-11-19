#!/usr/bin/env python3
"""Build offline "survival map" GeoJSON overlay layers from an OpenStreetMap PBF extract.

One streaming pass over the PBF with pyosmium (SimpleHandler, locations=True, flex_mem).
Only parses the input file. Writes one compact GeoJSON FeatureCollection per category
plus overlays/index.json into the output folder.

Run with the venv python in isolated mode:
  <venv>/bin/python -I tools/build-survival-layers.py
"""

import argparse
import json
import os
import sys
import time

import osmium

HOME_OFF_GRID = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PBF = os.path.join(HOME_OFF_GRID, "downloads/maps/texas-latest.osm.pbf")
DEFAULT_OUT = os.path.join(HOME_OFF_GRID, "downloads/maps/overlays")

GEN_SOURCES = {"solar", "wind", "hydro", "gas", "nuclear", "coal"}


# ---------- tag matchers: return a kind string or None ----------

def kv(key, vals=None):
    def f(t):
        v = t.get(key)
        if v is None:
            return None
        if vals is None or v in vals:
            return v
        return None
    return f


def alt(*fs):
    def f(t):
        for g in fs:
            r = g(t)
            if r:
                return r
        return None
    return f


def _fountain(t):
    if t.get("amenity") == "fountain" and t.get("drinking_water") == "yes":
        return "fountain"
    return None


def _storage_water(t):
    if t.get("man_made") == "storage_tank" and t.get("content") == "water":
        return "storage_tank"
    return None


def _comm_tower(t):
    if t.get("man_made") in ("mast", "tower") and t.get("tower:type") == "communication":
        return t["man_made"]
    return None


def _gen_plant(t):
    # Generators count only when they have a name and a listed source (skips unnamed rooftop units).
    if t.get("power") == "generator" and t.get("generator:source") in GEN_SOURCES and t.get("name"):
        return t["generator:source"]
    return None


# id, label, group, geometry, matcher, extra x keys
def _rail_main(t):
    # main and branch lines you could follow between towns; skip yard tracks, sidings and spurs
    if t.get("railway") == "rail" and t.get("service") not in {"yard", "siding", "spur", "crossover"}:
        return t.get("usage") or "rail"
    return None


def _rail_old(t):
    # disused = rails probably still there; abandoned/razed = rails pulled up, often a flat grade or a trail now
    v = t.get("railway")
    if v in {"disused", "abandoned", "razed"}:
        return v
    return None


CATEGORIES = [
    ("springs", "Springs", "Water", "point", kv("natural", {"spring"}), ["drinking_water"]),
    ("wells", "Water wells", "Water", "point", alt(kv("man_made", {"water_well"}), kv("amenity", {"water_point"})), ["drinking_water", "operator"]),
    ("drinking_water", "Drinking water", "Water", "point", alt(kv("amenity", {"drinking_water"}), _fountain), ["bottle", "operator"]),
    ("water_towers", "Water towers and storage", "Water", "point", alt(kv("man_made", {"water_tower", "water_works", "reservoir_covered"}), _storage_water), ["operator", "capacity"]),
    ("dams", "Dams and weirs", "Water", "point", kv("waterway", {"dam", "weir"}), ["operator"]),
    ("boat_ramps", "Boat ramps", "Water", "point", kv("leisure", {"slipway"}), ["access", "fee"]),

    ("hospitals", "Hospitals", "Medical", "point", alt(kv("amenity", {"hospital"}), kv("healthcare", {"hospital"})), ["emergency", "operator", "healthcare:speciality"]),
    ("clinics", "Clinics and doctors", "Medical", "point", alt(kv("amenity", {"clinic", "doctors", "dentist"}), kv("healthcare", {"clinic", "doctor", "centre"})), ["healthcare:speciality", "emergency", "operator"]),
    ("pharmacies", "Pharmacies", "Medical", "point", alt(kv("amenity", {"pharmacy"}), kv("healthcare", {"pharmacy"})), ["operator"]),
    ("vets", "Veterinarians", "Medical", "point", kv("amenity", {"veterinary"}), ["emergency", "operator"]),

    ("fire", "Fire stations", "Emergency", "point", kv("amenity", {"fire_station"}), ["operator", "emergency"]),
    ("police", "Police stations", "Emergency", "point", kv("amenity", {"police"}), ["operator"]),
    ("shelters", "Shelters and assembly points", "Emergency", "point", alt(kv("amenity", {"shelter"}), kv("emergency", {"assembly_point"}), kv("social_facility", {"shelter"})), ["capacity", "operator"]),
    ("aed", "AEDs (defibrillators)", "Emergency", "point", kv("emergency", {"defibrillator"}), ["access", "indoor"]),

    ("grocery", "Grocery and convenience", "Food & supplies", "point", kv("shop", {"supermarket", "convenience", "greengrocer", "butcher", "wholesale"}), ["operator", "opening_hours"]),
    ("hardware", "Hardware and farm supply", "Food & supplies", "point", kv("shop", {"hardware", "doityourself", "trade", "farm", "agrarian", "garden_centre"}), ["operator"]),
    ("farms", "Farms and markets", "Food & supplies", "point", alt(kv("landuse", {"farmyard", "orchard"}), kv("place", {"farm"}), kv("shop", {"farm"}), kv("amenity", {"marketplace"})), ["operator"]),

    ("fuel", "Fuel stations", "Fuel & power", "point", kv("amenity", {"fuel"}), ["brand", "operator"]),
    ("substations", "Electric substations", "Fuel & power", "point", kv("power", {"substation"}), ["voltage", "operator"]),
    ("power_plants", "Power plants", "Fuel & power", "point", alt(kv("power", {"plant"}), _gen_plant), ["plant:source", "generator:source", "operator"]),
    ("power_lines", "Power lines", "Fuel & power", "line", kv("power", {"line"}), ["voltage", "operator"]),

    ("camping", "Campgrounds and huts", "Shelter & outdoors", "point", kv("tourism", {"camp_site", "caravan_site", "alpine_hut", "wilderness_hut"}), ["fee", "access", "capacity"]),
    ("caves", "Cave entrances", "Shelter & outdoors", "point", kv("natural", {"cave_entrance"}), ["access"]),
    ("peaks", "Peaks and hills", "Shelter & outdoors", "point", kv("natural", {"peak", "hill"}), ["ele"]),
    ("hunting_fishing", "Hunting and fishing", "Shelter & outdoors", "point", kv("leisure", {"hunting_stand", "fishing"}), ["access", "fee"]),

    ("schools", "Schools and colleges", "Community", "point", kv("amenity", {"school", "college", "university"}), ["operator"]),
    ("worship", "Places of worship", "Community", "point", kv("amenity", {"place_of_worship"}), ["religion", "denomination"]),
    ("community", "Community centers and libraries", "Community", "point", kv("amenity", {"community_centre", "townhall", "library", "post_office"}), ["operator"]),

    ("towers", "Comms towers", "Comms", "point", alt(_comm_tower, kv("man_made", {"communications_tower"})), ["operator", "tower:type"]),

    ("airports", "Airports and helipads", "Transport", "point", kv("aeroway", {"aerodrome", "helipad"}), ["iata", "icao", "operator"]),
    ("rail", "Rail stations", "Transport", "point", kv("railway", {"station", "halt"}), ["operator"]),
    ("railroads", "Railroad tracks (in use)", "Transport", "line", _rail_main, ["operator", "usage", "service", "gauge", "ref"]),
    ("rail_old", "Old rail lines (disused or abandoned)", "Transport", "line", _rail_old, ["operator", "historic:railway", "highway"]),
]

CAT_BY_ID = {c[0]: c for c in CATEGORIES}
FUEL_PREFIX = "fuel:"


def classify(t):
    """Return list of (category_id, kind) for a tag dict."""
    out = []
    for cid, _label, _group, _geom, matcher, _x in CATEGORIES:
        kind = matcher(t)
        if kind:
            out.append((cid, kind))
    return out


def build_props(t, kind, xkeys, cid):
    props = {}
    name = t.get("name")
    if name:
        props["n"] = name
    props["k"] = kind
    phone = t.get("phone") or t.get("contact:phone")
    if phone:
        props["ph"] = phone
    hrs = t.get("opening_hours")
    if hrs:
        props["hrs"] = hrs
    hn = t.get("addr:housenumber", "").strip()
    st = t.get("addr:street", "").strip()
    city = t.get("addr:city", "").strip()
    street = " ".join(p for p in (hn, st) if p)
    ad = ", ".join(p for p in (street, city) if p)
    if ad:
        props["ad"] = ad
    x_parts = []
    if cid == "fuel":
        fuels = [k[len(FUEL_PREFIX):] for k, v in t.items() if k.startswith(FUEL_PREFIX) and v == "yes"]
        if fuels:
            x_parts.append(",".join(sorted(fuels)))
    for key in xkeys:
        v = t.get(key)
        if v:
            x_parts.append(f"{key}={v}")
    if x_parts:
        props["x"] = "; ".join(x_parts)
    return props


def make_feature(lon, lat, props, geom_type="Point", coords=None):
    if geom_type == "Point":
        geometry = {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}
    else:
        geometry = {"type": "LineString", "coordinates": coords}
    return {"type": "Feature", "geometry": geometry, "properties": props}


class Collector(osmium.SimpleHandler):
    def __init__(self, line_step):
        super().__init__()
        self.line_step = max(1, line_step)
        self.features = {c[0]: [] for c in CATEGORIES}
        self.skipped_relations = {c[0]: 0 for c in CATEGORIES}
        self.nodes_seen = 0
        self.ways_seen = 0
        self.relations_seen = 0

    def _add(self, cid, feat):
        self.features[cid].append(json.dumps(feat, separators=(",", ":"), ensure_ascii=False))

    def node(self, n):
        self.nodes_seen += 1
        if not n.tags:
            return
        matches = classify({tag.k: tag.v for tag in n.tags})
        if not matches:
            return
        loc = n.location
        if not loc.valid():
            return
        t = {tag.k: tag.v for tag in n.tags}
        for cid, kind in matches:
            geom = CAT_BY_ID[cid][3]
            if geom != "point":
                continue  # lines are only built from ways
            props = build_props(t, kind, CAT_BY_ID[cid][5], cid)
            self._add(cid, make_feature(loc.lon, loc.lat, props))

    def way(self, w):
        self.ways_seen += 1
        if not w.tags:
            return
        t = {tag.k: tag.v for tag in w.tags}
        matches = classify(t)
        if not matches:
            return
        coords_valid = []
        for ref in w.nodes:
            if ref.location.valid():
                coords_valid.append((ref.location.lon, ref.location.lat))
        if not coords_valid:
            return
        for cid, kind in matches:
            geom = CAT_BY_ID[cid][3]
            xkeys = CAT_BY_ID[cid][5]
            if geom == "line":
                if len(coords_valid) < 2:
                    continue
                step = self.line_step
                last = len(coords_valid) - 1
                pts = [coords_valid[i] for i in range(0, last + 1) if i % step == 0 or i == last]
                coords = [[round(lo, 5), round(la, 5)] for lo, la in pts]
                props = build_props(t, kind, xkeys, cid)
                self._add(cid, make_feature(0, 0, props, geom_type="LineString", coords=coords))
            else:
                # Ways used as points: centroid = average of node coordinates.
                n = len(coords_valid)
                lon = sum(c[0] for c in coords_valid) / n
                lat = sum(c[1] for c in coords_valid) / n
                props = build_props(t, kind, xkeys, cid)
                self._add(cid, make_feature(lon, lat, props))

    def relation(self, r):
        self.relations_seen += 1
        if not r.tags:
            return
        matches = classify({tag.k: tag.v for tag in r.tags})
        for cid, _kind in matches:
            # Multipolygon centroids need member-way geometry, which a single pass does not hold.
            self.skipped_relations[cid] += 1


def fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pbf", default=DEFAULT_PBF)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--line-step", type=int, default=3, help="keep every Nth node of power lines, plus endpoints")
    args = ap.parse_args()

    if not os.path.isfile(args.pbf):
        print(f"missing input: {args.pbf}", file=sys.stderr)
        return 2
    os.makedirs(args.out, exist_ok=True)

    t0 = time.time()
    h = Collector(args.line_step)
    h.apply_file(args.pbf, locations=True, idx="flex_mem")
    parse_secs = time.time() - t0
    print(f"pass done in {parse_secs:.1f}s: nodes={h.nodes_seen} ways={h.ways_seen} relations={h.relations_seen}", flush=True)

    index = []
    stats = []
    for cid, label, group, geom, _m, _x in CATEGORIES:
        feats = h.features[cid]
        path = os.path.join(args.out, f"{cid}.geojson")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write('{"type":"FeatureCollection","features":[')
            f.write(",".join(feats))
            f.write("]}")
        os.replace(tmp, path)
        size = os.path.getsize(path)
        index.append({"id": cid, "label": label, "group": group, "count": len(feats), "geom": geom, "bytes": size})
        stats.append((cid, group, len(feats), size, h.skipped_relations[cid]))
        flag = "  <-- OVER 40 MB" if size > 40 * 1024 * 1024 else ""
        print(f"{cid}: {len(feats)} features, {fmt_bytes(size)}{flag}", flush=True)

    with open(os.path.join(args.out, "index.json.tmp"), "w", encoding="utf-8") as f:
        json.dump(index, f, separators=(",", ":"), ensure_ascii=False)
    os.replace(os.path.join(args.out, "index.json.tmp"), os.path.join(args.out, "index.json"))

    total = sum(s[3] for s in stats)
    print(f"total geojson bytes: {total} ({fmt_bytes(total)})")
    print(f"total runtime: {time.time() - t0:.1f}s")
    skipped = {s[0]: s[4] for s in stats if s[4]}
    if skipped:
        print(f"multipolygon relations skipped (no centroid in one pass): {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
