// Checks gallonsOf (app/web/place.html): the unit conversion behind the water "What you have" figure.
const vm = require("vm"), fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "../app/web/place.html"), "utf8");
const m = /function gallonsOf\([^)]*\)\s*\{[\s\S]*?\n\}/.exec(html);
if (!m) { console.log("FAIL gallonsOf is found in app/web/place.html"); process.exit(1); }
const gallonsOf = vm.runInNewContext(m[0] + ";gallonsOf", {});
let failed = 0;
const check = (ok, msg) => { console.log((ok ? "PASS " : "FAIL ") + msg); if (!ok) failed++; };
const near = (a, b, tol) => a !== null && Math.abs(a - b) <= tol;
check(gallonsOf(24, "bottles") === null, "24 bottles is not a volume (null)");
check(gallonsOf(5, "gal") === 5, "5 gal is 5 gallons");
check(near(gallonsOf(10, "liters"), 2.64, 0.01), "10 liters is about 2.64 gallons (got " + gallonsOf(10, "liters") + ")");
check(gallonsOf(8, "qt") === 2, "8 qt is 2 gallons");
check(gallonsOf(128, "fl oz") === 1, "128 fl oz is 1 gallon");
check(gallonsOf(5, "") === null, "blank unit is not a volume (null)");
process.exitCode = failed ? 1 : 0;
