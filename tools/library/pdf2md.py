#!/usr/bin/env python3
"""Convert one PDF to Markdown for the Off-Grid library (stdlib only).

Usage:
  python3 -I tools/library/pdf2md.py <pdf> <slug> --title T --publisher P --year Y \
      --license L --source-url U [--old-safety-rules]

Writes content/library/<slug>/index.md and content/library/<slug>/img/page-NNN.webp.
Runs tools/library/pdf_extract (PDFKit) into content/library/<slug>/.work and removes it.
The PDF is parsed only, never executed.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXTRACT = HERE / "pdf_extract"
CWEBP = "/opt/homebrew/bin/cwebp"

BULLET_RE = re.compile(r"^(?:[•●▪◦‣·⁃■]|[-–*])\s+(?=\S)")
NUMBERED_RE = re.compile(r"^(\d{1,3})[.)]\s+(?=\S)")
BARE_NUMBER_RE = re.compile(r"^(?:page\s*)?\d{1,4}(?:\s*(?:of|/)\s*\d{1,4})?$", re.I)
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}


def clean(s):
    """Encoding fixes shared by the converter and the number check."""
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    s = s.replace(" ", " ").replace("­", "")
    s = s.replace("￼", "")
    s = s.replace("�", " ")
    s = s.replace("‘", "'").replace("’", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def norm_key(text):
    """Key for repeated-line detection: digits ignored, case ignored."""
    t = re.sub(r"\d+", "#", text.lower())
    return re.sub(r"\s+", " ", t).strip()


def run_extract(pdf, work):
    if not EXTRACT.exists():
        sys.exit("missing tool binary: %s (compile tools/library/pdf_extract.swift)" % EXTRACT)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    proc = subprocess.run([str(EXTRACT), str(pdf), str(work)],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        sys.exit("pdf_extract failed: %s" % proc.stderr.decode("utf-8", "replace")[-800:])
    with open(work / "pages.json", encoding="utf-8") as f:
        return json.load(f)


def png_width(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: %s" % path)
    return struct.unpack(">I", head[16:20])[0]


def to_webp(png, webp):
    cmd = [CWEBP, "-q", "55"]
    if png_width(png) > 900:
        cmd += ["-resize", "900", "0"]
    cmd += [str(png), "-o", str(webp)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        sys.exit("cwebp failed on %s: %s" % (png, proc.stderr.decode("utf-8", "replace")))


def build_pages(data):
    """Clean lines per page, split run-in headings, drop running headers/footers and bare page numbers."""
    pages = []
    total = data["page_count"]
    edge_counts = Counter()
    for p in data["pages"]:
        h = p["height"] or 792.0
        lines = []
        for l in p["lines"]:
            t = clean(l["text"])
            if not t:
                continue
            base = {"size": l["size"], "bold": l["bold"], "y0": l["y0"], "x0": l["x0"],
                    "bounds": l["bounds"], "zone": None, "same_line": False}
            lead = clean(l.get("lead_bold", ""))
            if len(lead) >= 3 and t.startswith(lead) and len(t) > len(lead) + 2:
                first = dict(base, text=lead, bold=True)
                rest = dict(base, text=t[len(lead):].strip(), bold=False, same_line=True)
                lines.append(first)
                lines.append(rest)
            else:
                lines.append(dict(base, text=t))
        n = len(lines)
        for idx, l in enumerate(lines):
            if l["bounds"]:
                if l["y0"] > h * 0.90:
                    l["zone"] = "top"
                elif l["y0"] < h * 0.08:
                    l["zone"] = "bottom"
            else:
                if idx < 2:
                    l["zone"] = "top"
                elif idx >= n - 2:
                    l["zone"] = "bottom"
        seen = set()
        for l in lines:
            if l["zone"] or len(l["text"]) < 60:
                k = norm_key(l["text"])
                if k not in seen:
                    seen.add(k)
                    edge_counts[k] += 1
        pages.append({"page": p["page"], "lines": lines, "p": p})
    repeated = {k for k, c in edge_counts.items() if total >= 3 and c >= 0.4 * total}
    for pg in pages:
        kept = []
        for l in pg["lines"]:
            k = norm_key(l["text"])
            if (l["zone"] or len(l["text"]) < 60) and k in repeated:
                continue
            if l["zone"] and BARE_NUMBER_RE.match(l["text"]):
                continue
            kept.append(l)
        pg["lines"] = kept
    return pages, repeated


COMPOUND_RE = re.compile(r"\b([a-z]+)-([a-z]+)\b")


def compound_set(pages):
    """Hyphenated words that appear inside a line in the PDF (e.g. boiling-water).
    A line-end hyphen joined to a known compound keeps its hyphen."""
    found = set()
    for pg in pages:
        for l in pg["lines"]:
            for m in COMPOUND_RE.finditer(l["text"].lower()):
                found.add(m.group(0))
    return found


def join_hyphen(last, text, compounds):
    """Join a line-end hyphen split. Keep the hyphen when the word is a known compound."""
    stem = last[:-1]
    head = re.search(r"([a-z]+)$", stem.lower())
    tail = re.match(r"^([a-z]+)", text.lower())
    if head and tail and (head.group(1) + "-" + tail.group(1)) in compounds:
        return stem + "-" + text
    return stem + text



STOP = set("""a i an and any are as at be by can do for from had has have he her his if in
is it its me my no not of on or our out so the to up us use was we were with you
one all may own via""".split())
ALPHA_RE = re.compile(r"[A-Za-z]+")
RIGHT_RE = re.compile(r"([a-z]+)(.*)")


def fix_split_words(text):
    """Undo PDF text-layer word splits (e.g. 'f or', 'pur ity', 'm ust') when the joined
    word is common elsewhere in this same document. Returns (new_text, list of (before, after))."""
    words = Counter(w.lower() for w in re.findall(r"[A-Za-z]+", text))
    joins = []

    def qualifies(left, right):
        lo, ro = left.lower(), right.lower()
        jc = words.get(lo + ro, 0)
        if len(lo) == 1:
            # a lone letter is almost always a split, except the words a and I
            return lo not in ("a", "i") and jc >= 3 and words.get(ro, 0) < jc
        return (jc >= 3 and words.get(lo, 0) < jc and words.get(ro, 0) < jc
                and lo not in STOP and ro not in STOP)

    out_lines = []
    for line in text.split("\n"):
        if line.startswith(("<!--", "![", "---", "title:", "publisher:", "year:", "license:",
                            "source_url:", "source_file:", "pages:", "old_safety_rules:", "converted:")):
            out_lines.append(line)
            continue
        toks = line.split(" ")
        out = []
        i = 0
        while i < len(toks):
            if i + 1 < len(toks) and ALPHA_RE.fullmatch(toks[i]):
                rm = RIGHT_RE.fullmatch(toks[i + 1])
                if rm and qualifies(toks[i], rm.group(1)):
                    joined = toks[i] + rm.group(1) + rm.group(2)
                    joins.append((toks[i] + " " + toks[i + 1], joined))
                    out.append(joined)
                    i += 2
                    continue
            out.append(toks[i])
            i += 1
        out_lines.append(" ".join(out))
    return "\n".join(out_lines), joins


def body_size(pages):
    weight = Counter()
    for pg in pages:
        for l in pg["lines"]:
            weight[round(l["size"], 1)] += len(l["text"])
    if not weight:
        return 10.0
    return weight.most_common(1)[0][0]


def style(l):
    return (round(l["size"], 1), l["bold"])


def is_bullet(text):
    return bool(BULLET_RE.match(text) or NUMBERED_RE.match(text))


HEADING_RATIO = 1.15
COMPOUNDS = set()
HYPHEN_JOINS = []


def classify_blocks(pages, body):
    """Return per page a list of items: ('heading', level_key, text) or ('line', line)."""
    result = []
    for pg in pages:
        lines = pg["lines"]
        items = []
        i = 0
        while i < len(lines):
            j = i
            while j + 1 < len(lines) and style(lines[j + 1]) == style(lines[i]) \
                    and not is_bullet(lines[j + 1]["text"]):
                j += 1
            run = lines[i:j + 1]
            s, b = style(lines[i])
            text = " ".join(l["text"] for l in run)
            prev_style = style(lines[i - 1]) if i > 0 else None
            next_style = style(lines[j + 1]) if j + 1 < len(lines) else None
            big = s >= body * HEADING_RATIO
            alone = (prev_style != style(lines[i])) and (next_style != style(lines[i]))
            is_head = (len(run) <= 2 and len(text) < 90 and not text.endswith(".")
                       and not is_bullet(text) and (big or (b and alone)))
            if is_head:
                key = ("size", s) if big else ("bold", 0)
                items.append(("heading", key, text))
            else:
                for l in run:
                    items.append(("line", l))
            i = j + 1
        result.append((pg["page"], items))
    return result


def heading_levels(classified):
    keys = set()
    for _, items in classified:
        for it in items:
            if it[0] == "heading":
                keys.add(it[1])
    ordered = sorted(keys, key=lambda k: (0, -k[1]) if k[0] == "size" else (1, 0))
    level = {}
    for idx, k in enumerate(ordered):
        level[k] = "##" if idx == 0 else ("###" if idx == 1 else "####")
    return level


def page_markdown(page_no, items, levels, figure, table, page_img_name):
    out = ["<!-- page %d -->" % page_no, ""]
    if figure or table:
        out += ["![Page %d of the original: figure or table](img/%s)" % (page_no, page_img_name), ""]
    if table:
        out += ["*Table text below was read automatically. Check it against the page image above.*", ""]
    para = []
    list_item = None  # index into para for an open list item
    blocks = []

    def flush():
        nonlocal para, list_item
        if para:
            if list_item is not None:
                blocks.append(("list", para[0]))
            else:
                blocks.append(("para", " ".join(para)))
        para = []
        list_item = None

    prev = None
    pending_bullet = False
    for it in items:
        if it[0] == "heading":
            flush()
            blocks.append(("para", "%s %s" % (levels[it[1]], it[2])))
            prev = None
            continue
        l = it[1]
        text = l["text"]
        if pending_bullet:
            text = "- " + text if not NUMBERED_RE.match(text) else text
            pending_bullet = False
        if text in ("•", "●", "▪", "-", "–", "*"):
            pending_bullet = True
            continue
        gap_break = False
        if prev is not None:
            spacing = prev["y0"] - l["y0"]
            size = max(prev["size"], l["size"], 1.0)
            if l["bounds"] and prev["bounds"] and not l.get("same_line"):
                if spacing <= 0 or spacing > 1.6 * size:
                    gap_break = True
                if abs(l["x0"] - prev["x0"]) > 40 and spacing <= 0:
                    gap_break = True
        if gap_break:
            flush()
        bm = BULLET_RE.match(text)
        nm = NUMBERED_RE.match(text)
        if bm or nm:
            flush()
            if bm:
                body_text = text[bm.end():]
                para = ["- " + body_text]
            else:
                body_text = text[nm.end():]
                para = ["%s. %s" % (nm.group(1), body_text)]
            list_item = len(para) - 1
            prev = l
            continue
        if para:
            last = para[-1]
            # hyphen rejoin: word split across a line end
            if last.endswith("-") and len(last) > 2 and last[-2].isalpha() and text[:1].islower():
                para[-1] = join_hyphen(last, text, COMPOUNDS)
                HYPHEN_JOINS.append(1)
            else:
                para[-1] = last + " " + text
        else:
            para = [text]
        prev = l
    flush()
    prev_kind = None
    for kind, b in blocks:
        if kind == "list" and prev_kind == "list":
            out.append(b)
        else:
            if out and out[-1] != "":
                out.append("")
            out.append(b)
        prev_kind = kind
    if out and out[-1] != "":
        out.append("")
    return out


def convert(args):
    pdf = Path(args.pdf).resolve()
    if not pdf.exists():
        sys.exit("no such PDF: %s" % pdf)
    out_dir = ROOT / "content" / "library" / args.slug
    work = out_dir / ".work"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = run_extract(pdf, work)
    pages, repeated = build_pages(data)
    global COMPOUNDS
    COMPOUNDS = compound_set(pages)
    body = body_size(pages)
    classified = classify_blocks(pages, body)
    levels = heading_levels(classified)

    img_out = out_dir / "img"
    if img_out.exists():
        shutil.rmtree(img_out)
    img_out.mkdir()

    raw_pages = {p["page"]: p for p in data["pages"]}
    md = []
    fm = [
        "---",
        "title: %s" % json.dumps(args.title, ensure_ascii=False),
        "publisher: %s" % json.dumps(args.publisher, ensure_ascii=False),
        "year: %s" % json.dumps(str(args.year)),
        "license: %s" % json.dumps(args.license, ensure_ascii=False),
        "source_url: %s" % json.dumps(args.source_url),
        "source_file: %s" % json.dumps(os.path.relpath(pdf, ROOT)),
        "pages: %d" % data["page_count"],
        "old_safety_rules: %s" % ("true" if args.old_safety_rules else "false"),
        "converted: %s" % json.dumps(datetime.date.today().isoformat()),
        "---",
        "",
    ]
    md += fm
    md += ["# %s" % args.title, ""]
    figures = tables = 0
    for page_no, items in classified:
        rp = raw_pages[page_no]
        fig = bool(rp["has_figure"])
        tbl = bool(rp["looks_like_table"])
        img_name = "page-%03d.webp" % page_no
        if fig or tbl:
            if not rp.get("rendered"):
                sys.exit("page %d flagged but not rendered" % page_no)
            to_webp(work / rp["rendered"], img_out / img_name)
        figures += fig
        tables += tbl
        md += page_markdown(page_no, items, levels, fig, tbl, img_name)

    text = "\n".join(md)
    text = re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"
    text, split_joins = fix_split_words(text)
    (out_dir / "split_joins.json").write_text(json.dumps(split_joins, ensure_ascii=False, indent=0), encoding="utf-8")
    (out_dir / "index.md").write_text(text, encoding="utf-8")
    shutil.rmtree(work)

    headings = Counter(line.split(" ")[0] for line in text.splitlines()
                       if re.match(r"^#{2,4} ", line))
    print("wrote %s" % (out_dir / "index.md"))
    print("pages %d, body size %.1f, repeated running lines removed: %d" %
          (data["page_count"], body, len(repeated)))
    print("figure pages %d, table pages %d, headings %s" % (figures, tables, dict(headings)))
    print("hyphen rejoins %d (compounds kept: %d)" % (len(HYPHEN_JOINS), len(COMPOUNDS)))
    print("split-word joins %d" % len(split_joins))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("slug")
    ap.add_argument("--title", required=True)
    ap.add_argument("--publisher", required=True)
    ap.add_argument("--year", required=True)
    ap.add_argument("--license", required=True)
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--old-safety-rules", action="store_true")
    ap.add_argument("--heading-ratio", type=float, default=1.15,
                    help="a line this many times the body size can be a heading (default 1.15)")
    args = ap.parse_args()
    global HEADING_RATIO
    HEADING_RATIO = args.heading_ratio
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", args.slug):
        sys.exit("slug must be lowercase letters, digits and hyphens")
    convert(args)


if __name__ == "__main__":
    main()
