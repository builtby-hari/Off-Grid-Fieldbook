# PDF to Markdown for the library

Converts one PDF into `content/library/<slug>/index.md` with page markers, detected headings, paragraphs and lists, and page images (WebP) for figure and table pages. It also writes `CHECK.md` for a fidelity review.

Nothing here runs anything from `downloads/`. The PDF is only parsed. Python runs as `python3 -I`. No network, no packages.

## Parts

- `pdf_extract.swift` (compiled to `pdf_extract`): PDFKit text lines with font size, bold flag, bounds and a leading bold run; figure flags (large image XObjects, vector path segments, under 400 characters); table flag; PNG render at 110 dpi for flagged pages. Output: `pages.json` and `img/page-NNN.png`.
- `pdf2md.py`: builds `index.md` and `img/*.webp`, using `pdf_extract` into `content/library/<slug>/.work`, then deletes `.work`.
- `check_fidelity.py`: writes `CHECK.md` (sizes, counts, heading outline, NUMBERS CHECK, word recall). Re-extracts the PDF to a temp folder and deletes it.

## Build and run

    swiftc -O -o tools/library/pdf_extract tools/library/pdf_extract.swift
    python3 -I tools/library/pdf2md.py <pdf> <slug> --title "..." --publisher "..." --year 2015 \
        --license "..." --source-url "..." [--old-safety-rules] [--heading-ratio 1.15]
    python3 -I tools/library/check_fidelity.py <slug>

`--old-safety-rules` is only recorded in the front matter (`old_safety_rules: true`). It changes nothing else. The three current conversions do not set it.

## Output

`index.md` has YAML front matter (title, publisher, year, license, source_url, source_file, pages, old_safety_rules, converted), one `# title`, then `<!-- page N -->` before each page. Flagged pages get `![Page N of the original: figure or table](img/page-NNN.webp)` right after the marker. Table-flagged pages also get the note line and their text.

`split_joins.json` lists every split-word repair (see below) so a reviewer can undo any of them. `CHECK.md` is the review record.

## Rules the tool follows, and where it departs from the spec

- Running headers and footers: removed when they repeat (digits ignored) on at least 40 percent of pages. Bare page numbers in the top or bottom edge zone are removed. Short repeated lines (under 60 characters) are removed even when they are not in an edge zone, because some running titles sit in a side margin.
- Headings: a line at least 1.15 times body size, or a bold run alone on its line, under 90 characters, not ending in a period, no more than two lines. Heading levels: the largest sizes are `##`, the next `###`, all others `####`.
- Run-in headings (bold text at the start of a body line) are split off as their own line.
- Hyphen rejoin: a line-end hyphen joins the next line only when that line starts with a lowercase letter. If the joined word also appears with a hyphen elsewhere in the document (for example "boiling-water"), the hyphen is kept.
- Split words (not in the spec): the PDF text layer of some documents breaks words ("f or", "m ust"). A split is joined only when the joined word is common in the same document. Every join is listed in `split_joins.json`.
- Figures: flagged when a large image (both sides at least 120 px) is in the page or in one Form XObject level down, when the page has at least 24 curve segments of vector art (designed sheets draw their graphics this way), or when it has under 400 characters.
- Tables: flagged when 8 or more short lines contain digits, or when three or more left-edge columns of digit lines are shared by three or more lines each. A table-flagged page keeps its normal text, reflowed. Cells are not separated; read the page image.
- WebP: `cwebp -q 55`, with `-resize 900 0` only when the PNG is wider than 900 px.
- Encoding: U+FFFD becomes a space, U+FFFC is dropped, ligatures are expanded, curly quotes become straight, spaces are collapsed. Em dashes in the source text are kept as written.

## Known limits

- Headings: the level rule works only where the source uses clearly different sizes. A source with 13 pt section headings on an 11.5 pt body (1.13 times) gets none at the default ratio. `--heading-ratio 1.10` catches them, with more false positives.
- Heading levels follow the largest sizes only. A manual that uses one bold size for chapters and sections gets one flat level.
- Table text is reflowed, not rebuilt. Values run together. The page image is the reference.
- Split words: Texas run had 514 repairs and about 200 left by a rough count. The leftovers stay, and one stays in a safety-relevant sentence ("dive rt", p13). The number check reads the same text layer, so it cannot catch a number the text layer itself splits ("1 0"). Check the page image for those.
- Scanned pages without a text layer produce no text. None of the three documents is scanned.
- Page images are rendered from the PDF, not from an OCR layer.
