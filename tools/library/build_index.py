#!/usr/bin/env python3
"""Build the Learn library indexes.

Reads content/library/pdf-catalog.json and every converted manual at
content/library/<slug>/index.md. Writes:
  content/library/catalog.json       the catalog, with "md" and "pages" added
  content/library/search-index.json  one entry per section of each converted manual

Usage: python3 -I tools/library/build_index.py [--share]

--share keeps only entries whose "share" is true (public domain or CC) and says what it dropped.

Anchors follow app/web/md.js exactly: slug(), the duplicate "-2", "-3" rule, and the same
line rules for headings, fenced code, comments and page markers. Keep the two in step.
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "content" / "library"
CHUNK = 1500

# Same patterns as md.js
PAGE_RE = re.compile(r"^\s*<!--\s*page\s+(\d+)\s*-->\s*$")
COMMENT_RE = re.compile(r"^\s*<!--")
HEAD_RE = re.compile(r"^(#{1,6})\s+([^\n\r  ]*)")
FM_RE = re.compile(r"^---\n([\s\S]*?)\n---\n?")


def js_slug(s):
    """md.js slug(): lowercase, drop tags, non-alphanumeric runs become '-', trim '-'."""
    s = s.lower()
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def split_front_matter(src):
    """md.js split(): returns (meta, body)."""
    text = src.replace("\r", "")
    m = FM_RE.match(text)
    if not m:
        return {}, src
    meta = {}
    for line in m.group(1).split("\n"):
        i = line.find(":")
        if i > 0:
            key = line[:i].strip()
            val = line[i + 1:].strip()
            val = re.sub(r"^[\"']|[\"']$", "", val)
            meta[key] = val
    return meta, text[m.end():]


def plain_line(line):
    """Turn one Markdown line into plain text for search. Image markup goes entirely."""
    if re.match(r"^\s*\|?[\s:|-]+\|?\s*$", line) and "-" in line:
        return ""  # table separator or horizontal rule
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", line)
    t = re.sub(r"<!--.*?-->", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", t)
    t = re.sub(r"^\s*>\s?", "", t)
    t = re.sub(r"\[[ xX]\]", " ", t)
    t = t.replace("`", "").replace("**", "").replace("__", "").replace("*", "").replace("|", " ")
    return t


def scan_sections(body):
    """Walk the body the way md.js render() does, and return a list of sections.

    Each section: {level, raw, text, page}. A section starts at a heading line and runs
    to the next heading. Text before the first heading goes in a section with raw None.
    """
    lines = body.replace("\r", "").split("\n")
    sections = [{"level": 0, "raw": None, "text": [], "page": 1}]
    page = 1
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        pg = PAGE_RE.match(line)
        if pg:
            page = int(pg.group(1))
            i += 1
            continue
        if COMMENT_RE.match(line):
            i += 1
            continue
        if line.startswith("```"):
            # fenced code: its lines are text, never headings
            i += 1
            while i < n and not lines[i].startswith("```"):
                sections[-1]["text"].append(lines[i])
                i += 1
            i += 1
            continue
        h = HEAD_RE.match(line)
        if h:
            sections.append({"level": len(h.group(1)), "raw": h.group(2), "text": [], "page": page})
            i += 1
            continue
        sections[-1]["text"].append(line)
        i += 1
    return sections


def section_entries(slug, title, body):
    """One or more search entries per heading, with the anchors md.js would give."""
    used = {}
    out = []
    for sec in scan_sections(body):
        if sec["raw"] is None:
            anchor = ""
            heading = title
        else:
            base = js_slug(sec["raw"]) or "section"
            used[base] = used.get(base, 0) + 1
            anchor = base if used[base] == 1 else f"{base}-{used[base]}"
            heading = re.sub(r"[*`]", "", sec["raw"])
        text_lines = [plain_line(x) for x in sec["text"]]
        text = " ".join(t for t in text_lines if t.strip())
        text = re.sub(r"\s+", " ", text).strip()
        if not text and sec["raw"] is None:
            continue
        pieces = []
        while len(text) > CHUNK:
            cut = text.rfind(" ", 0, CHUNK)
            if cut < 500:
                cut = CHUNK
            pieces.append(text[:cut].strip())
            text = text[cut:].strip()
        pieces.append(text)
        for piece in pieces:
            out.append({"s": slug, "t": title, "h": heading, "a": anchor, "p": sec["page"], "x": piece})
    return out


def max_page(body):
    pages = [int(m.group(1)) for m in (PAGE_RE.match(x) for x in body.replace("\r", "").split("\n")) if m]
    return max(pages) if pages else None


# ----- PDF pages: every catalog PDF is read page by page with tools/library/pdf_text (PDFKit) -----
PDF_TEXT = ROOT / "tools" / "library" / "pdf_text"
PDF_PAGES = LIB / "pdf-pages"
PAGE_MIN = 80            # a page needs at least this many characters to be indexed
PAGE_CUT = 1500          # characters of text kept per indexed page
PAGE_CUT_SMALL = 900     # used only if search-index.json would be over SIZE_LIMIT
SIZE_LIMIT = 12 * 1024 * 1024


def pdf_source(path):
    """Map a catalog pdf path to the file on disk. Same mapping as the path check."""
    top, _, rest = path.lstrip("/").partition("/")
    cands = []
    if top == "shelf":
        cands = [ROOT / "downloads" / "extra" / "library" / rest, ROOT / "downloads" / "extra" / "research" / rest]
    elif top == "books":
        category, _, tail = rest.partition("/")
        cands = [ROOT / "Offline Kit - Mac" / "Books (PDF)" / rest,
                 ROOT / "downloads" / "pdf" / category.lower() / tail]
    for c in cands:
        if c.is_file():
            return c
    return None


def build_pdf_pages(catalog):
    """Run pdf_text on every catalog PDF into content/library/pdf-pages/<slug>.json.
    A file is skipped when its output is newer than the PDF."""
    if not PDF_TEXT.is_file():
        raise SystemExit("pdf_text is not built. Run: swiftc -O tools/library/pdf_text.swift -o tools/library/pdf_text")
    PDF_PAGES.mkdir(parents=True, exist_ok=True)
    stats = {"pdfs": 0, "ran": 0, "skipped": 0, "missing": [], "failed": []}
    for e in catalog:
        if not e.get("pdf"):
            continue
        stats["pdfs"] += 1
        src = pdf_source(e["pdf"])
        if src is None:
            stats["missing"].append(e["slug"])
            print("warning: PDF file not found for %s: %s" % (e["slug"], e["pdf"]))
            continue
        out = PDF_PAGES / (e["slug"] + ".json")
        if out.is_file() and out.stat().st_mtime >= src.stat().st_mtime:
            stats["skipped"] += 1
            continue
        r = subprocess.run([str(PDF_TEXT), str(src), str(out)], capture_output=True, text=True)
        if r.returncode != 0:
            stats["failed"].append(e["slug"])
            print("warning: pdf_text failed for %s: %s" % (e["slug"], (r.stderr or "").strip()[:200]))
            continue
        stats["ran"] += 1
    return stats


def page_entries(e, cut):
    """One search entry per page with at least PAGE_MIN characters of text."""
    path = PDF_PAGES / (e["slug"] + ".json")
    if not path.is_file():
        return []
    out = []
    for pg in json.loads(path.read_text(encoding="utf-8")):
        text = re.sub(r"\s+", " ", pg.get("x", "")).strip()
        if len(text) < PAGE_MIN:
            continue
        n = int(pg["p"])
        # Index the whole page. A long page becomes several entries for the same page, cut at a space,
        # so nothing on it is left out of search.
        start = 0
        while start < len(text):
            end = min(len(text), start + cut)
            if end < len(text):
                sp = text.rfind(" ", start, end)
                if sp > start + cut // 2:
                    end = sp
            out.append({"s": e["slug"], "t": e["title"], "h": "Page %d" % n, "a": "", "p": n, "x": text[start:end].strip(), "pg": n})
            start = end
    return out


def main():
    started = time.monotonic()
    args = sys.argv[1:]
    share_only = "--share" in args
    out = LIB   # --out <folder>: write the two files there (the app build uses this, one folder per edition)
    if "--out" in args:
        i = args.index("--out")
        if i + 1 >= len(args):
            print("usage: python3 -I tools/library/build_index.py [--share] [--out folder]")
            return 1
        out = Path(args[i + 1]); out.mkdir(parents=True, exist_ok=True)
        del args[i:i + 2]
    unknown = [a for a in args if a != "--share"]
    if unknown:
        print("usage: python3 -I tools/library/build_index.py [--share] [--out folder]")
        return 1

    pdf_catalog = json.loads((LIB / "pdf-catalog.json").read_text(encoding="utf-8"))
    page_stats = build_pdf_pages(pdf_catalog)
    entries = []
    for e in pdf_catalog:
        e = dict(e)
        index = LIB / e["slug"] / "index.md"
        e["md"] = index.is_file()
        if e["md"]:
            src = index.read_text(encoding="utf-8")
            meta, body = split_front_matter(src)
            pages = meta.get("pages")
            try:
                pages = int(pages) if pages is not None else None
            except ValueError:
                pages = None
            if pages is None:
                pages = max_page(body)
            if pages is not None:
                e["pages"] = pages
        entries.append(e)

    dropped = []
    if share_only:
        kept = []
        for e in entries:
            if e.get("share") is True:
                kept.append(e)
            else:
                dropped.append(e)
        entries = kept
        print("--share: dropped %d entries that are not shareable:" % len(dropped))
        for e in dropped:
            print("  - %s (%s, license %s)" % (e["slug"], e.get("title", ""), e.get("license", "?")))

    # converted folders that the catalog does not list
    known = {e["slug"] for e in pdf_catalog}
    for d in sorted(LIB.iterdir()) if LIB.is_dir() else []:
        if d.is_dir() and (d / "index.md").is_file() and d.name not in known:
            print("warning: converted folder not in pdf-catalog.json, not indexed: %s" % d.name)

    docs = 0
    sections = []
    for e in entries:
        if not e["md"]:
            continue
        docs += 1
        src = (LIB / e["slug"] / "index.md").read_text(encoding="utf-8")
        meta, body = split_front_matter(src)
        title = meta.get("title") or e.get("title") or e["slug"]
        sections.extend(section_entries(e["slug"], title, body))

    # PDF pages: try the normal cut first, then the smaller cut if the file would be too big
    cut = PAGE_CUT
    pages = []
    while True:
        pages = [p for e in entries if e.get("pdf") for p in page_entries(e, cut)]
        search = sections + pages
        text = json.dumps(search, ensure_ascii=False) + "\n"
        if len(text.encode("utf-8")) <= SIZE_LIMIT or cut == PAGE_CUT_SMALL:
            break
        print("search-index.json would be over 12 MB at %d characters per page; cutting to %d" % (cut, PAGE_CUT_SMALL))
        cut = PAGE_CUT_SMALL

    (out / "catalog.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "search-index.json").write_text(text, encoding="utf-8")

    size_mb = len(text.encode("utf-8")) / (1024 * 1024)
    print("catalog entries: %d" % len(entries))
    print("converted manuals in catalog: %d" % docs)
    print("PDFs in catalog: %d (text run: %d, up to date: %d, missing: %d, failed: %d)" % (
        page_stats["pdfs"], page_stats["ran"], page_stats["skipped"], len(page_stats["missing"]), len(page_stats["failed"])))
    print("pages indexed: %d (per-page cut: %d characters)" % (len(pages), cut))
    print("search entries: %d (sections %d, pages %d)" % (len(search), len(sections), len(pages)))
    print("search-index.json: %.2f MB" % size_mb)
    print("written: %s and %s" % (out / "catalog.json", out / "search-index.json"))
    print("time: %.1f s" % (time.monotonic() - started))
    return 0


if __name__ == "__main__":
    sys.exit(main())
