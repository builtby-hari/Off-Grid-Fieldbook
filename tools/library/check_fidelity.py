#!/usr/bin/env python3
"""Fidelity check for a converted library document (stdlib only).

Usage: python3 -I tools/library/check_fidelity.py <slug>

Re-extracts the PDF named in index.md front matter, then writes
content/library/<slug>/CHECK.md with:
  sizes, counts, heading outline (first 40), a NUMBERS CHECK (number + unit
  tokens from the PDF text layer, per page, looked for in index.md's same page
  section), and a word-recall figure. The safety-steps section is written by hand.
"""

import collections
import json
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import pdf2md  # noqa: E402  (same clean() and extractor as the converter)

UNITS = (r"minutes?|min|hours?|psig?|lbs?|pounds?|gallons?|gal|inches|inch|feet|foot|ft|"
         r"degrees?|°\s?F|percent|%|ppm|drops?|cups?|quarts?|pints?|tsp|tablespoons?|tbsp")
NUM_UNIT_RE = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s?(" + UNITS + r")(?![A-Za-z])", re.I)
HEAD_RE = re.compile(r"^(#{1,6}) (.*)$")
MARK_RE = re.compile(r"^<!-- page (\d+) -->$", re.M)


def front_matter(text):
    fm = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm


def sections(text):
    """Map page number -> markdown text of that page section."""
    marks = list(MARK_RE.finditer(text))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[int(m.group(1))] = text[m.end():end]
    return out


def extract(pdf, tmp):
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    import subprocess
    proc = subprocess.run([str(HERE / "pdf_extract"), str(pdf), str(tmp)],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        sys.exit("extract failed")
    with open(tmp / "pages.json", encoding="utf-8") as f:
        return json.load(f)


def pdf_page_text(data):
    """Page -> cleaned text, using the same running-line removal as the converter."""
    pages, _ = pdf2md.build_pages(data)
    out = {}
    for pg in pages:
        out[pg["page"]] = " ".join(l["text"] for l in pg["lines"])
    return out


def norm_ws(s):
    return re.sub(r"\s+", " ", s)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: check_fidelity.py <slug>")
    slug = sys.argv[1]
    out_dir = ROOT / "content" / "library" / slug
    index = out_dir / "index.md"
    text = index.read_text(encoding="utf-8")
    fm = front_matter(text)
    pdf = ROOT / fm["source_file"]
    tmp = out_dir / ".check-work"
    data = extract(pdf, tmp)
    shutil.rmtree(tmp)

    pdf_bytes = os.path.getsize(pdf)
    idx_bytes = os.path.getsize(index)
    img_dir = out_dir / "img"
    img_files = sorted(img_dir.glob("*.webp")) if img_dir.exists() else []
    img_bytes = sum(os.path.getsize(p) for p in img_files)

    heads = [(len(m.group(1)), m.group(2)) for m in (HEAD_RE.match(l) for l in text.splitlines()) if m]
    by_level = collections.Counter("#" * lvl for lvl, _ in heads)
    img_refs = re.findall(r"!\[Page \d+ of the original: figure or table\]\(img/([^)]+)\)", text)
    table_notes = text.count("*Table text below was read automatically.")
    secs = sections(text)
    pdf_text = pdf_page_text(data)

    # NUMBERS CHECK
    checked = 0
    missing = []
    per_page_counts = collections.Counter()
    for page_no in sorted(pdf_text):
        ptxt = pdf_text[page_no]
        found = NUM_UNIT_RE.findall(ptxt)
        if not found:
            continue
        sec = norm_ws(secs.get(page_no, ""))
        for num, unit in found:
            checked += 1
            per_page_counts[page_no] += 1
        tokens = collections.Counter(f"{n} {u}" for n, u in found)
        for tok, want in tokens.items():
            n, u = tok.split(" ", 1)
            pat = re.compile(r"(?<![\d.,])" + re.escape(n) + r"\s?" + re.escape(u) + r"(?![A-Za-z])", re.I)
            have = len(pat.findall(sec))
            if have < want:
                missing.append((page_no, tok, want, have))

    # word recall (whole document, multiset of words of 4+ letters)
    # same split-word repair as the converter, so the comparison is fair
    fixed_pdf, _ = pdf2md.fix_split_words(" ".join(pdf_text[k] for k in sorted(pdf_text)))
    pdf_words = collections.Counter(w.lower() for w in re.findall(r"[A-Za-z]{4,}", fixed_pdf))
    idx_words = collections.Counter(w.lower() for w in re.findall(r"[A-Za-z]{4,}", text))
    total_pdf = sum(pdf_words.values())
    kept = sum(min(c, idx_words[w]) for w, c in pdf_words.items())
    recall = 100.0 * kept / total_pdf if total_pdf else 100.0

    # hyphen rejoins: count line ends in the PDF text where a word breaks with "-" and continues lowercase
    raw_joined = 0
    for pg in data["pages"]:
        lines = [pdf2md.clean(l["text"]) for l in pg["lines"]]
        for a, b in zip(lines, lines[1:]):
            if a.endswith("-") and len(a) > 2 and a[-2].isalpha() and b[:1].islower():
                raw_joined += 1

    em_dash_src = sum(pg_text.count("\u2014") for pg_text in pdf_text.values())
    split_path = out_dir / "split_joins.json"
    split_joins = len(json.loads(split_path.read_text(encoding="utf-8"))) if split_path.exists() else 0
    digit_re = r"(?<![\d.,])\d \d(?![\d.,])"
    digit_split_pdf = sum(len(re.findall(digit_re, t)) for t in pdf_text.values())
    digit_split_idx = len(re.findall(digit_re, re.sub(r"<!--.*?-->", "", text)))

    lines_out = []
    add = lines_out.append
    add("# CHECK: %s" % slug)
    add("")
    add("Made by running `tools/library/check_fidelity.py` on the PDF at `%s`." % fm["source_file"])
    add("")
    add("## Sizes")
    add("")
    add("| Item | Bytes |")
    add("|---|---:|")
    add("| PDF (source) | %s |" % f"{pdf_bytes:,}")
    add("| index.md | %s |" % f"{idx_bytes:,}")
    add("| img/*.webp (total, %d files) | %s |" % (len(img_files), f"{img_bytes:,}"))
    add("| index.md + img | %s |" % f"{idx_bytes + img_bytes:,}")
    add("")
    add("Ratio (index.md + img) / PDF: %.2f" % ((idx_bytes + img_bytes) / pdf_bytes))
    add("")
    add("## Counts")
    add("")
    add("- Pages in PDF: %d" % data["page_count"])
    add("- Headings: %s (# title, ## x%d, ### x%d, #### x%d)" % (
        dict(by_level), by_level.get("##", 0), by_level.get("###", 0), by_level.get("####", 0)))
    add("- Images (figure or table pages with a WebP): %d" % len(img_refs))
    add("- Pages flagged as table (note line present): %d" % table_notes)
    add("- Pages flagged has_figure: %d" % sum(1 for p in data["pages"] if p["has_figure"]))
    add("- Hyphen rejoins done by the converter (PDF line ends with a hyphen, next line lowercase): %d" % raw_joined)
    add("- Em dashes in the PDF text layer (kept as in the source): %d" % em_dash_src)
    add("- Split-word repairs made by the converter (PDF text layer broke a word, e.g. 'f or'): %d" % split_joins)
    add("- Digit splits such as '1 0' in the PDF text layer: %d; in index.md: %d" % (digit_split_pdf, digit_split_idx))
    add("- Word recall (4+ letter words, whole document, PDF words found in index.md): %.1f%%" % recall)
    add("")
    add("## Heading outline (first 40)")
    add("")
    for lvl, t in heads[:40]:
        add("%s %s" % ("#" * lvl, t))
    add("")
    add("## NUMBERS CHECK")
    add("")
    add("Method: every number followed by one of these units in the PDF text layer, per page: %s. "
        "Each (number, unit) token is searched for in the same page section of index.md, "
        "the same number of times it occurs on the PDF page." % UNITS.replace("|", ", "))
    add("")
    add("- Number-with-unit tokens checked: %d" % checked)
    add("- Tokens missing or with fewer occurrences in index.md: %d" % len(missing))
    add("")
    if missing:
        add("| Page | Token | PDF count | index.md count |")
        add("|---:|---|---:|---:|")
        for pg, tok, want, have in missing:
            add("| %d | %s | %d | %d |" % (pg, tok, want, have))
        add("")
    add("SAFETY_STEPS_PLACEHOLDER")
    add("")
    (out_dir / "CHECK.md").write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    print("CHECK.md written: numbers checked %d, missing %d, word recall %.1f%%, pages %d" % (
        checked, len(missing), recall, data["page_count"]))


if __name__ == "__main__":
    main()
