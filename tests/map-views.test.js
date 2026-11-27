// Checks the map page's logic for packed terrain and the Road / Satellite / Hybrid switch (app/web/map/index.html):
// where terrain tiles come from, which satellite sources get made, and which road-map layers each view shows.
const vm = require("vm"), fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "../app/web/map/index.html"), "utf8");
let failed = 0;
const check = (ok, msg) => { console.log((ok ? "PASS " : "FAIL ") + msg); if (!ok) failed++; };
const grab = name => {
  const m = new RegExp("function " + name + "\\([^)]*\\)\\s*\\{[\\s\\S]*?\\n\\}").exec(html)
    || new RegExp("const " + name + " = [\\s\\S]*?\\);\\n").exec(html);
  if (!m) { check(false, name + " is found in app/web/map/index.html"); process.exit(1); }
  return m[0];
};
const ctx = {};
vm.runInNewContext(["viewShows", "zxyOf", "terrainTiles", "satPlan", "satSources", "satLayers"].map(grab).join("\n")
  + ";this.f = { viewShows, zxyOf, terrainTiles, satPlan, satSources, satLayers };", ctx);
const { viewShows, zxyOf, terrainTiles, satPlan, satSources, satLayers } = ctx.f;
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// ---- terrain: old folder of PNGs vs one PMTiles file ----
const P = "http://127.0.0.1:47321/packs/texas/";
const oldT = terrainTiles({ dir: "terrain", maxzoom: 12, encoding: "terrarium" }, P);
check(oldT.tiles === P + "terrain/{z}/{x}/{y}.png" && oldT.file === "", "old packs keep reading terrain/{z}/{x}/{y}.png");
const newT = terrainTiles({ file: "terrain.pmtiles", format: "webp", maxzoom: 12, encoding: "terrarium" }, P);
check(newT.file === P + "terrain.pmtiles", "new packs read terrain.pmtiles from the pack folder");
check(newT.tiles === "pmtiles://" + P + "terrain.pmtiles/{z}/{x}/{y}", "hill shading gets a pmtiles:// tile address");
check(newT.type === "image/webp", "packed terrain tiles are decoded as WebP");
check(terrainTiles({ file: "terrain.pmtiles", format: "png" }, P).type === "image/png", "a PNG terrain file is decoded as PNG");
check(terrainTiles(null, P).tiles === P + "terrain/{z}/{x}/{y}.png", "no terrain part falls back to the terrain folder");

// ---- tile address parsing (what the elevation-line maker asks for) ----
check(eq(zxyOf(newT.tiles.replace("{z}/{x}/{y}", "12/948/1653")), [12, 948, 1653]), "reads z/x/y from a pmtiles:// address");
check(eq(zxyOf(P + "terrain/7/30/52.png"), [7, 30, 52]), "reads z/x/y from a .png address");
check(eq(zxyOf("pmtiles://http://127.0.0.1:47321/packs/a2/terrain.pmtiles/0/0/0"), [0, 0, 0]), "a digit in the host or slug does not confuse it");
check(zxyOf("pmtiles://x/terrain.pmtiles") === null, "an address without z/x/y gives null");

// ---- satellite plan ----
const header = { minZoom: 0, maxZoom: 17, minLon: -106.6, minLat: 25.7, maxLon: -93.0, maxLat: 36.5, tileType: 3 };
const meta = { attribution: "USGS The National Map: Imagery (public domain)",
  offgrid_sat: { bbox: [-106.6, 25.7, -93.0, 36.5], maxzoom: 14, detail: ["-96.82,32.77,-96.78,32.79:17"] } };
const part = { file: "satellite.pmtiles", maxzoom: 14, detail_maxzoom: 17, attribution: "USGS The National Map: Imagery" };
const plan = satPlan(part, header, meta, P + "satellite.pmtiles");
check(plan.maxzoom === 14, "the whole region stops at zoom 14 (pack.json maxzoom), then enlarges instead of going blank");
check(plan.detail.length === 1 && plan.detail[0].minzoom === 15 && plan.detail[0].maxzoom === 17, "the sharp area covers zoom 15 to 17");
check(eq(plan.detail[0].bounds, [-96.82, 32.77, -96.78, 32.79]), "the sharp area is limited to its own box");
check(eq(plan.bounds, [-106.6, 25.7, -93.0, 36.5]), "photo requests stay inside the file's bounds");
check(plan.attribution === "USGS The National Map: Imagery", "attribution comes from pack.json");
check(plan.tiles === "pmtiles://" + P + "satellite.pmtiles/{z}/{x}/{y}", "satellite tiles use the pmtiles:// address");
check(satPlan({ file: "s.pmtiles" }, header, meta, "u").maxzoom === 14, "without pack.json maxzoom, the file's own note (14) is used");
check(satPlan({ file: "s.pmtiles", maxzoom: 14, detail_maxzoom: 16 }, header, meta, "u").detail[0].maxzoom === 16, "detail_maxzoom caps a sharper area");
check(satPlan(part, header, {}, "u").detail.length === 0, "no detail note in the file: one source, no blank sharp tiles");
check(satPlan(part, header, { offgrid_sat: { detail: ["bad", "1,2:17", "-96,33,-97,32:17"] } }, "u").detail.length === 0, "broken detail boxes are skipped");
check(satPlan(part, Object.assign({}, header, { minLon: 0, maxLon: 0, minLat: 0, maxLat: 0 }), meta, "u").bounds[0] === -106.6, "an empty header box falls back to the file's note");
check(satPlan(part, Object.assign({}, header, { maxZoom: 12 }), meta, "u").maxzoom === 12, "never asks for zooms past what the file holds");

const src = satSources(plan), lays = satLayers(plan);
check(eq(Object.keys(src), ["x_sat", "x_sat_0"]), "one source for the region and one per sharp area");
check(src.x_sat.maxzoom === 14 && src.x_sat_0.minzoom === 15 && src.x_sat_0.maxzoom === 17, "source zoom ranges match the plan");
check(src.x_sat.attribution === plan.attribution, "photo sources carry the USGS attribution");
check(eq(lays.map(l => l.id), ["x_sat", "x_sat_0"]) && lays[1].minzoom === 15 && lays.every(l => l.type === "raster"), "photo layers: region first, sharp area on top from zoom 15");

// ---- which road-map layers each view shows ----
check(viewShows("road", "fill", true) && viewShows("road", "line", true), "Road shows everything");
check(!viewShows("satellite", "line", true) && !viewShows("satellite", "symbol", true) && !viewShows("satellite", "fill", true), "Satellite hides roads, labels and fills above the photos");
check(viewShows("satellite", "fill", false), "Satellite keeps land colors under the photos (they fill gaps)");
check(viewShows("hybrid", "line", true) && viewShows("hybrid", "symbol", true), "Hybrid keeps roads, boundaries and names on top");
check(!viewShows("hybrid", "fill", true), "Hybrid hides water and building fills that would cover the photos");

process.exitCode = failed ? 1 : 0;
