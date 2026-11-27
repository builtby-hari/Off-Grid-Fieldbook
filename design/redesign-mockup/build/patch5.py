import sys
S = sys.argv[1]
path = S + '/fieldbook-redesign.src.html'
src = open(S + '/fieldbook-redesign.src.v5.html').read()   # always patch from the v5 backup

def rep(a, b, n=1):
    global src
    assert src.count(a) == n, (a[:90], src.count(a))
    src = src.replace(a, b)

# ---------------- CSS ----------------
rep('mark { background: var(--mark); color: inherit;', 'mark { background: var(--mark); color: var(--ink);')
rep('.app { position: relative; display: grid; grid-template-columns: 228px minmax(0, 1fr); height: 690px;', '.app { position: relative; display: grid; grid-template-columns: 228px minmax(0, 1fr); height: 716px;')
rep('.appwrap.phone .app { height: 760px; }', '.appwrap.phone .app { height: 700px; }')
rep('padding: 14px 10px 10px; display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow: auto; }', 'padding: 12px 10px 8px; display: flex; flex-direction: column; gap: 8px; min-height: 0; overflow: auto; }')
rep('.tab { border: 0; background: none; border-radius: 7px; min-height: 40px;', '.tab { border: 0; background: none; border-radius: 7px; min-height: 36px;')
rep('.subs { display: flex; flex-direction: column; padding: 2px 0 6px 25px; }', '.subs { display: flex; flex-direction: column; padding: 1px 0 4px 25px; }')
rep('.subs button { border: 0; background: none; text-align: left; padding: 5px 10px;', '.subs button { border: 0; background: none; text-align: left; padding: 3px 10px;')
rep('.foot { display: flex; flex-direction: column; gap: 1px; border-top: 1px solid var(--line); padding-top: 8px; }', '.foot { display: flex; flex-direction: column; gap: 0; border-top: 1px solid var(--line); padding-top: 6px; }')
rep('.foot button { border: 0; background: none; text-align: left; padding: 7px 9px;', '.foot button { border: 0; background: none; text-align: left; padding: 5px 9px;')
rep('.state i { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }', '.state i { flex: none; width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }\n.state.warn i { background: var(--due); }')
rep('display: flex; flex-wrap: wrap; gap: 8px; align-items: flex-start; pointer-events: none; }', 'display: flex; flex-wrap: nowrap; gap: 8px; align-items: flex-start; pointer-events: none; }')
rep('height: 40px; flex: 0 1 260px; min-width: 150px; }', 'height: 40px; flex: 1 1 140px; min-width: 110px; max-width: 260px; }')
rep('.packchip { background', '.packchip { flex: none; white-space: nowrap; background')
rep('.maptools { margin-left: auto; display: flex; gap: 6px; }', '.maptools { margin-left: auto; display: flex; gap: 6px; flex: none; }')
rep('.swatch { width: 12px;', '.drawer .dhead { display: flex; align-items: center; justify-content: space-between; gap: 8px; }\n.drawer label.miss { color: var(--ink2); flex-wrap: wrap; }\n.drawer label.miss .linkbtn { font-size: 13px; }\n.swatch { flex: none; width: 12px;')
rep('border-radius: 5px; padding: 3px 8px; }\n.emptymap', 'border-radius: 5px; padding: 3px 8px; }\n.mapbox.has-drawer .mapfoot { max-width: calc(100% - 306px); }\n.emptymap')
rep('.split .list { border-right', '.split.plan { grid-template-columns: 190px minmax(0, 1fr); }\n.split.plan .detail { padding: 22px 18px 34px; }\n.split .list { border-right')
rep('.filters { display: flex; gap: 5px;', '.filters { flex: none; display: flex; gap: 5px;')
rep('.sheet select { min-width: 132px; }\n', '')
rep('.sheet input[type="text"]:focus-visible, .sheet select:focus-visible {', '''.sheet select { min-width: 108px; }
.sheet textarea { display: block; width: 100%; min-height: 36px; border: 0; background: none; font: inherit; line-height: 1.35; color: inherit; padding: 8px 9px; border-radius: 0; resize: none; overflow: hidden; }
.sheet.fit { table-layout: fixed; width: 100%; min-width: 540px; }
.sheet.fit select { min-width: 0; padding: 0 4px 0 7px; }
.sheet.fit thead th { padding: 6px 7px; }
.sheet input[type="text"]:focus-visible, .sheet select:focus-visible, .sheet textarea:focus-visible {''')
rep('.sheet td.num { width: 110px; }', '.sheet td.num { width: 80px; }\n.sheet td.calc .hint { display: inline-block; white-space: normal; line-height: 1.15; font-size: 12px; color: var(--ink2); padding: 3px 0; }')
rep('.sheet tr.hit td { background: var(--mark); }', '.sheet tr.hit td { background: var(--mark); }\n.sheet tr.hit td.rn { color: var(--ink); }')
rep('.bar.wide > span:first-child { display: flex; gap: 6px; align-items: center; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }', '.bar.wide > span:first-child { display: flex; gap: 6px; align-items: center; line-height: 1.2; overflow-wrap: anywhere; }')
rep('.sheet td:nth-child(2) input[type="text"] { min-width: 200px; }', '#suprows td:nth-child(2) input[type="text"] { min-width: 215px; }')
rep('button.mapfoot { cursor: pointer; text-align: left; line-height: 1.5; }', '''button.mapfoot { cursor: pointer; text-align: left; line-height: 1.5; }
.chartscroll { overflow-x: auto; }
.facts.coords { font-family: var(--mono); font-size: 13px; grid-template-columns: minmax(0, 1fr); gap: 1px; } .facts.coords dt { font-family: var(--body); } .facts.coords dd { white-space: nowrap; margin-bottom: 7px; }
.rowitem.off { color: var(--ink2); }
.idea .more { color: var(--ink2); font-size: 12.5px; white-space: nowrap; }
.toast { position: absolute; left: 50%; bottom: 18px; transform: translateX(-50%); z-index: 6; background: var(--ink); color: var(--paper); border-radius: 8px; padding: 9px 15px; font-weight: 600; font-size: 14px; white-space: nowrap; box-shadow: 0 10px 30px -12px rgba(0, 0, 0, .6); }
.toast[hidden] { display: none; }''')
rep('''.topbar, .tabbar { display: none; }
@container app (max-width: 640px) {''', '''.topbar, .tabbar { display: none; }
@container app (max-width: 900px) { .maptools .btn span { display: none; } }
@container app (max-width: 960px) {
  .split, .split.plan { grid-template-columns: minmax(0, 1fr); }
  .split .list { display: none; border-right: 0; } .split.show-list .list { display: flex; } .split.show-list .detail { display: none; }
  .phone-only { display: inline-flex; }
  .rowitem.idea { flex-wrap: wrap; } .idea .more { flex-basis: 100%; padding-left: 36px; white-space: normal; text-decoration: underline; text-underline-offset: 3px; } .rowitem.idea > .ic { display: none; }
}
@container app (max-width: 640px) {''')
rep("  .topbar .sos-btn { min-height: 40px; } .topbar .sos-btn .kbd,", "  .topbar .sos-btn { min-height: 40px; padding: 0 9px; gap: 7px; font-size: 12.5px; line-height: 1.1; max-width: 136px; } .topbar .sos-btn .kbd,")
rep('  .split { grid-template-columns: minmax(0, 1fr); }\n', '')
rep('  .split .detail { padding: 18px 16px 28px; }', '  .split .detail, .split.plan .detail { padding: 18px 16px 28px; }')
rep('''  .maptools .btn span { display: none; }
}''', '''  .maptop { flex-wrap: wrap; } .mapsearch { flex: 1 1 100%; max-width: none; }
  .drawer { top: auto; left: 12px; right: 12px; bottom: 12px; width: auto; max-height: 58%; }
  .mapfoot { max-width: calc(100% - 24px); } .mapbox.has-drawer .mapfoot { display: none; }
  .toast { bottom: 68px; }
}''')

# ---------------- markup ----------------
rep('''            </div>
          </div>
        </div>
      </div>
    </div>
    <aside class="notes"''', '''            </div>
          </div>
          <div class="toast" id="toast" role="status" hidden></div>
        </div>
      </div>
    </div>
    <aside class="notes"''')

# ---------------- data and copy ----------------
rep('["Bung thread", "2 inch coarse"], ["Spare parts", "Bung wrench and 2 gaskets, garage shelf"]', '["Cap thread", "2 inch coarse"], ["Spare parts", "Cap wrench and 2 gaskets, garage shelf"]')
rep('["Walk time", "About 15 minutes"]', '["Walk time", "About 12 minutes"]')
rep('["s8", "Write the start time in the incident log"]', '["s8", "Write down the time the power went out"]')
rep('hist: [], menu: false, mapEmpty: false, drawer: "layers",', 'hist: [], menu: false, mapEmpty: false, mapq: "", wikiq: "", backed: false, drawer: "layers",')
rep('''`${u.zone}${u.band} ${Math.round(u.E)}E ${Math.round(u.N)}N`], ["USNG, for rescue and radio",''', '''`${u.zone}${u.band} ${Math.floor(u.E)}E ${Math.floor(u.N)}N`], ["USNG (US National Grid), for rescue and radio",''')
rep('''const coordHTML = ll => `<dl class="facts" style="font-family:var(--mono);font-size:13px">${coordLines(ll[0], ll[1]).map(c => `<dt style="font-family:var(--body)">${c[0]}</dt><dd>${c[1]}</dd>`).join("")}</dl>`;''',
    '''const coordHTML = ll => `<dl class="facts coords">${coordLines(ll[0], ll[1]).map(c => `<dt>${c[0]}</dt><dd>${c[1]}</dd>`).join("")}</dl>`;''')

# moon phases (true new and full moons, Meeus main terms)
rep('function utm(lat, lon) {', '''const SYNODIC = 29.530588861 * 864e5;
function moonAt(k) {
  const T = k / 1236.85, E = 1 - 0.002516 * T, M = (2.5534 + 29.1053567 * k) * D2R, Mp = (201.5643 + 385.81693528 * k) * D2R, F = (160.7108 + 390.67050284 * k) * D2R, full = k % 1 !== 0;
  const c = full ? -0.40614 * Math.sin(Mp) + 0.17302 * E * Math.sin(M) + 0.01614 * Math.sin(2 * Mp) + 0.01043 * Math.sin(2 * F) + 0.00734 * E * Math.sin(Mp - M) - 0.00515 * E * Math.sin(Mp + M)
    : -0.4072 * Math.sin(Mp) + 0.17241 * E * Math.sin(M) + 0.01608 * Math.sin(2 * Mp) + 0.01039 * Math.sin(2 * F) + 0.00739 * E * Math.sin(Mp - M) - 0.00514 * E * Math.sin(Mp + M);
  return (2451550.09766 + 29.530588861 * k + 0.00015437 * T * T + c - 2440587.5) * 864e5 - 7e4;
}
function lastNew(ms) { let k = Math.floor((ms - Date.UTC(2000, 0, 6, 18, 14)) / SYNODIC) + 1; while (moonAt(k) > ms) k--; return k; }
function utm(lat, lon) {''')

# supplies
rep('''const fmtD = d => (d >= 10 ? Math.round(d) : Math.round(d * 10) / 10) + (d === 1 ? " day" : " days");''',
    '''const fmtD = d => { const v = d >= 10 ? Math.round(d) : Math.round(d * 10) / 10; return v + (v === 1 ? " day" : " days"); };
const badNum = r => ["qty", "use"].some(f => { const s = String(r[f] || "").trim(); return s && !(parseFloat(s) >= 0); });''')
rep('''<span class="days">${d != null ? fmtD(d) : "no rate"}</span></div>`; }).join("")}</div><p class="fine">The black line is 14 days. Scale runs 0 to 21.</p>''',
    '''<span class="days">${d != null ? fmtD(d) : badNum(r) ? "check" : "no rate"}</span></div>`; }).join("")}</div><p class="fine">The line across each bar is 14 days. Scale runs 0 to 21.</p>''')
rep('''const daysCell = r => { const d = daysOf(r); return d != null ? fmtD(d) : `<span style="color:var(--ink2)">add use per day</span>`; };''',
    '''const daysCell = r => { const d = daysOf(r); return badNum(r) ? `<span style="color:var(--low)">check the number</span>` : d != null ? fmtD(d) : `<span class="hint">add use per day</span>`; };''')
rep('''function addSup(name, guess) {
  name = (name || "").trim(); if (!name) return;
  const low = name.toLowerCase(), free = x => !SUP.some(r => r.item.toLowerCase() === x[0].toLowerCase());
  const c = COMMON.find(x => x[0].toLowerCase() === low) || (guess ? COMMON.find(x => x[0].toLowerCase().includes(low) && free(x)) : null);
  const row = { id: "u" + Date.now().toString(36), item: c ? c[0] : name, cat: c ? c[1] : "Gear", qty: "", unit: c ? c[2] : "", use: "" };
  SUP.push(row); store.set("fb-sup", SUP); S.supq = ""; render(true); const e = document.getElementById("c-" + row.id + "-qty"); if (e) e.focus();
}''', '''const KIND = [[/water|bleach|filter|purif/, "Water"], [/rice|bean|food|\\bcans?\\b|canned|flour|oat|pasta|meal|sugar|salt|milk|honey|soup|tuna|cereal/, "Food"], [/propane|gasoline|\\bgas\\b|fuel|kerosene|diesel|solar|charger|generator/, "Power"], [/bandage|medic|first aid|gauze|aspirin|ibuprofen|pain|antibiotic|insulin|inhaler|ointment|thermometer/, "Medical"]];
function addSup(name, guess) {
  name = (name || "").trim(); if (!name) return;
  const low = name.toLowerCase(), free = x => !SUP.some(r => r.item.toLowerCase() === x[0].toLowerCase());
  const focus = id => { const e = document.getElementById("c-" + id + "-qty"); if (e) e.focus(); };
  const same = SUP.find(r => r.item.trim().toLowerCase() === low);
  if (same) { S.supq = ""; render(true); return focus(same.id); }
  const c = COMMON.find(x => x[0].toLowerCase() === low) || (guess ? COMMON.find(x => x[0].toLowerCase().includes(low) && free(x)) : null);
  const row = { id: "u" + Date.now().toString(36), item: c ? c[0] : name[0].toUpperCase() + name.slice(1), cat: c ? c[1] : (KIND.find(k => k[0].test(low)) || [0, "Gear"])[1], qty: "", unit: c ? c[2] : "", use: "" };
  SUP.push(row); store.set("fb-sup", SUP); S.supq = ""; render(true); focus(row.id);
}''')

# ---------------- search ----------------
rep('"a an the to of how do i my what is for in on and with when it if can we you me"', '"a an the to of how do i my what is for in on and with when it if can we you me no not much many per does long will should there where has have wont cant dont are am was too very really so"')
rep('''    if (w.endsWith("es") && !w.endsWith("ses")) return w.slice(0, -2);
''', '''    if (/(sses|xes|zes|ches|shes)$/.test(w)) return w.slice(0, -2);
''')
rep('cold: ["freeze", "winter"], snow: ["winter", "freeze"], ice: ["freeze", "winter"],', 'cold: ["freeze", "freez", "winter"], snow: ["winter", "freeze"], ice: ["freeze", "winter"], frozen: ["freeze", "freez"], storage: ["stor", "store"], scald: ["burn"], heatstroke: ["heat", "stroke"], torch: ["flashlight"], toddler: ["children", "child"],\n  chok: ["throat"], choke: ["throat"], heimlich: ["throat"], temperature: ["fever"], dehydration: ["rehydration"], er: ["hospital"], clinic: ["hospital"], doctor: ["hospital"],')
rep('''  if (q.length >= 4) { const max = q.length >= 8 ? 2 : 1; for (const t of set) if (t.length >= 4 && lev(q, t, max) <= max) return { s: .6, tok: t, fix: t }; }
  return null;
}
const DOCS = [];
const addDoc = (type, title, body, o) => DOCS.push(Object.assign({ type, title, body, T: new Set(toks(title)), B: new Set(toks(body)), K: new Set(toks(o.kw || "")), w: 1 }, o));''',
'''  /* typo fixing: only for a word that is in no document, and only close misses that keep the first letter */
  if (q.length >= 4 && !VOCAB.has(q)) { const max = q.length >= 8 ? 2 : 1; for (const t of set) {
    if (t[0] !== q[0] || t.length < 4) continue;
    const swap = t.length === q.length && [...q].some((c, i) => i < q.length - 1 && q.slice(0, i) + q[i + 1] + c + q.slice(i + 2) === t);
    const near = q.length >= 5 && t.length >= 5 && !(t.length === q.length && q.length < 6) && lev(q, t, max) <= max;
    if (swap || near) return { s: .6, tok: t, fix: q.startsWith(t) ? null : t };
  } }
  return null;
}
const DOCS = [], VOCAB = new Set();
const addDoc = (type, title, body, o) => { const d = Object.assign({ type, title, body, T: new Set(toks(title)), B: new Set(toks(body)), K: new Set(toks(o.kw || "")), w: 1 }, o); [d.T, d.B, d.K].forEach(s => s.forEach(t => VOCAB.add(t))); DOCS.push(d); };''')
rep(''', ["Start a new checklist", "new plan create list template", "plan", "plus"], ["Print the rescue card", "print rescue card location", "emergency:hurt", "print"]].forEach''',
    ''', ["Start a new checklist", "new plan create list template", "plan", "plus"], ["Something happening", "help emergency 911 sos urgent danger mayday", "emergency:power:menu", "alert"], ["Nearest shelter or hospital", "hospital shelter nearest near me closest clinic", "map:near", "near"]].forEach''')
rep('''function search(q, filter) {
  const qt =''', '''function search(q, filter) {
  q = String(q).toLowerCase().replace(/\\b(no|without|lost) (the )?heat(ing|er)?\\b|\\bheat(ing|er)? (is |went )?(out|off|broke|broken|down)\\b/g, "freeze");
  const qt =''')
rep('if (miss && !(qt.length >= 3 && miss === 1)) continue;', 'if (miss && !(qt.length >= 2 && miss === 1)) continue;')
rep('* (miss ? .5 : 1);', '* (miss ? (qt.length >= 3 ? .55 : .35) : 1);')
rep('let recent = ["barrel bung thread", "boil water"];', 'let recent = ["barrel cap thread", "boil water"];')
rep('''<button class="res" data-n="${n++}" data-route="map" style="--c:var(--b-map)">''', '''<button class="res" data-n="${n++}" data-route="map" data-hand="map" style="--c:var(--b-map)">''')
rep('''<button class="res" data-n="${n++}" data-route="learn" style="--c:var(--b-learn)">''', '''<button class="res" data-n="${n++}" data-route="learn" data-hand="wiki" style="--c:var(--b-learn)">''')
rep('''  closePal(); go(b.dataset.route);
}''', '''  closePal(); go(b.dataset.route);
  if (b.dataset.hand === "map") { S.mapq = q; S.drawer = "search"; render(); }
  if (b.dataset.hand === "wiki") { S.wikiq = q; render(); }
}''')
rep('''  Object.assign(S, { screen, arg, arg2, menu: false, listOpen: false });
  if (screen === "map" && arg) S.drawer = arg;''', '''  Object.assign(S, { screen, arg, arg2, menu: screen === "emergency" && arg2 === "menu", listOpen: false, mapq: "", wikiq: "" });
  if (screen === "map" && arg) S.drawer = arg; else if (S.drawer === "search") S.drawer = "";''')

# ---------------- screens ----------------
rep('<p class="fine">The black line is the 2-week goal. Scale runs 0 to 21 days.</p>', '<p class="fine">The line across each bar is the 2-week goal. Scale runs 0 to 21 days.</p>')
rep('''    const m = search(s.title + " " + s.kw.split(" ")[0], "manual").hits[0] || search(s.title, "manual").hits[0];''',
    '''    const m = PASS.find(p => p.id === ({ power: "m0", tornado: "m20", flood: "m17", heat: "m8", freeze: "m11", water: "m5", hurt: "m6", earthquake: "m21" })[s.id]);''')
rep('''${m ? `<button class="quote" data-route="${m.d.route}" style="text-align:left;background:none"><span class="eyebrow">From the manuals</span><span>${esc(snip(m.d.body, m.used))}</span><span class="src">${esc(m.d.pass.doc)} · page ${m.d.pass.p}</span></button>` : ""}''',
    '''${m ? `<button class="quote" data-route="learn:read:${m.id}" style="text-align:left;background:none"><span class="eyebrow">From the manuals</span><span>${(x => esc(x.split(" ").slice(0, 34).join(" ")) + (x.split(" ").length > 34 ? "…" : ""))(/^[a-z]/.test(m.x) ? m.x.slice(m.x.indexOf(". ") + 2) : m.x)}</span><span class="src">${esc(m.doc)} · page ${m.p}</span></button>` : ""}''')
rep('''      <p class="fine">The emergency steps, the manuals and your records all work without a map.</p></section></div></div>`;
    const d = S.drawer;
    return `<div class="mapbox"><canvas''', '''      ${S.mapq ? `<p class="sub">Your search for “${esc(S.mapq)}” needs a map first.</p>` : ""}
      <p class="fine">The emergency steps, the manuals and your records all work without a map.</p></section></div></div>`;
    const d = S.drawer, dh = (k, t) => `<div class="dhead"><h3>${t}</h3><button class="xbtn" data-act="drawer:${k}" aria-label="Close this panel">${ic("x", 16)}</button></div>`;
    return `<div class="mapbox${d ? " has-drawer" : ""}"><canvas''')
rep('''<input id="mapq" type="text" placeholder="Search the map" aria-label="Search the map">''', '''<input id="mapq" type="text" value="${esc(S.mapq)}" placeholder="Search the map" aria-label="Search the map">''')
rep('''${d === "layers" ? `<div class="drawer"><h3>Layers</h3>${[["Your pins", "var(--signal)", 1], ["Water sources", "var(--map-water)", 1], ["Shelters", "var(--b-plan)", 1], ["Hospitals", "var(--low)", 0], ["Rail lines", "var(--ink)", 1], ["Old rail lines", "var(--ink2)", 0], ["Hill shading", "var(--map-line)", 1]].map((l, i) => `<label><input type="checkbox" id="ly${i}" ${l[2] ? "checked" : ""}><i class="swatch" style="background:${l[1]}"></i>${l[0]}</label>`).join("")}<p class="fine">Layers that are not in your pack are listed as missing, with a button to get them.</p></div>` : ""}''',
    '''${d === "layers" ? `<div class="drawer">${dh("layers", "Layers")}${[["Your pins", "var(--signal)", 1], ["Water sources", "var(--map-water)", 1], ["Shelters", "var(--b-plan)", 1], ["Hospitals", "var(--low)", 0], ["Rail lines", "var(--ink)", 1], ["Old rail lines", "var(--ink2)", -1], ["Hill shading", "var(--map-line)", 1]].map((l, i) => l[2] < 0 ? `<label class="miss"><input type="checkbox" id="ly${i}" disabled><i class="swatch" style="background:${l[1]}"></i>${l[0]}, missing <button class="linkbtn" data-route="setup">Get it</button></label>` : `<label><input type="checkbox" id="ly${i}" ${l[2] ? "checked" : ""}><i class="swatch" style="background:${l[1]}"></i>${l[0]}</label>`).join("")}<p class="fine">A layer that is not in your map is marked missing, with a link to get it.</p></div>` : ""}''')
rep('''${d === "near" ? `<div class="drawer"><h3>Near me</h3>''', '''${d === "near" ? `<div class="drawer">${dh("near", "Near me")}''')
rep('["Meeting point", "0.8 mi south", "flag"]', '["Meeting point", "0.5 mi south", "flag"]')
rep('''${d === "tools" ? `<div class="drawer"><h3>Measure</h3>''', '''${d === "tools" ? `<div class="drawer">${dh("tools", "Measure")}''')
rep('''      <button class="mapfoot" data-act="ll">''', '''      ${d === "search" ? `<div class="drawer">${dh("search", "Map search")}<p class="sub">You searched the map for “${esc(S.mapq)}”.</p><p class="fine">Not in this mock-up yet. The real app lists the towns, pins, water, shelters and hospitals that match.</p></div>` : ""}
      <button class="mapfoot" data-act="ll">''')
rep('"Show coordinates · drawing only, the real app shows your state pack here"', '"Show coordinates · drawing only, the real app shows your state map here"')
rep('Add the survival layers: water, shelters, hospitals, rail lines</label>', 'Add the survival layers: water, shelters, hospitals, rail lines, old rail lines</label>')
rep('''    return `<div class="head"><div><h1>Learn</h1><p class="sub">Start from the question you have. Everything listed is already on this Mac.</p></div><button class="btn" data-act="pal">${ic("search", 16)}Search inside the manuals</button></div>
''', '''    return `<div class="head"><div><h1>Learn</h1><p class="sub">Start from the question you have. Everything listed is already on this Mac.</p></div><button class="btn" data-act="pal">${ic("search", 16)}Search inside the manuals</button></div>
    ${S.wikiq ? `<section class="panel"><p class="eyebrow">Wiki library</p><h3>You searched the wiki library for “${esc(S.wikiq)}”</h3><p class="fine">Not in this mock-up yet. The real app opens the wiki library with this search already typed in.</p></section>` : ""}
''')
rep('''return `<button class="rowitem" data-route="${p ? "learn:read:" + p.id : "learn:" + t[0]}">${ic("book")}<span class="grow">${esc(name)}<small>${n ? n.toLocaleString() + " sections · " : ""}opens on this Mac</small></span>${ic("arrow", 16)}</button>`; }).join("")}</div></section>''',
    '''return p ? `<button class="rowitem" data-route="learn:read:${p.id}">${ic("book")}<span class="grow">${esc(name)}<small>${n ? n.toLocaleString() + " sections · " : ""}opens on this Mac</small></span>${ic("arrow", 16)}</button>` : `<div class="rowitem off">${ic("book")}<span class="grow">${esc(name)}<small>${n ? n.toLocaleString() + " sections · " : ""}not in this mock-up</small></span></div>`; }).join("")}</div>
        <p class="fine">In the real app every manual opens. This mock-up carries sample pages from some of them.</p></section>''')

# plan sheet
rep('''    const whenOf = s =>''', '''    const ta = (id, f, def) => `<textarea rows="1" id="c-${id}-${f}" data-cell="${id}:${f}" aria-label="${f}">${esc(cell(id, f, def))}</textarea>`;
    const whenOf = s =>''')
rep('''<div class="sheetbox"><table class="sheet"><thead><tr><th></th><th>Person</th><th>Phone</th><th>Where they would be</th><th>Check-in time</th></tr></thead>''',
    '''<div class="sheetbox"><table class="sheet fit"><thead><tr><th style="width:28px"></th><th style="width:23%">Person</th><th style="width:23%">Phone</th><th>Where they would be</th><th style="width:84px">Check-in</th></tr></thead>''')
rep('''<div class="sheetbox"><table class="sheet"><thead><tr><th></th><th>Done</th><th>Step</th>${timed ? "<th>When</th>" : ""}<th>Who</th><th>What you need</th></tr></thead>''',
    '''<div class="sheetbox"><table class="sheet fit"><thead><tr><th style="width:28px"></th><th style="width:48px">Done</th><th>Step</th>${timed ? `<th style="width:108px">When</th>` : ""}<th style="width:78px">Who</th><th style="width:${timed ? 116 : 150}px">What you need</th></tr></thead>''')
rep('''<td style="min-width:260px">${ci(s[0], "text", s[1])}</td>''', '''<td>${ta(s[0], "text", s[1])}</td>''')
rep('''<td>${ci(s[0], "who", "", "Anyone")}</td><td>${ci(s[0], "need")}</td></tr>''', '''<td>${ci(s[0], "who", "", "Anyone")}</td><td>${ta(s[0], "need")}</td></tr>''')
rep('''    return `<div class="split${S.listOpen ? " show-list" : ""}">
      <div class="list"><button class="btn pri" data-act="noop">${ic("plus", 16)}New checklist</button>''', '''    return `<div class="split plan${S.listOpen ? " show-list" : ""}">
      <div class="list"><button class="btn pri" data-act="noop">${ic("plus", 16)}New checklist</button>''')

# sun: moon
rep('''    const P = 29.530588, ageAt = ms => (((ms - Date.UTC(2000, 0, 6, 18, 14)) / 864e5) % P + P) % P, age = ageAt(+now), c = Math.cos(2 * Math.PI * age / P), wax = age < P / 2;''',
    '''    const k0 = lastNew(+now), new0 = moonAt(k0), P = (moonAt(k0 + 1) - new0) / 864e5, age = (now - new0) / 864e5, c = Math.cos(2 * Math.PI * age / P), wax = age < P / 2;''')
rep('''    for (let d = 1; d <= dim; d++) { const q = sunAt(cy, cm, d, lat, lon), ag = ageAt(Date.UTC(cy, cm, d, 18)), due = DUE.filter(x => x[0] === cy && x[1] === cm && x[2] === d);''',
    '''    const ymd = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" }), MOONS = {}, kc = lastNew(Date.UTC(cy, cm, 1));
    for (let j = -1; j <= 2.5; j += .5) MOONS[ymd.format(moonAt(kc + j))] = j % 1 ? "Full moon" : "New moon";
    for (let d = 1; d <= dim; d++) { const q = sunAt(cy, cm, d, lat, lon), mn = MOONS[cy + "-" + String(cm + 1).padStart(2, "0") + "-" + String(d).padStart(2, "0")], due = DUE.filter(x => x[0] === cy && x[1] === cm && x[2] === d);''')
rep('''${ag < 1 ? `<span class="moon">New moon</span>` : Math.abs(ag - P / 2) < .5 ? `<span class="moon">Full moon</span>` : ""}''', '''${mn ? `<span class="moon">${mn}</span>` : ""}''')
rep('''      <svg class="chart" viewBox="0 0 640 222" role="img" aria-label="Sunrise and sunset times across the year">''', '''      <div class="chartscroll"><svg class="chart" style="min-width:540px" viewBox="0 0 640 222" role="img" aria-label="Sunrise and sunset times across the year">''')
rep('''style="fill:var(--ink)">today</text></svg>
      <p class="fine">The colored band''', '''style="fill:var(--ink)">today</text></svg></div>
      <p class="fine">The colored band''')

# earth: winter label above its own sun, summer label beside
rep('''<text x="${(sx + 15).toFixed(0)}" y="${(ly ? sy + 4 : sy - 8).toFixed(0)}" text-anchor="start" style="fill:var(--ink)">''', '''<text x="${(ly ? sx + 15 : Math.max(sx, 56)).toFixed(0)}" y="${(ly ? sy + 4 : sy - 16).toFixed(0)}" text-anchor="${ly ? "start" : "middle"}" style="fill:var(--ink)">''')
rep('''<button class="rowitem" data-route="${x[2]}"><span class="badge">${i + 1}</span><span class="grow"><b>${x[0]}</b><small>${x[1]}</small></span><span class="fine" style="white-space:nowrap">${x[3]}</span>''',
    '''<button class="rowitem idea" data-route="${x[2]}"><span class="badge">${i + 1}</span><span class="grow"><b>${x[0]}</b><small>${x[1]}</small></span><span class="more">${x[3]}</span>''')

# readiness check
rep('''    const rows = [["Map of Texas opens", "Standard detail, a real tile was read", "ok", "Ready"], ["Hill shading", "Read from the pack", "ok", "Ready"], ["Survival layers", "4 of 5 found. Rail lines are missing.", "low", "Missing", "Get the layer", "setup"],
      ["Manuals", "18 manuals opened, 1 page each", "ok", "Ready"], ["Wiki library", "The reader started and answered", "ok", "Ready"], ["Your records", "9 records read", "ok", "Ready"], ["Backup", "Last backup was 23 days ago", "due", "Due", "Back up now", ""]];''',
    '''    const rows = (S.mapEmpty ? [["Map", "No map on this Mac yet", "low", "Missing", "Get a map", "setup"]] : [["Map of Texas opens", "Standard detail. One piece of the map was opened to be sure.", "ok", "Ready"], ["Hill shading", "Opened from the map files", "ok", "Ready"], ["Survival layers", "4 of 5 found. Old rail lines are missing.", "low", "Missing", "Get the layer", "setup"]]).concat([
      ["Manuals", "18 manuals opened, 1 page each", "ok", "Ready"], ["Wiki library", "The reader started and answered", "ok", "Ready"], ["Your records", "9 records read", "ok", "Ready"], S.backed ? ["Backup", "Backed up just now (example)", "ok", "Ready"] : ["Backup", "Last backup was 23 days ago", "due", "Due", "Back up now", "act:backup"]]);''')
rep('''(r[4] ? `<button class="btn" data-route="${r[5] || "check"}">${r[4]}</button>` : "")''', '''(r[4] ? `<button class="btn" ${r[5].startsWith("act:") ? `data-act="${r[5].slice(4)}"` : `data-route="${r[5]}"`}>${r[4]}</button>` : "")''')

# notes
rep('"The pack name sits on the map, so you know which state and detail level you are looking at."', '"The state and detail level sit on the map, so you know what you are looking at."')

# render
rep('''<div class="state"><i></i>Offline ready · Texas map</div></div>`;''', '''<div class="state${S.mapEmpty ? " warn" : ""}"><i></i>${S.mapEmpty ? "No map yet · manuals ready" : "Offline ready · Texas map"}</div></div>`;''')
rep('''aria-label="Something happening">${ic("alert")}<span>Help</span></button>`;''', '''aria-label="Something happening">${ic("alert")}<span>Something happening?</span></button>`;''')
rep('''  if (S.screen === "map" && !S.mapEmpty) drawMap();
  noteKey''', '''  if (S.screen === "map" && !S.mapEmpty) drawMap();
  fitTA();
  noteKey''')
rep('''function drawNotes() {''', '''function fitTA() { document.querySelectorAll(".sheet textarea").forEach(e => { e.style.height = "auto"; e.style.height = e.scrollHeight + "px"; }); }
let toastT = 0;
function toast(msg) { const e = $("#toast"); e.textContent = msg; e.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { e.hidden = true; }, 2200); }
function drawNotes() {''')

# events
rep('''closest("[data-strip],[data-device],[data-try],[data-addsup],[data-delsup],[data-route],[data-act],[data-filter],[data-state],[data-level],[data-dest]")''', '''closest("[data-strip],[data-device],[data-try],[data-addsup],[data-delsup],[data-route],[data-act],[data-filter],[data-state],[data-level],[data-dest],[data-q]")''')
rep('''  if (a === "pal") { openPal(""); noteKey = "search"; return drawNotes(); }
  if (a === "back") return back();''', '''  if (a === "pal") { openPal(""); noteKey = "search"; return drawNotes(); }
  if (a === "noop") return toast("Not in this mock-up yet");
  if (a === "backup") { S.backed = true; render(true); return toast("Backed up (example)"); }
  if (a === "back") return back();''')
rep('''  if (t.dataset.cell) { cells[t.dataset.cell] = t.value; store.set("fb-cells", cells); }''', '''  if (t.dataset.cell) { cells[t.dataset.cell] = t.value; store.set("fb-cells", cells); if (t.tagName === "TEXTAREA") fitTA(); }''')
rep('''  if (e.target.id === "supq" && e.key === "Enter") { e.preventDefault(); return addSup(e.target.value, true); }''', '''  if (e.target.id === "supq" && e.key === "Enter") { e.preventDefault(); return addSup(e.target.value, true); }
  if (e.target.id === "mapq" && e.key === "Enter") { e.preventDefault(); S.mapq = e.target.value.trim(); S.drawer = S.mapq ? "search" : ""; return render(); }
  if (e.target.tagName === "TEXTAREA" && e.key === "Enter") return e.preventDefault();''')
rep('''addEventListener("resize", () => drawMap());''', '''addEventListener("resize", () => { drawMap(); fitTA(); });''')
rep('''document.fonts.ready.then(() => drawMap());''', '''document.fonts.ready.then(() => { drawMap(); fitTA(); });''')

rep('["Run the readiness check", "offline test ready works", "check", "shield"]', '["Run the readiness check", "offline test ready works backup back up", "check", "shield"]')
rep('PASS.forEach(p => addDoc("manual", p.h || p.doc, p.x, { route:', 'PASS.forEach(p => addDoc("manual", p.h || p.doc, p.x, { kw: p.kw || "", route:')
assert '—' not in src
open(path, 'w').write(src)
print('patched', len(src))
