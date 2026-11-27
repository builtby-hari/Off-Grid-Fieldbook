# Off-Grid Fieldbook | Layout and build notes

## Navigation

Keep five destinations. The sidebar is the desktop menu. On a narrow screen use five labeled bottom tabs. Keep Search and Emergency available from every page and put a labeled Settings entry in the mobile menu.

| Destination | Owns | Show first |
| --- | --- | --- |
| Home | Starting a response and deciding what to prepare next | Six direct situation buttons. Under them, one household task with its action. |
| Map | Installed packs, nearby places and visible layers | The selected map, or Choose a state and Open a drive when empty. |
| My Place | Private records, supplies, contacts, shutoffs and maintenance | Searchable records grouped by purpose. On a fresh copy, show Add your first record. |
| Learn | Offline guides, books, diagrams and reference tools | A question someone can answer with an installed guide. Keep Sun and time and Living with the land here. |
| Plan | Household checklists and shareable cards | Start or resume a checklist. Keep Edit plan as a separate action. |

## Three layouts to build first

1. **Home.** Put the scenario buttons in the first screenful. Give the preparation area one next task, such as Add drinking water. Once populated, show the most important due item and the amount of drinking water left. Move the full charts and record list to My Place. Reserve orange for emergency actions.
2. **Emergency.** The global button opens a neutral picker. Choosing Power out opens its instructions directly. Put the source near the steps, then related household gear and nearby help. A missing map must never hide the instructions. On a phone, keep the first step above the fold.
3. **My Place and Supplies.** Keep a sortable desktop sheet. On a phone show the item, days left and an Update amount button on each row. Opening a row reveals units, daily use, last measurement and history. A stock edit updates Home and My Place together. Keep Find and Add separate.

## Presentation cleanup

- Put the preview navigation strip, commentary column and embedded audit on a separate reviewer page. The app-only prototype should open directly to Home.
- Use one main action per empty state. Use grouped rows for related records, not separate cards for every fact.
- A chart should answer a specific question. A barrel fill bar answers how full the container is. A group of checklist dots plus a ring plus a completed count repeats one fact. Show the next unfinished step.
- Capture each main screen at actual desktop and 390 px widths in both themes. Include a clean first run, a populated profile and a disconnected drive. Label example data in the review gallery.
- Put private backup and clean starter export on separate actions. The export preview lists exactly which records, photos and coordinates will be included.

## Implementation structure

| Owner | Responsibility |
| --- | --- |
| app/web/index.html, ui.js and ui.css | Navigation, back behavior, search dialog, focus, themes and shared component styles. |
| Existing screen files under app/web/ | Screen-specific layout and input. Keep the giant review prototype outside production. |
| og.js and the native records service | Read and save one versioned household dataset. Household inventory and plan tasks use stable IDs. |
| Shared calculation and search code | Calculate days left once. Index the current saved task wording after edits. Let the UI display the result. |
| Native file and pack services | Identify mounted volumes, validate local content and create or restore archives. The UI reports actual results. |
| Separate demo fixtures and screenshot tools | Run visual reviews without copying private records or personal locations into a public build. |

## Ship order

1. Home → situation → sourced offline steps → Back. Include the neutral picker and test urgent search phrases.
2. Add drinking water → update amount → see the same number on Home. Test zero, missing rate and restricted-use stock.
3. Choose state or drive → open exact map → remove and reconnect drive. Keep guides available throughout.
4. Create plan → check a step → search edited text → back up → restore on a fresh profile. Verify photos and task IDs.
5. Add printable family cards, calendar views and a Flipper launcher after the everyday paths work. Keep large state packs optional.
