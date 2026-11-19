// Off-Grid shared code: your records store, record types, status levels, coordinates and units.
// Used by the My Place, Map and Emergency screens. Works offline; saves through the app's local server.
"use strict";
const OG = (() => {
  const api = location.origin;
  const now = () => new Date().toISOString();
  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  const device = (() => { try { let d = localStorage.getItem("og:device"); if (!d) { d = "mac-" + uid(); localStorage.setItem("og:device", d); } return d; } catch { return "mac"; } })();

  // ---------- record types ----------
  // Each field: [key, label, kind, extra]. kind: text, num, date, select, long, check
  const STATUS = {
    shelter: [["designated", "Designated facility", "info"], ["reported_open", "Reported open", "warn"], ["confirmed_open", "Confirmed open", "good"],
              ["closed", "Closed", "bad"], ["unknown", "Status unknown", "muted"]],
    water_source: [["mapped", "Mapped only", "muted"], ["seen", "Water observed", "info"], ["tested", "Tested", "warn"],
                   ["potable", "Confirmed potable", "good"], ["unsafe", "Do not use", "bad"], ["dry", "Dry", "bad"]],
    water_container: [["ok", "In service", "good"], ["needs_clean", "Needs cleaning", "warn"], ["leaking", "Leaking", "bad"], ["empty", "Empty", "muted"]],
    equipment: [["tested_ok", "Passed last test", "good"], ["untested", "Not tested yet", "muted"], ["failed", "Failed last test", "bad"], ["in_repair", "In repair", "warn"]],
    supply: [["ok", "Stocked", "good"], ["low", "Running low", "warn"], ["out", "Out", "bad"]],
    place: [["ok", "Checked", "good"], ["unverified", "Not checked", "muted"], ["problem", "Problem", "bad"]],
    route: [["ok", "Passable", "good"], ["unverified", "Not checked", "muted"], ["blocked", "Blocked", "bad"]],
    contact: [["ok", "Reached", "good"], ["unknown", "Not reached", "muted"]],
    bulletin: [["heard", "Heard, not confirmed", "warn"], ["confirmed", "Confirmed", "good"], ["outdated", "No longer true", "muted"], ["false", "Turned out false", "bad"]],
  };
  const TYPES = {
    water_container: { label: "Water storage", icon: "🛢️", group: "Water", fields: [
      ["capacity_gal", "Capacity (gal)", "num"], ["level_gal", "Current level (gal)", "num"],
      ["use", "Intended use", "select", ["drinking", "cooking", "hygiene", "pets", "livestock", "irrigation", "untested roof runoff"]],
      ["daily_draw_gal", "Daily draw (gal/day)", "num"], ["draw_basis", "Draw is", "select", ["estimated", "measured"]],
      ["last_filled", "Last filled", "date"], ["last_cleaned", "Last cleaned", "date"], ["clean_every_days", "Clean every (days)", "num"],
      ["dimensions", "Dimensions", "text"], ["bung_thread", "Bung thread (size and pitch)", "text"],
      ["fittings", "Fittings that actually fit (part numbers)", "long"], ["gaskets", "Gasket and seal sizes", "text"],
      ["valve", "Valve type", "text"], ["screen", "Screen, lid, first flush", "text"], ["spares", "Spare parts and where", "long"]] },
    water_source: { label: "Water source", icon: "💧", group: "Water", fields: [
      ["kind", "Kind", "select", ["creek", "river", "lake or pond", "spring", "well", "tap or refill station", "distribution point", "rain catchment"]],
      ["access_point", "Exact access point", "text"], ["last_flowing", "Last seen flowing", "date"], ["advisory", "Known advisory", "text"],
      ["treatment", "Treatment needed", "text"], ["test_method", "Last test method and result", "long"], ["permission", "Permission to draw", "select", ["public", "permission granted", "ask first", "no permission"]]] },
    shelter: { label: "Shelter", icon: "⛺", group: "Safety", fields: [
      ["kind", "Kind", "select", ["evacuation shelter", "tornado safe room", "cooling center", "warming center", "clean-air center", "overnight shelter", "pet shelter", "trusted host", "campground"]],
      ["operator", "Operated by", "text"], ["reported", "Report (who, when)", "text"], ["route_a", "Way to get there #1", "long"], ["route_b", "Way to get there #2", "long"],
      ["bring", "What to bring", "long"], ["pets", "Pets allowed", "select", ["yes", "no", "service animals only", "unknown"]], ["accessible", "Accessible entrance", "text"]] },
    equipment: { label: "Equipment", icon: "🔧", group: "Gear", fields: [
      ["category", "Category", "select", ["power station", "UPS", "generator", "solar panel", "pump", "radio", "fridge or freezer", "filter", "heater", "tool", "vehicle", "other"]],
      ["model", "Make and model", "text"], ["serial_note", "Where the serial plate is", "text"], ["watts", "Running watts", "num"], ["surge_watts", "Startup watts", "num"],
      ["wh_day", "Daily use (Wh/day)", "num"], ["wh_basis", "Daily use is", "select", ["estimated", "measured"]], ["capacity_wh", "Battery capacity (Wh)", "num"],
      ["last_test", "Last real test", "date"], ["test_result", "Test result and runtime", "long"], ["test_every_days", "Test every (days)", "num"],
      ["connector", "Connectors and cables", "text"], ["parts", "Part numbers (oil, filter, seals, fuses)", "long"], ["manual", "Manual (file or library link)", "text"], ["priority", "Charging priority", "select", ["1 medical", "2 essential", "3 useful", "4 comfort"]]] },
    supply: { label: "Supply", icon: "📦", group: "Supplies", fields: [
      ["category", "Category", "select", ["drinking water", "food", "pet food", "batteries", "fuel", "first aid", "hygiene", "medication", "filters", "other"]],
      ["qty", "Quantity on hand", "num"], ["unit", "Unit", "text"], ["daily_use", "Used per day", "num"], ["use_basis", "Use rate is", "select", ["estimated", "measured"]],
      ["bin", "Bin or shelf", "text"], ["expires", "Expires", "date"], ["allergens", "Allergens", "text"]] },
    place: { label: "Place", icon: "📍", group: "Places", fields: [
      ["kind", "Kind", "select", ["home", "meeting point", "utility shutoff", "breaker panel", "first-aid kit", "spare key", "supply bin", "exit", "trusted host", "flood spot", "radio reception", "garden bed", "other"]],
      ["where", "Exactly where (words someone else can follow)", "long"], ["how", "How to use or open it", "long"], ["tools", "Tool needed", "text"]] },
    route: { label: "Route", icon: "🧭", group: "Places", fields: [
      ["mode", "Mode", "select", ["drive", "walk", "bike", "wheelchair", "with trailer"]], ["from", "From", "text"], ["to", "To", "text"],
      ["distance_mi", "Distance (mi)", "num"], ["avoids", "Avoids (bridge, low crossing)", "text"], ["directions", "Written directions", "long"], ["water_stops", "Water and rest stops", "long"]] },
    contact: { label: "Contact", icon: "☎️", group: "People", fields: [
      ["role", "Role", "select", ["family", "out-of-area contact", "neighbor", "doctor or pharmacy", "vet", "utility", "plumber or well", "insurer", "other"]],
      ["phone", "Phone", "text"], ["radio", "Radio channel or call sign", "text"], ["address", "Address", "text"], ["checkin", "Check-in window", "text"], ["can_help", "Can help with", "text"]] },
    bulletin: { label: "Bulletin", icon: "📢", group: "People", fields: [
      ["message", "What was announced", "long"], ["heard_on", "Heard on", "select", ["NOAA weather radio", "AM/FM radio", "GMRS or ham", "TV", "neighbor", "door notice", "text or phone", "official website", "other"]],
      ["heard_by", "Who heard it", "text"], ["heard_at", "When (date and time)", "text"], ["area", "Area it covers", "text"],
      ["good_until", "Good until (date and time, if said)", "text"], ["confirmed_by", "Confirmed by (who, how, when)", "text"]] },
  };
  const COMMON = [["source", "Source of this info", "text"], ["access", "Access or permission", "text"], ["season", "Seasonal availability", "text"],
    ["contact_info", "Contact details", "text"], ["accessibility", "Accessibility", "text"],
    ["broke_later", "What broke later? (clogs, freeze damage, wear, redesigns)", "long"], ["notes", "Notes", "long"]];

  // ---------- store ----------
  // Every screen (My Place, Map, Emergency) holds its own copy of the records. So a save never
  // writes that copy blindly: it reads the file again, merges, then writes. Schema version 2 adds
  // "deleted" (id -> time) so a record removed on one screen is not brought back by another.
  const VERSION = 2;
  let DB = null, base = {};   // base: id -> the record as last seen on disk (JSON text)
  let diskRev = null;   // the server's revision of the file as this screen last read it
  async function readDisk() {
    const r = await fetch(api + "/api/data/records.json", { cache: "no-store" });
    if (!r.ok) throw new Error("read failed");
    diskRev = r.headers && r.headers.get ? r.headers.get("X-Rev") : null;
    const d = await r.json();
    if (d && !Array.isArray(d.items)) throw new Error("records file is damaged");
    return d || { version: VERSION, items: [] };
  }
  function remember() { base = {}; DB.items.forEach(x => base[x.id] = JSON.stringify(x)); }
  // Fold what is on disk into this screen's copy. Changes made here win unless the disk copy is newer.
  function merge(disk) {
    const mine = new Map(DB.items.map(x => [x.id, x]));
    const tomb = Object.assign({}, disk.deleted, DB.deleted);
    for (const id in base) if (!mine.has(id) && !tomb[id]) tomb[id] = now();   // deleted on this screen
    const out = [];
    for (const d of disk.items) {
      if (tomb[d.id]) { mine.delete(d.id); continue; }
      const m = mine.get(d.id);
      if (!m) { out.push(d); continue; }                                        // added on another screen
      mine.delete(d.id);
      const mineChanged = JSON.stringify(m) !== base[d.id], diskChanged = JSON.stringify(d) !== base[d.id];
      out.push(diskChanged && (!mineChanged || (d.updated || "") > (m.updated || "")) ? d : m);
    }
    for (const m of mine.values()) if (!tomb[m.id]) out.push(m);                // new on this screen
    DB.items = out; DB.deleted = tomb; DB.version = VERSION;
    const drills = new Map([...(disk.drills || []), ...(DB.drills || [])].map(x => [x.t, x]));
    if (drills.size) DB.drills = [...drills.values()].sort((x, y) => (y.t || "").localeCompare(x.t || ""));
    if (!DB.calc && disk.calc) DB.calc = disk.calc;
    if (disk.migratedPins) DB.migratedPins = true;
  }
  // load() gives this screen's copy. load({ fresh: true }) also pulls in what other screens saved.
  async function load(opts = {}) {
    if (DB && !opts.fresh) return DB;
    // "base" must be what is on disk, not this screen's copy: an edit that is not saved yet has to still count as an edit.
    if (DB) { try { const disk = await readDisk(); merge(disk); base = {}; disk.items.forEach(x => base[x.id] = JSON.stringify(x)); delete DB.unread; } catch { DB.unread = true; } return DB; }   // unread: the file could not be read just now
    try { DB = await readDisk(); } catch { DB = { version: VERSION, items: [], unread: true }; }
    DB.version = VERSION; remember();
    // one-time move of map pins saved in the old viewer
    try { const pins = JSON.parse(localStorage.getItem("map:pins") || "[]");
      if (pins.length && !DB.migratedPins) { pins.forEach(p => DB.items.push(blank("place", { name: p.name, loc: { lng: p.lng, lat: p.lat }, fields: { kind: /home/i.test(p.name) ? "home" : "other" } })));
        DB.migratedPins = true; await save(); } } catch {}
    return DB;
  }
  let saving = Promise.resolve();
  function save() {
    // One failed save must not block the next one, so the queue always recovers.
    saving = saving.catch(() => {}).then(async () => {
      // Read, merge, then write against the revision just read. If another screen saved in between,
      // the server answers 409 and this screen reads and merges again. Nothing is ever written blind.
      for (let attempt = 0; attempt < 30; attempt++) {
        if (attempt) await new Promise(r => setTimeout(r, Math.random() * 40 * attempt));   // step back a little more each time
        merge(await readDisk());            // if the file can't be read, stop here and write nothing
        delete DB.unread; DB.saved = now();
        const headers = { "X-OffGrid": "1", "Content-Type": "application/json" };
        if (diskRev) headers["X-OffGrid-Base"] = diskRev;
        const r = await fetch(api + "/api/data/records.json", { method: "PUT", headers, body: JSON.stringify(DB) });
        if (r.status === 409) continue;
        if (!r.ok) throw new Error("save failed");
        remember(); return;
      }
      throw new Error("save failed: the records kept changing");
    });
    return saving;
  }
  // What a brand new record starts as. Something you just added is not "running low" or "needs cleaning".
  const NEW_STATUS = { shelter: "unknown", water_source: "seen", water_container: "ok", equipment: "untested", supply: "ok", place: "unverified", route: "unverified", contact: "unknown", bulletin: "heard" };
  function blank(type, extra = {}) {
    const st = STATUS[type] || STATUS.place;
    return Object.assign({ id: uid(), type, name: "New " + TYPES[type].label.toLowerCase(), loc: null, status: (NEW_STATUS[type] || st[0][0]),
      verified: null, fields: {}, photos: [], guides: [], links: [], log: [], created: now(), updated: now() }, extra);
  }
  function statusOf(r) {
    const s = (STATUS[r.type] || STATUS.place).find(x => x[0] === r.status);
    const out = s ? { key: s[0], label: s[1], tone: s[2] } : { key: "", label: "No status", tone: "muted" };
    // bulletins go stale on their own: yesterday's "shelter open" must not look current
    if (r.type === "bulletin" && (out.key === "heard" || out.key === "confirmed")) {
      const until = Date.parse(r.fields.good_until || ""), age = (Date.now() - Date.parse(r.created)) / 3600e3;
      if ((until && Date.now() > until) || (!until && age > 24)) return { key: out.key, label: out.label + ", " + Math.round(age / 24 * 10) / 10 + " days old", tone: "muted" };
    }
    return out;
  }
  function addLog(r, text, kind = "note", extra = {}) { r.log.unshift(Object.assign({ t: now(), text, kind, device }, extra)); r.updated = now(); }
  async function upload(file) {
    const r = await fetch(api + "/api/media", { method: "POST", headers: { "X-OffGrid": "1", "Content-Type": file.type || "application/octet-stream" }, body: file });
    if (!r.ok) throw new Error("upload failed"); return (await r.json()).url;
  }

  // ---------- runway: how long things last ----------
  const daysBetween = (a, b) => (new Date(b) - new Date(a)) / 864e5;
  function runway(items) {
    const out = {};
    const add = (key, have, use, basis) => { const o = out[key] || (out[key] = { have: 0, use: 0, basis: new Set() }); o.have += have || 0; o.use += use || 0; if (basis) o.basis.add(basis); };
    items.forEach(r => {
      const f = r.fields || {};
      if (r.type === "water_container" && r.status !== "leaking") add("water: " + (f.use || "unassigned"), +f.level_gal || 0, +f.daily_draw_gal || 0, f.draw_basis || "estimated");
      if (r.type === "supply" && f.category) add(f.category, +f.qty || 0, +f.daily_use || 0, f.use_basis || "estimated");
    });
    return Object.entries(out).map(([k, o]) => ({ key: k, have: o.have, use: o.use, days: o.use > 0 ? o.have / o.use : null,
      basis: o.basis.has("estimated") || !o.basis.size ? "estimated" : "measured" })).sort((a, b) => (a.days ?? 1e9) - (b.days ?? 1e9));
  }
  function dueItems(items) {
    const t = now(), due = [];
    items.forEach(r => { const f = r.fields || {};
      if (r.type === "water_container" && f.last_cleaned && f.clean_every_days) { const d = +f.clean_every_days - daysBetween(f.last_cleaned, t); if (d < 14) due.push({ r, what: "Clean", days: d }); }
      if (r.type === "equipment") {
        if (r.status === "failed") due.push({ r, what: "Failed last test", days: -999 });
        if (f.last_test && f.test_every_days) { const d = +f.test_every_days - daysBetween(f.last_test, t); if (d < 14) due.push({ r, what: "Test", days: d }); }
        else if (!f.last_test) due.push({ r, what: "Never tested", days: -1 }); }
      if (r.type === "supply" && f.expires) { const d = daysBetween(t, f.expires); if (d < 60) due.push({ r, what: "Expires", days: d }); } });
    return due.sort((a, b) => a.days - b.days);
  }

  // ---------- coordinates (WGS84): DMS, DDM, UTM, USNG/MGRS ----------
  function dms(v, p, n) { const a = Math.abs(v), d = Math.floor(a), mf = (a - d) * 60, m = Math.floor(mf), s = (mf - m) * 60;
    return `${d}°${String(m).padStart(2, "0")}'${s.toFixed(1).padStart(4, "0")}"${v >= 0 ? p : n}`; }
  function ddm(v, p, n) { const a = Math.abs(v), d = Math.floor(a); return `${d}°${((a - d) * 60).toFixed(3)}'${v >= 0 ? p : n}`; }
  function utm(lat, lon) {
    const a = 6378137, f = 1 / 298.257223563, k0 = 0.9996, e2 = f * (2 - f), ep2 = e2 / (1 - e2);
    const zone = Math.floor((lon + 180) / 6) + 1, lon0 = ((zone - 1) * 6 - 180 + 3) * Math.PI / 180;
    const φ = lat * Math.PI / 180, λ = lon * Math.PI / 180;
    const N = a / Math.sqrt(1 - e2 * Math.sin(φ) ** 2), T = Math.tan(φ) ** 2, C = ep2 * Math.cos(φ) ** 2, A = Math.cos(φ) * (λ - lon0);
    const M = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * φ - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * Math.sin(2 * φ)
      + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * Math.sin(4 * φ) - (35 * e2 ** 3 / 3072) * Math.sin(6 * φ));
    const E = k0 * N * (A + (1 - T + C) * A ** 3 / 6 + (5 - 18 * T + T ** 2 + 72 * C - 58 * ep2) * A ** 5 / 120) + 500000;
    let Nn = k0 * (M + N * Math.tan(φ) * (A ** 2 / 2 + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24 + (61 - 58 * T + T ** 2 + 600 * C - 330 * ep2) * A ** 6 / 720));
    if (lat < 0) Nn += 10000000;
    const band = "CDEFGHJKLMNPQRSTUVWXX"[Math.floor((lat + 80) / 8)];
    return { zone, band, E, N: Nn };
  }
  function usng(lat, lon, digits = 5) {
    const u = utm(lat, lon), set = (u.zone - 1) % 6 + 1;
    const colL = ["ABCDEFGH", "JKLMNPQR", "STUVWXYZ"][(set - 1) % 3], rowL = "ABCDEFGHJKLMNPQRSTUV";
    const col = colL[Math.floor(u.E / 100000) - 1], row = rowL[(Math.floor(u.N / 100000) + (set % 2 === 0 ? 5 : 0)) % 20];
    const pad = v => String(Math.floor((v % 100000) / 10 ** (5 - digits))).padStart(digits, "0");
    return `${u.zone}${u.band} ${col}${row} ${pad(u.E)} ${pad(u.N)}`;
  }
  function coordLines(lat, lon) {
    const u = utm(lat, lon);
    return { dd: `${lat.toFixed(5)}, ${lon.toFixed(5)}`, dms: `${dms(lat, "N", "S")} ${dms(lon, "E", "W")}`, ddm: `${ddm(lat, "N", "S")} ${ddm(lon, "E", "W")}`,
      utm: `${u.zone}${u.band} ${Math.round(u.E)}E ${Math.round(u.N)}N`, usng: usng(lat, lon) };
  }
  function miles(a, b) { const R = 3958.8, r = x => x * Math.PI / 180, dLat = r(b[1] - a[1]), dLng = r(b[0] - a[0]);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(r(a[1])) * Math.cos(r(b[1])) * Math.sin(dLng / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); }
  function bearing(a, b) { const r = x => x * Math.PI / 180, y = Math.sin(r(b[0] - a[0])) * Math.cos(r(b[1]));
    const x = Math.cos(r(a[1])) * Math.sin(r(b[1])) - Math.sin(r(a[1])) * Math.cos(r(b[1])) * Math.cos(r(b[0] - a[0])); return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360; }
  const compass = d => ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"][Math.round(d / 22.5) % 16];
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const ago = t => { if (!t) return "never"; const d = (Date.now() - new Date(t)) / 864e5; return d < 1 ? "today" : d < 2 ? "yesterday" : d < 60 ? Math.round(d) + " days ago" : Math.round(d / 30) + " months ago"; };

  return { load, save, blank, statusOf, addLog, upload, runway, dueItems, TYPES, STATUS, COMMON, coordLines, utm, usng, miles, bearing, compass, esc, ago, uid, now, get db() { return DB; } };
})();
