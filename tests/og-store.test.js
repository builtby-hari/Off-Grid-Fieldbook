const vm = require("vm"), fs = require("fs");
const src = fs.readFileSync(require("path").join(__dirname, "../app/web/og.js"), "utf8") + "\n;globalThis.OG = OG;";
let disk = null, failNext = 0, puts = 0, conflicts = 0, slow = 0;
const rev = () => disk === null ? "0" : String(disk.length) + ":" + [...disk].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);
const wait = ms => new Promise(r => setTimeout(r, ms));
// Behaves like the app's server: every read carries a revision, and a save against an old revision is refused.
const fetch = async (url, o = {}) => {
  if (slow) await wait(slow);
  if (o.method === "PUT") {
    if (failNext > 0) { failNext--; return { ok: false, status: 500 }; }
    const base = o.headers["X-OffGrid-Base"];
    if (base && base !== rev()) { conflicts++; return { ok: false, status: 409 }; }
    disk = o.body; puts++; return { ok: true, status: 200 };
  }
  const r = rev(), body = disk;
  return { ok: true, status: 200, headers: { get: k => k === "X-Rev" ? r : null }, json: async () => JSON.parse(body || "null") };
};
const realm = () => { const store = {}; const c = vm.createContext({ fetch, setTimeout, location: { origin: "" }, localStorage: { getItem: k => store[k] ?? null, setItem: (k, v) => store[k] = v }, console }); vm.runInContext(src, c); return c.OG; };
const ok = (c, m) => { console.log((c ? "PASS " : "FAIL ") + m); if (!c) process.exitCode = 1; };
(async () => {
  const place = realm(), map = realm();
  const pdb = await place.load(); await map.load();
  const a = place.blank("supply", { name: "Rice" }); pdb.items.push(a); await place.save();
  // map drops a pin from its own (older) copy
  const pin = map.blank("place", { name: "Home" }); map.db.items.push(pin); await map.save();
  ok(JSON.parse(disk).items.length === 2, "map save keeps the record My Place added");
  // My Place edits Rice from its stale copy and saves: the pin must survive
  a.name = "Rice 20 lb"; a.updated = place.now(); await place.save();
  let d = JSON.parse(disk);
  ok(d.items.length === 2 && d.items.some(x => x.name === "Home") && d.items.some(x => x.name === "Rice 20 lb"), "stale My Place save keeps the map pin and its own edit");
  ok(place.db.items.some(x => x.name === "Home"), "My Place copy now includes the pin");
  // delete on My Place, then map saves its copy that still has Rice: must stay deleted
  place.db.items = place.db.items.filter(x => x.id !== a.id); await place.save();
  pin.fields.kind = "home"; pin.updated = map.now(); await map.save();
  d = JSON.parse(disk);
  ok(d.items.length === 1 && d.items[0].fields.kind === "home", "a deleted record is not brought back by another screen");
  // a failed save must not block the next
  failNext = 1; pin.name = "Home base"; pin.updated = map.now();
  let threw = false; try { await map.save(); } catch { threw = true; }
  ok(threw, "failed save reports the failure");
  await map.save(); ok(JSON.parse(disk).items[0].name === "Home base", "the next save after a failure goes through");
  // fresh load pulls other screens' records
  const r2 = map.blank("contact", { name: "Aunt" }); map.db.items.push(r2); await map.save();
  await place.load({ fresh: true }); ok(place.db.items.some(x => x.name === "Aunt"), "fresh load sees a record saved elsewhere");
  // damaged file: refuse to overwrite
  const good = disk; disk = '{"oops":1}'; const e = realm(); const edb = await e.load(); edb.items.push(e.blank("place"));
  threw = false; try { await e.save(); } catch { threw = true; } ok(threw && disk === '{"oops":1}', "a damaged file is never overwritten");
  disk = good; ok(JSON.parse(disk).version === 2, "schema version is 2");
  // two screens save different new records at the very same moment: both must survive
  disk = null; slow = 5; conflicts = 0;
  const s1 = realm(), s2 = realm(); await s1.load(); await s2.load();
  s1.db.items.push(s1.blank("water_container", { name: "Rain barrel" }));
  s2.db.items.push(s2.blank("water_source", { name: "Well pin" }));
  await Promise.all([s1.save(), s2.save()]);
  const names = JSON.parse(disk).items.map(x => x.name).sort().join(", ");
  ok(names === "Rain barrel, Well pin", "two saves at the same moment keep both records (got: " + names + ")");
  ok(conflicts >= 1, "the server refused the stale save and the screen retried (" + conflicts + " conflict)");
  // ten screens at once
  disk = null; const many = []; for (let i = 0; i < 10; i++) { const r = realm(); await r.load(); r.db.items.push(r.blank("supply", { name: "Item " + i })); many.push(r); }
  await Promise.all(many.map(r => r.save()));
  ok(JSON.parse(disk).items.length === 10, "ten screens saving at once keep all ten records");
  slow = 0;
  // an edit that is not saved yet must survive this screen reading the file again (the address changes while you type)
  disk = null; const e1 = realm(); await e1.load(); const home = e1.blank("place", { name: "Home" }); e1.db.items.push(home); await e1.save();
  home.loc = { lng: -97, lat: 33 }; home.updated = e1.now();
  await e1.load({ fresh: true }); await e1.save();
  ok(!!JSON.parse(disk).items[0].loc, "an unsaved map pin survives a fresh read before the save");
  const e2 = realm(); await e2.load(); e2.db.items[0].name = "Home base"; e2.db.items[0].updated = e2.now();
  await Promise.all([e2.load({ fresh: true }), e2.save()]);
  ok(JSON.parse(disk).items[0].name === "Home base", "an edit survives a fresh read that runs at the same time as the save");
})();
