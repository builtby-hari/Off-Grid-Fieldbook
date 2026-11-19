// The shell hands a command to a screen by putting it in that screen's address.
// The map reads it with URLSearchParams. This checks both ends agree, for every command the app sends.
const ok = (c, m) => { console.log((c ? "PASS " : "FAIL ") + m); if (!c) process.exitCode = 1; };
const send = rest => encodeURI(rest);                               // what the shell writes after the #
const mapReads = hash => new URLSearchParams(hash);                 // what the map does with it
const screenReads = hash => decodeURIComponent(hash);               // what UI.onRoute does with it

ok(mapReads(send("pick=mabc123")).get("pick") === "mabc123", "pick a location: the map gets the record id");
ok(mapReads(send("fly=-104.99,39.74")).get("fly") === "-104.99,39.74", "show on map: the map gets the point");
ok(mapReads(send("q=fire station")).get("q") === "fire station", "map search: the map gets the words, spaces and all");
ok(screenReads(send("r=mabc123")) === "r=mabc123", "open a record in My Place");
ok(screenReads(send("usda-canning?page=12")) === "usda-canning?page=12", "open a manual at a page");
ok(screenReads(send("plants?q=wild onion")) === "plants?q=wild onion", "plant search with a space");
ok(mapReads(encodeURIComponent("pick=mabc123")).get("pick") === null, "the old way of encoding really was broken (guards against going back)");
