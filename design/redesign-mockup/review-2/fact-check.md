# Second-opinion review: fact check

An outside review of the mock-up came back on 27 November 2026 (`Fieldbook-redesign-review.pdf`, `Layout-and-build-notes.md`). We reproduced 25 of its claims against the same mock-up file in headless Chrome.

Result: 23 true, 2 partly true, 0 false. None of this is fixed in the mock-up yet.

Line numbers refer to `../fieldbook-redesign.src.html`.

| # | Claim | Verdict | What we saw |
|---|---|---|---|
| 1 | "can't breathe" ranks Flash flood first | True | The tokenizer splits on the apostrophe (line 641). "cant breathe" finds the choking page. "don't" and "won't" break the same way. |
| 2 | "do not drink water" equals "drink water" | True | "do" and "not" are stop words (line 629). |
| 3 | "co alarm" opens a power-outage prep passage | True | Ties with a Winter Storm page. No CO alarm situation exists. |
| 4 | "generator indoors" opens Hard freeze | True | Scoring at lines 659 to 680. |
| 5 | "backup" opens Power station | True | The backup feature is not indexed. |
| 6 | "can I drink rainwater" opens Rain tote | True | The record says garden and washing, not for drinking. |
| 7 | "gas smell" opens a personal shutoff step | True | No gas leak situation exists. |
| 8 | E and the orange button show Power out before a choice | True | Lines 1045, 1049, 1166. |
| 9 | Water at 0 shows "unknown" on Home; categories add days across unlike items | True | Line 791 and line 594. The sheet cell correctly says "0 days". |
| 10 | Coordinates stay shown on the map under a different label | True | One shared flag (lines 844, 1119). Show on map carries no record id (line 871). |
| 11 | Sidebar says "Offline ready" while a layer is missing | True | Sidebar only checks whether a map exists. |
| 12 | Backup turns green without saving | Partly | Nothing is written, but it is labelled "(example)" twice. |
| 13 | Page fetches Google Fonts | True | Line 3. Works on fallback fonts when blocked. |
| 14 | Renamed plan step is not searchable | True | Index uses the original labels (line 680). |
| 15 | Palette: Tab changes the filter, Escape drops focus, no screen-reader state | True | Lines 1153, 1157, 751. |
| 16 | Map tool buttons lose their names when text is hidden | True | Under 900px wide (line 318). |
| 17 | Check the size enables Download with no sizes shown | True | Lines 858, 1124. |
| 18 | At 390px the supplies table is 640 wide and the plan table 540 | True | The page itself does not scroll sideways. |
| 19 | Sun and time uses the device date, upkeep dates are offsets from today | True | Lines 925, 935, 940. |
| 20 | Water drawing sends toilet water to outdoor beds with no treatment | True | Line 991. Safety problem, see below. |
| 21 | Two prior searches are seeded on a fresh open | True | Line 714. |
| 22 | The six phone screenshots are 1500 x 1010 boards | True | They capture the review page in phone mode. |
| 23 | Manual reader shows one paragraph; Prev, Next and Print are stubs | True | Line 880. |
| 24 | Family card grid omits timezone, fallback and no-contact steps | Partly | The contact record has an if-no-answer line. Timezone is nowhere. |
| 25 | Library chart sizes topics by section count | True | Three large books drive it (line 891). |

## Fix first

Claim 20. The water reuse drawing and the Idea 4 text say that water used to flush a toilet then waters outdoor beds. That is wrong and unsafe. In the real design, flushed water goes to a septic tank and a lined, contained treatment cell with non-food plants. The drawing needs that stage, a last box that says it is not for food, and a line that greywater and blackwater reuse is regulated.

## Also found by us, not in the review

- Earthquake has only one step.
- Some manual quotes are cut mid-word at 320 characters.
- "settings", "print" and "rice" return nothing.
- Enter on "water" in the supplies bar adds a Bottled water row.
- Phone calendar cells wrap the time onto two lines.
