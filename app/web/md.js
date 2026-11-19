// Small Markdown renderer shared by the shell (plan pages, help) and Learn (converted manuals).
// Handles: front matter, headings with anchors, lists, task boxes, tables, code, quotes, images,
// links, bold, italics, and the <!-- page N --> markers the manual converter writes.
"use strict";
const MD = (() => {
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const slug = s => String(s).toLowerCase().replace(/<[^>]+>/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  // "---\nkey: value\n---" at the top of a file -> { meta, body }
  function split(src) {
    const m = /^---\n([\s\S]*?)\n---\n?/.exec(src.replace(/\r/g, ""));
    if (!m) return { meta: {}, body: src };
    const meta = {};
    m[1].split("\n").forEach(l => { const i = l.indexOf(":"); if (i > 0) meta[l.slice(0, i).trim()] = l.slice(i + 1).trim().replace(/^["']|["']$/g, ""); });
    return { meta, body: src.replace(/\r/g, "").slice(m[0].length) };
  }

  // opts.base: folder that relative image paths are resolved against, for example "/learn/texas-rainwater-manual/"
  function render(src, opts = {}) {
    const base = opts.base || "", used = {}, toc = [];
    const url = u => /^(https?:|\/|#)/.test(u) ? u : base + u;
    const inline = s => esc(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (_, a, u) => `<img loading="lazy" alt="${a}" src="${url(u)}">`)
      .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, t, u) => /^(https?:|\/|#)/.test(u) ? `<a href="${u}">${t}</a>` : t)
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
      .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<i>$2</i>");
    const lines = src.replace(/\r/g, "").split("\n"), out = []; let i = 0;
    const isList = l => /^\s*([-*+]|\d+\.)\s+/.test(l);
    while (i < lines.length) {
      const l = lines[i];
      const pg = /^\s*<!--\s*page\s+(\d+)\s*-->\s*$/.exec(l);
      if (pg) { out.push(`<span class="pageref" data-page="${pg[1]}">page ${pg[1]}</span>`); i++; continue; }
      if (/^\s*<!--/.test(l)) { i++; continue; }
      if (/^```/.test(l)) { const buf = []; i++; while (i < lines.length && !/^```/.test(lines[i])) buf.push(esc(lines[i++])); i++; out.push("<pre>" + buf.join("\n") + "</pre>"); continue; }
      const h = /^(#{1,6})\s+(.*)/.exec(l);
      if (h) {
        let id = slug(h[2]) || "section"; used[id] = (used[id] || 0) + 1; if (used[id] > 1) id += "-" + used[id];
        toc.push({ level: h[1].length, text: h[2].replace(/[*`]/g, ""), id });
        out.push(`<h${h[1].length} id="${id}">${inline(h[2])}</h${h[1].length}>`); i++; continue;
      }
      if (/^\s*(---+|\*\*\*+)\s*$/.test(l)) { out.push("<hr>"); i++; continue; }
      if (/^\s*\|/.test(l) && i + 1 < lines.length && /^\s*\|?\s*:?-+/.test(lines[i + 1])) {
        const row = r => r.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
        const head = row(l); i += 2; const body = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) body.push(row(lines[i++]));
        out.push('<div class="scroll-x"><table><tr>' + head.map(c => "<th>" + inline(c) + "</th>").join("") + "</tr>" +
          body.map(r => "<tr>" + r.map(c => "<td>" + inline(c) + "</td>").join("") + "</tr>").join("") + "</table></div>");
        continue;
      }
      if (isList(l)) {
        const ordered = /^\s*\d+\./.test(l), items = [];
        while (i < lines.length && isList(lines[i])) {
          const t = lines[i++].replace(/^\s*([-*+]|\d+\.)\s+/, "");
          const task = /^\[( |x|X)\]\s*(.*)/.exec(t);
          items.push(task ? `<li class="task"><label><input type="checkbox"${task[1] !== " " ? " checked" : ""}>${inline(task[2])}</label></li>` : "<li>" + inline(t) + "</li>");
        }
        out.push((ordered ? "<ol>" : "<ul>") + items.join("") + (ordered ? "</ol>" : "</ul>")); continue;
      }
      if (/^>\s?/.test(l)) { const buf = []; while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(inline(lines[i++].replace(/^>\s?/, ""))); out.push("<blockquote>" + buf.join("<br>") + "</blockquote>"); continue; }
      if (!l.trim()) { i++; continue; }
      const buf = [];
      while (i < lines.length && lines[i].trim() && !/^(#{1,6}\s|\s*[-*+]\s|\s*\d+\.\s|\s*\||```|>|\s*<!--)/.test(lines[i])) buf.push(inline(lines[i++]));
      if (buf.length) out.push("<p>" + buf.join(" ") + "</p>"); else i++;
    }
    return { html: out.join("\n"), toc };
  }
  return { render, split, slug, esc };
})();
