// Off-Grid shared UI helpers. Every screen loads this after og.js.
// Holds: DOM helpers, the theme (shared by the shell and every screen), toasts, safe fetch,
// and the one way a screen asks the shell to go somewhere. See CONTRACT.md.
"use strict";
const UI = (() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const el = (tag, props = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) k === "class" ? n.className = v : k.startsWith("on") ? n.addEventListener(k.slice(2), v) : k in n ? n[k] = v : n.setAttribute(k, v);
    n.append(...kids.filter(x => x != null));
    return n;
  };
  const store = {
    get(k, d = null) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  };
  const debounce = (fn, ms = 200) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
  const reRegex = s => String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  // ----- theme: one setting, read by every screen, changed live when the shell toggles it -----
  function applyTheme() {
    let t = null; try { t = localStorage.getItem("theme"); } catch {}
    if (t === "light" || t === "dark") document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
  }
  function toggleTheme() {
    const dark = matchMedia("(prefers-color-scheme: dark)").matches;
    const cur = document.documentElement.dataset.theme || (dark ? "dark" : "light");
    try { localStorage.setItem("theme", cur === "dark" ? "light" : "dark"); } catch {}
    applyTheme();
  }
  applyTheme();
  addEventListener("storage", e => { if (e.key === "theme") applyTheme(); });

  // ----- toast -----
  let toastEl, toastT;
  function toast(msg = "Saved", bad = false) {
    if (!toastEl) { toastEl = el("div", { class: "toast", role: "status" }); toastEl.setAttribute("aria-live", "polite"); document.body.append(toastEl); }
    toastEl.textContent = msg; toastEl.className = "toast on" + (bad ? " bad" : "");
    clearTimeout(toastT); toastT = setTimeout(() => toastEl.className = "toast", bad ? 4000 : 1400);
  }

  // ----- fetch that tells you what went wrong -----
  async function getJSON(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(url + " is not in this copy (" + r.status + ")");
    return r.json();
  }
  async function getText(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(url + " is not in this copy (" + r.status + ")");
    return r.text();
  }
  async function exists(url) { try { return (await fetch(url, { method: "HEAD" })).ok; } catch { return false; } }

  // ----- navigation: a screen never touches another screen. It asks the shell. -----
  // route examples: "home/power", "map?fly=-104.99,39.74", "place/r=abc", "learn/texas-rainwater-manual/storage-tanks"
  const inShell = () => parent !== window;
  function go(route) {
    route = String(route).replace(/^#/, "");
    if (inShell()) parent.postMessage({ og: "go", route }, location.origin); else location.hash = route;
  }
  // The shell tells a screen its sub-route by setting the frame's hash. Call onRoute once per screen.
  function onRoute(fn) {
    const run = () => { try { fn(decodeURIComponent(location.hash.slice(1))); } catch (e) { console.error(e); } };
    addEventListener("hashchange", run); run();
  }
  // Send a message to the shell (pickLocation, showOnMap, ...). Always same-origin.
  const tell = msg => { if (inShell()) parent.postMessage(msg, location.origin); };
  // Listen for shell messages. Anything not from the app's own shell is ignored.
  function onMessage(fn) {
    addEventListener("message", e => { if (e.origin === location.origin && e.source === parent && e.data && e.data.og) fn(e.data); });
  }

  // ----- small shared renderers -----
  const pill = st => `<span class="pill ${esc(st.tone || "muted")}">${esc(st.label)}</span>`;
  const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  function highlight(text, q) {
    const words = String(q || "").trim().split(/\s+/).filter(w => w.length > 1).map(reRegex);
    const safe = esc(text);
    return words.length ? safe.replace(new RegExp("(" + words.join("|") + ")", "gi"), "<mark>$1</mark>") : safe;
  }

  return { $, $$, el, esc, store, debounce, reRegex, applyTheme, toggleTheme, toast, getJSON, getText, exists, go, onRoute, tell, onMessage, pill, slug, highlight, inShell };
})();
