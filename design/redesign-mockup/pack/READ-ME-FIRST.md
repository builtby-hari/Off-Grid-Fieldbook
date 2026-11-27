# Fieldbook redesign: second-opinion pack

This is a redesign mock-up of Off-Grid Fieldbook, an offline emergency-prep app for Mac (iPhone and a USB go-bag edition come later). Nothing here is built yet. All household data shown is made up. The manual text and the situation steps are real.

## What is in this zip
- `Fieldbook-redesign.html`: the clickable mock-up. Open it in a browser. Keys: Cmd+K or / for search, 1 to 5 for tabs, E for an emergency. The audit of today's app (19 ranked problems) is at the bottom of the same page.
- `screens/`: 34 PNGs. 20 views on Mac in light, 8 in dark, 6 at phone width. File names are numbered in the order a person would meet them.

## What changed from today's app
- Sidebar: one color and icon per tab, number keys, the open tab lists what is inside, an orange emergency button on every screen.
- Search: one pop-up from anywhere. Typo fixing, short names (co, fridge, blackout), whole-word matching, emergency sources ranked above old books, plan steps searched.
- Home: emergency choices and supplies runway on top. One search box.
- Supplies sheet (new): a spreadsheet for what is on hand, with a bar that both searches and adds, and charts that update while typing.
- Plan: every checklist is a fill-in table (step, when, who, what you need) with a progress ring and timeline.
- Learn: six "How do I" questions, a library chart that doubles as the menu, the open shelf beside it.
- Map: tools open on demand, a clear next step when no map is installed.
- Coordinates (new): hidden by default, one click shows latitude and longitude, degrees-minutes-seconds, UTM and USNG, on a record and on the map.
- Sun and time (new): today's sun path, live clocks with UTC, a year-of-daylight chart, moon phase, and a printable month calendar with sunrise, sunset and upkeep due dates. All calculated offline.
- Living with the land (new, under Learn): the six ideas behind earth-sheltered, sun-heated homes, with a cross-section drawing that uses the real summer and winter sun angles for the chosen place.

## Already known gaps (from an internal audit, no need to repeat these)
- Supplies sheet and My Place records are two copies of the same data. The sheet should be a view of the records.
- No add or edit flow for records. No empty or first-run states.
- Settings and backup is one dead button, and is unreachable on the phone layout.
- Dropped from today's app: calculators, drills, rescue card, guides page, plants, radio bulletins. No incident log.
- Search does not index sheet rows or app features, and the typo fixer overreaches.
- The supplies rings add days across unlike items.

## What I want from you
Please audit the redesign, not today's app. The owner likes the direction but feels things are missing.
1. What screens, flows or features are missing? Rank them.
2. For each screen: what is confusing, cramped or weak? Check the phone shots too.
3. The owner is a very visual person. Where would a chart, diagram or picture help, and what data would it show?
4. Where would the smart search still fail a stressed person?
5. Empty states: what should each screen show on a friend's fresh copy with no data?
6. Anything that looks generic or templated. Say exactly which element and what to do instead.

Give a ranked list with a size for each item (S, M or L) and finish with the top 10 things to add before building. Mock-ups for your top 3 changes are welcome.
