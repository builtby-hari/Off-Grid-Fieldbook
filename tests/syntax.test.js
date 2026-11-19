// Every screen's script must at least parse. A screen with a syntax error shows a blank page,
// so this is the cheapest test there is and it runs on every screen.
const fs = require("fs"), path = require("path"), vm = require("vm");
const root = path.join(__dirname, "..");
const files = fs.readdirSync(path.join(root, "app/web")).filter(f => f.endsWith(".html")).map(f => "app/web/" + f).concat(["app/web/map/index.html"]);
const shared = ["app/web/og.js", "app/web/ui.js", "app/web/md.js"];
let bad = 0;
const check = (name, code) => { try { new vm.Script(code, { filename: name }); console.log("PASS " + name + " parses"); } catch (e) { bad++; console.log("FAIL " + name + ": " + e.message); } };
for (const f of files) {
  const html = fs.readFileSync(path.join(root, f), "utf8");
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  if (!scripts.length) { bad++; console.log("FAIL " + f + ": no script found"); continue; }
  scripts.forEach((code, i) => check(f + (scripts.length > 1 ? " #" + (i + 1) : ""), code));
}
for (const f of shared) check(f, fs.readFileSync(path.join(root, f), "utf8"));
for (const f of ["app/web/data/scenarios.json", "content/library/pdf-catalog.json", "tools/packs/regions.json"]) {
  try { JSON.parse(fs.readFileSync(path.join(root, f), "utf8")); console.log("PASS " + f + " is valid JSON"); } catch (e) { bad++; console.log("FAIL " + f + ": " + e.message); }
}
process.exitCode = bad ? 1 : 0;
